import os

REDCAP_API_URL = "https://YOUR_REDCAP_SERVER/api/"
REDCAP_API_TOKEN = os.getenv("REDCAP_API_TOKEN", "PUT_YOUR_TOKEN_HERE")

RAW_CSV_PATH = "data/raw_redcap_export.csv"
LESIONS_LONG_PATH = "data/lesions_long.csv"
VALIDATION_REPORT_PATH = "data/validation_report.txt"

META_COLS = [
    "mrn",
    "redcap_event_name",
    "redcap_data_access_group",
    "break_the_glass",
    "anonimized_number",
    "secondary_anonymization_id",
    "date_of_birth",
    "mri_scan_date",
    "pathology_complete",
]

MAX_LESIONS = 5