import os
import re
import requests
import pandas as pd

from config import (
    REDCAP_API_URL,
    REDCAP_TOKEN,
    RAW_CSV_PATH,
    LESIONS_LONG_PATH,
    VALIDATION_REPORT_PATH,
    META_COLS,
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
    df = pd.read_csv(RAW_CSV_PATH)

    # 1. Propagate anonymized_number across all visits per MRN
    if "mrn" in df.columns and "anonimized_number" in df.columns:
        df["anonimized_number"] = (
            df.groupby("mrn")["anonimized_number"]
              .transform(lambda x: x.ffill().bfill())
        )

    long_rows = []

    # 2. Build long-format lesion rows
    for _, row in df.iterrows():
        for lesion_num in range(1, MAX_LESIONS + 1):
            prefix = f"lesion{lesion_num}_"
            lesion_cols = [c for c in df.columns if c.startswith(prefix)]

            if not lesion_cols:
                continue

            lesion_data = {c: row[c] for c in lesion_cols}

            if all(pd.isna(v) for v in lesion_data.values()):
                continue

            lesion_clean = {
                re.sub(f"^{prefix}", "", k): v
                for k, v in lesion_data.items()
            }

            meta_data = {m: row[m] for m in META_COLS if m in df.columns}

            combined = {**meta_data, **lesion_clean}
            combined["lesion_number"] = lesion_num

            long_rows.append(combined)

    # 3. Convert to DataFrame
    lesions_df = pd.DataFrame(long_rows)

    # 4. Drop MRN (privacy)
    if "mrn" in lesions_df.columns:
        lesions_df = lesions_df.drop(columns=["mrn"])

    # 5. Keep only events after 2023-06-23
    if "mri_scan_date" in lesions_df.columns:
        lesions_df["mri_scan_date"] = pd.to_datetime(lesions_df["mri_scan_date"], errors="coerce")
        cutoff = pd.Timestamp("2023-06-23")
        lesions_df = lesions_df[lesions_df["mri_scan_date"] > cutoff]

    # 6. Move anonimized_number to the first column
    cols = lesions_df.columns.tolist()
    if "anonimized_number" in cols:
        cols.insert(0, cols.pop(cols.index("anonimized_number")))
        lesions_df = lesions_df[cols]

    # 7. Save final long-format table
    os.makedirs(os.path.dirname(LESIONS_LONG_PATH), exist_ok=True)
    lesions_df.to_csv(LESIONS_LONG_PATH, index=False)

    print(f"[reshape] Created {LESIONS_LONG_PATH} with {len(lesions_df)} rows")
    return lesions_df


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