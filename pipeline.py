import os
import re
import requests
import pandas as pd
import numpy as np 

from config import (
    REDCAP_API_URL,
    REDCAP_TOKEN,
    RAW_CSV_PATH,
    LESIONS_LONG_PATH,
    VALIDATION_REPORT_PATH,
    META_COLS,
    COLUMNS_TO_DELETE,
    MAX_LESIONS,
)
from lesion_dictionary import describe_field


def download_redcap_export():
    os.makedirs(os.path.dirname(RAW_CSV_PATH), exist_ok=True)

    payload = {
        "token": REDCAP_TOKEN,
        "content": "record",
        "format": "csv",
        "type": "flat",
        "exportDataAccessGroups": "true",
        "rawOrLabel": "raw",
        "rawOrLabelHeaders": "raw",
        "exportCheckboxLabel": "false",
    }

    resp = requests.post(REDCAP_API_URL, data=payload)
    resp.raise_for_status()

    with open(RAW_CSV_PATH, "wb") as f:
        f.write(resp.content)

    print(f"[download] Saved REDCap export to {RAW_CSV_PATH}")


def reshape_to_lesions():

    from config import META_COLS

    print("\n[reshape] Starting reshape_to_lesions()")

    df = pd.read_csv(RAW_CSV_PATH)
    print(f"[debug] Raw rows: {len(df)}")

    # ---------------------------------------------------------
    # 1. Propagate anonymized_number and date_of_birth per MRN
    # ---------------------------------------------------------
    if "mrn" in df.columns and "anonimized_number" in df.columns:
        df["anonimized_number"] = (
            df.groupby("mrn")["anonimized_number"]
              .transform(lambda x: x.ffill().bfill())
        )

    if "mrn" in df.columns and "date_of_birth" in df.columns:
        df["date_of_birth"] = (
            df.groupby("mrn")["date_of_birth"]
              .transform(lambda x: x.ffill().bfill())
        )

    # ---------------------------------------------------------
    # 2. Split MRI and pathology visits
    # ---------------------------------------------------------
    mri_df = df[df["mri_scan_date"].notna()].copy()
    path_df = df[df["biopsy_date"].notna()].copy()

    print(f"[debug] MRI visits: {len(mri_df)}")
    print(f"[debug] Pathology visits: {len(path_df)}")

    # ---------------------------------------------------------
    # 3. Reshape MRI visits into long format
    # ---------------------------------------------------------
    mri_rows = []

    for _, row in mri_df.iterrows():
        n_lesions = row.get("number_of_lesions", 0)
        if pd.isna(n_lesions):
            n_lesions = 0

        if n_lesions > 0:
            for lesion_num in range(1, MAX_LESIONS + 1):
                prefix = f"lesion{lesion_num}_"
                lesion_cols = [c for c in mri_df.columns if c.startswith(prefix)]

                if not lesion_cols:
                    continue

                lesion_data = {c: row[c] for c in lesion_cols}
                if all(pd.isna(v) for v in lesion_data.values()):
                    continue

                lesion_clean = {
                    re.sub(f"^{prefix}", "", k): v
                    for k, v in lesion_data.items()
                }

                meta = {m: row.get(m) for m in META_COLS if m in row.index}

                mri_rows.append({
                    **meta,
                    "lesion_number": lesion_num,
                    "lesion_status": "positive",
                    **lesion_clean
                })

        else:
            meta = {m: row.get(m) for m in META_COLS if m in row.index}
            mri_rows.append({
                **meta,
                "lesion_number": 0,
                "lesion_status": "negative",
            })

    mri_long = pd.DataFrame(mri_rows)
    print(f"[debug] MRI long rows: {len(mri_long)}")
    print("[debug] MRI long columns:", mri_long.columns.tolist())

    # ---------------------------------------------------------
    # 4. Reshape pathology visits into long format
    # ---------------------------------------------------------
    path_rows = []

    for _, row in path_df.iterrows():
        for lesion_num in range(1, MAX_LESIONS + 1):
            prefix = f"lesion{lesion_num}_"
            lesion_cols = [c for c in path_df.columns if c.startswith(prefix)]

            if not lesion_cols:
                continue

            lesion_data = {c: row[c] for c in lesion_cols}
            if all(pd.isna(v) for v in lesion_data.values()):
                continue

            lesion_clean = {
                re.sub(f"^{prefix}", "", k): v
                for k, v in lesion_data.items()
            }

            meta = {m: row.get(m) for m in META_COLS if m in row.index}

            path_rows.append({
                **meta,
                "lesion_number": lesion_num,
                **lesion_clean
            })

    path_long = pd.DataFrame(path_rows)
    print(f"[debug] Pathology long rows: {len(path_long)}")
    print("[debug] Pathology long columns:", path_long.columns.tolist())

    # ---------------------------------------------------------
    # 5. Merge MRI + pathology lesion tables
    # ---------------------------------------------------------
    merged = mri_long.merge(
        path_long,
        on=["anonimized_number", "lesion_number"],
        how="outer",
        suffixes=("_mri", "_path")
    )
    print(f"[debug] After merge: {len(merged)} rows")
    print("[debug] Merged columns:", merged.columns.tolist())

    # ---------------------------------------------------------
    # 6. Remove fake positive lesions
    # ---------------------------------------------------------
    mri_finding_cols = [
        c for c in merged.columns
        if "image_finding" in c and c.endswith("_mri")
    ]
    print(f"[debug] MRI finding columns: {mri_finding_cols}")

    before = len(merged)
    if mri_finding_cols:
        merged = merged[
            ~(
                (merged["lesion_status"] == "positive") &
                merged[mri_finding_cols].isna().all(axis=1)
            )
        ]
    print(f"[debug] Removed {before - len(merged)} fake lesions")

    # ---------------------------------------------------------
    # DEBUG: Inspect raw date values BEFORE parsing
    # ---------------------------------------------------------
    print("\n[debug] RAW MRI date samples BEFORE parsing:")
    print(merged["mri_scan_date_mri"].dropna().head(20).tolist())

    print("\n[debug] RAW PATH date samples BEFORE parsing:")
    print(merged["biopsy_date_path"].dropna().head(20).tolist())

    # ---------------------------------------------------------
    # 7. Parse dates correctly (YYYY-MM-DD)
    # ---------------------------------------------------------
    for col in ["mri_scan_date_mri", "biopsy_date_path"]:
        if col in merged.columns:
            merged[col] = pd.to_datetime(
                merged[col],
                format="%Y-%m-%d",
                errors="coerce"
            )

    print("[debug] Date parsing complete")
    print(merged[["mri_scan_date_mri", "biopsy_date_path"]].head())

    # ---------------------------------------------------------
    # 8. Date filtering
    # ---------------------------------------------------------
    cutoff = pd.Timestamp("2023-06-23")

    before = len(merged)
    merged = merged[
        (
            merged["mri_scan_date_mri"].notna() &
            (merged["mri_scan_date_mri"] > cutoff)
        )
        |
        (
            merged["biopsy_date_path"].notna() &
            (merged["biopsy_date_path"] > cutoff)
        )
    ]
    print(f"[debug] Removed {before - len(merged)} rows by date filter")
    print(f"[debug] After date filter: {len(merged)} rows")

    # ---------------------------------------------------------
    # 9. Replace numeric values with labels for better reading
    # ---------------------------------------------------------
    # 9.1 mr_indication
    mr_map = {
        1: "high-risk screening",
        2: "lesion follow-up",
        3: "recent cancer diagnosis",
        4: "symptoms"
    }
    if "mr_indication_mri" in merged.columns:
        merged["mr_indication_mri"] = merged["mr_indication_mri"].map(mr_map)

    # 9.2 treatment_status_mri
    mr_map = {
        1: "pre-tx",
        2: "post-tx",
    }
    if "treatment_status_mri" in merged.columns:
        merged["treatment_status_mri"] = merged["treatment_status_mri"].map(mr_map)

    # 9.3 Replace lymph_nodes_mri
    ln_map = {
        1: "not biopsied",
        2: "benign",
        3: "malignant",
    }
    if "lymph_nodes_mri" in merged.columns:
        merged["lymph_nodes_mri"] = merged["lymph_nodes_mri"].map(ln_map)

    # 9.4 Replace mr_facility_mri
    ln_map = {
        1: "ROPCC",
        2: "KOP",
        3: "ACTRI",
        4: "Other"
    }
    if "mr_facility_mri" in merged.columns:
        merged["mr_facility_mri"] = merged["mr_facility_mri"].map(ln_map)

    # 10. Collapse MRI type one-hot columns into a single type_mri column
    # ---------------------------------------------------------

    type_map = {
        "type___m_mri": "mass",
        "type___nme_mri": "nme",
        "type___mnme_mri": "mass + nme",
        "type___inme_mri": "intervening nme",
        "type___iml_mri": "intramammary LN",
        "type___nm_mri": "no-mass"
    }

    type_cols = list(type_map.keys())

    def collapse_types(row):
        active = []
        for col, label in type_map.items():
            if col in row and row[col] in [1, "1", True]:
                active.append(label)
        if not active:
            return None

        ordering = ["mass", "nme", "non-mass", "mnme", "inme", "iml"]
        active_sorted = [t for t in ordering if t in active]

        return " + ".join(active)

    merged["type_mri"] = merged.apply(collapse_types, axis=1)
    merged = merged.drop(columns=type_cols)
    cols = merged.columns.tolist()

    if "type_mri" in cols and "lesion_status" in cols:
        cols.insert(cols.index("lesion_status") + 1, cols.pop(cols.index("type_mri")))
        merged = merged[cols]

    # ---------------------------------------------------------
    # 11. FINAL CLEANUP: delete unwanted columns
    # ---------------------------------------------------------
    cols_to_drop = [c for c in COLUMNS_TO_DELETE if c in merged.columns]
    merged = merged.drop(columns=cols_to_drop)

    # ---------------------------------------------------------
    # 12. Save final lesion-centric table
    # ---------------------------------------------------------
    os.makedirs(os.path.dirname(LESIONS_LONG_PATH), exist_ok=True)
    merged.to_csv(LESIONS_LONG_PATH, index=False)

    print(f"[reshape] Created {LESIONS_LONG_PATH} with {len(merged)} rows")
    return merged


