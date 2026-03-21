import os
import re
import requests
import pandas as pd
import numpy as np 

from config import (
    REDCAP_API_URL,
    REDCAP_TOKEN,
    REDCAP_PAYLOAD,
    RAW_CSV_PATH,
    LESIONS_LONG_PATH,
    VALIDATION_REPORT_PATH,
    META_COLS,
    COLUMNS_TO_DELETE,
    MAX_LESIONS,
)

from dictionaries import (
    describe_field, 
    MR_MAP, 
    TX_MAP,
    LN_MAP,
    MR_FACILITY_MAP,
    TYPE_MAP,
)

def download_redcap_export():
    os.makedirs(os.path.dirname(RAW_CSV_PATH), exist_ok=True)

    payload = REDCAP_PAYLOAD

    resp = requests.post(REDCAP_API_URL, data=payload)
    resp.raise_for_status()

    with open(RAW_CSV_PATH, "wb") as f:
        f.write(resp.content)

    print(f"[download] Saved REDCap export to {RAW_CSV_PATH}")


def reshape_to_lesions() -> pd.DataFrame:
    df = pd.read_csv(RAW_CSV_PATH)

    # ---------------------------------------------------------
    # 1. Normalize lesion-level MRI column names
    # ---------------------------------------------------------
    rename_map = {}

    for i in range(1, MAX_LESIONS + 1):
        # lesion1position → lesion1_position
        old = f"lesion{i}position"
        new = f"lesion{i}_position"
        if old in df.columns:
            rename_map[old] = new

        # lesion_1_side → lesion1_side
        old = f"lesion_{i}_side"
        new = f"lesion{i}_side"
        if old in df.columns:
            rename_map[old] = new

        # l1small → lesion1_small, l1long → lesion1_long
        old_small = f"l{i}small"
        old_long = f"l{i}long"
        new_small = f"lesion{i}_small"
        new_long = f"lesion{i}_long"
        if old_small in df.columns:
            rename_map[old_small] = new_small
        if old_long in df.columns:
            rename_map[old_long] = new_long

    if rename_map:
        df = df.rename(columns=rename_map)

    # ---------------------------------------------------------
    # 2. Propagate anonymized_number and date_of_birth per MRN
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
    # 3. Split MRI and pathology visits
    # ---------------------------------------------------------
    mri_df = df[df["mri_scan_date"].notna()].copy()
    path_df = df[df["biopsy_date"].notna()].copy()

    # ---------------------------------------------------------
    # 4. Reshape MRI visits into long format
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
                    **lesion_clean,
                })
        else:
            meta = {m: row.get(m) for m in META_COLS if m in row.index}
            mri_rows.append({
                **meta,
                "lesion_number": 0,
                "lesion_status": "negative",
            })

    mri_long = pd.DataFrame(mri_rows)

    # ---------------------------------------------------------
    # 5. Reshape pathology visits into long format
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
                **lesion_clean,
            })

    path_long = pd.DataFrame(path_rows)

    # ---------------------------------------------------------
    # 6. Merge MRI + pathology lesion tables
    # ---------------------------------------------------------
    merged = mri_long.merge(
        path_long,
        on=["anonimized_number", "lesion_number"],
        how="outer",
        suffixes=("_mri", "_path"),
    )

    # ---------------------------------------------------------
    # 7. Remove fake positive lesions (no MRI image finding)
    # ---------------------------------------------------------
    mri_finding_cols = [
        c for c in merged.columns
        if "image_finding" in c and c.endswith("_mri")
    ]

    if mri_finding_cols:
        merged = merged[
            ~(
                (merged["lesion_status"] == "positive") &
                merged[mri_finding_cols].isna().all(axis=1)
            )
        ]

    # ---------------------------------------------------------
    # 8. Parse dates and apply date filter
    # ---------------------------------------------------------
    for col in ["mri_scan_date_mri", "biopsy_date_path"]:
        if col in merged.columns:
            merged[col] = pd.to_datetime(
                merged[col],
                format="%Y-%m-%d",
                errors="coerce",
            )

    cutoff = pd.Timestamp("2023-06-23")
    merged = merged[
        (
            merged.get("mri_scan_date_mri").notna() &
            (merged["mri_scan_date_mri"] > cutoff)
        ) |
        (
            merged.get("biopsy_date_path").notna() &
            (merged["biopsy_date_path"] > cutoff)
        )
    ]

    # ---------------------------------------------------------
    # 9. Replace numeric codes with human-readable labels
    # ---------------------------------------------------------
    if "mr_indication_mri" in merged.columns:
        merged["mr_indication_mri"] = merged["mr_indication_mri"].map(MR_MAP)

    if "treatment_status_mri" in merged.columns:
        merged["treatment_status_mri"] = merged["treatment_status_mri"].map(TX_MAP)

    if "lymph_nodes_mri" in merged.columns:
        merged["lymph_nodes_mri"] = merged["lymph_nodes_mri"].map(LN_MAP)

    if "mr_facility_mri" in merged.columns:
        merged["mr_facility_mri"] = merged["mr_facility_mri"].map(MR_FACILITY_MAP)

    # ---------------------------------------------------------
    # 10. Collapse MRI type one-hot columns into type_mri
    # ---------------------------------------------------------
    type_cols = [c for c in TYPE_MAP.keys() if c in merged.columns]

    def collapse_types(row):
        active = []
        for col, label in TYPE_MAP.items():
            if col in row and row[col] in [1, "1", True]:
                active.append(label)
        if not active:
            return None

        ordering = ["mass", "nme", "non-mass", "mass + nme", "intervening nme", "intramammary LN"]
        active_sorted = [t for t in ordering if t in active]

        return " + ".join(active_sorted) if active_sorted else None

    if type_cols:
        merged["type_mri"] = merged.apply(collapse_types, axis=1)
        merged = merged.drop(columns=type_cols)

        cols = merged.columns.tolist()
        if "type_mri" in cols and "lesion_status" in cols:
            cols.insert(cols.index("lesion_status") + 1, cols.pop(cols.index("type_mri")))
            merged = merged[cols]

    # ---------------------------------------------------------
    # 11. Final cleanup: delete unwanted columns from config
    # ---------------------------------------------------------
    cols_to_drop = [c for c in COLUMNS_TO_DELETE if c in merged.columns]
    if cols_to_drop:
        merged = merged.drop(columns=cols_to_drop)

    # ---------------------------------------------------------
    # 12. Save final lesion-centric table
    # ---------------------------------------------------------
    os.makedirs(os.path.dirname(LESIONS_LONG_PATH), exist_ok=True)
    merged.to_csv(LESIONS_LONG_PATH, index=False)

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