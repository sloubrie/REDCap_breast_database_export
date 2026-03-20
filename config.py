import os

REDCAP_API_URL = "https://redcap.ucsd.edu/api/"
REDCAP_API_TOKEN = os.getenv("REDCAP_TOKEN")

RAW_CSV_PATH = "data/raw_redcap_export.csv"
LESIONS_LONG_PATH = "data/lesions_long.csv"
VALIDATION_REPORT_PATH = "data/validation_report.txt"

META_COLS = [
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