def validate_lesions(lesions_df):
    lines = []

    def add(msg):
        print("[validate]", msg)
        lines.append(msg)

    add("Validation Report")
    add(f"Total lesion rows: {len(lesions_df)}")

    if "lesion_number" not in lesions_df.columns:
        add("ERROR: lesion_number missing")
    else:
        invalid = lesions_df[
            ~lesions_df["lesion_number"].between(1, MAX_LESIONS)
        ]
        if not invalid.empty:
            add(f"WARNING: {len(invalid)} invalid lesion numbers")

    key_fields = ["side", "position", "image_finding", "small", "long"]

    for field in key_fields:
        if field not in lesions_df.columns:
            add(f"Missing field: {field}")
            continue

        missing = lesions_df[field].isna().sum()
        if missing > 0:
            add(f"{missing} missing values in {field} ({describe_field(field)})")

    with open(VALIDATION_REPORT_PATH, "w") as f:
        f.write("\n".join(lines))

    print(f"[validate] Saved report to {VALIDATION_REPORT_PATH}")


def main():
    download_redcap_export()
    lesions_df = reshape_to_lesions()
    validate_lesions(lesions_df)

    if os.path.exists(RAW_CSV_PATH):
        os.remove(RAW_CSV_PATH)
        print(f"[cleanup] Deleted raw REDCap export: {RAW_CSV_PATH}")


if __name__ == "__main__":
    main()