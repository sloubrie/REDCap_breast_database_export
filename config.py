import os

REDCAP_API_URL = "https://redcap.ucsd.edu/api/"
REDCAP_TOKEN = os.getenv("REDCAP_TOKEN")

RAW_CSV_PATH = "/space/wil-syn01/1/cmig_body/RSIData/Breast/UCSD/Multiband/metadata/raw_redcap_export.csv"
LESIONS_LONG_PATH = "/space/wil-syn01/1/cmig_body/RSIData/Breast/UCSD/Multiband/metadata/breast_database.csv"
VALIDATION_REPORT_PATH = "/space/wil-syn01/1/cmig_body/RSIData/Breast/UCSD/Multiband/metadata/validation_report.txt"

META_COLS = [
    "anonimized_number",
    "redcap_data_access_group",
    "break_the_glass",
    "date_of_birth",
    "redcap_event_name",
    "mri_scan_date",
    "biopsy_date",
    "mr_indication",
    "treatment_status",
    "lymph_nodes",
    "other_mr_facility",
    "accession_number",
    "number_of_lesions",
    "pathology_type",
    "pathology_source",
    "specimen_number",
    "pathology_text",
]

MAX_LESIONS = 5