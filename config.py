import os

REDCAP_API_URL = "https://redcap.ucsd.edu/api/"
REDCAP_TOKEN = os.getenv("REDCAP_TOKEN")

# REDCap API export payload
REDCAP_PAYLOAD = {
    "token": REDCAP_TOKEN,
    "content": "record",
    "format": "csv",
    "type": "flat",
    "exportDataAccessGroups": "true",
    "rawOrLabel": "raw",
    "rawOrLabelHeaders": "raw",
    "exportCheckboxLabel": "false",
}

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
    "mr_facility",
    "accession_number",
    "number_of_lesions",
    "pathology_type",
    "pathology_source",
    "specimen_number",
    "pathology_text",
    "mri_complete",
]

COLUMNS_TO_DELETE = [
        # Add any columns you want removed from the final table:
        "biopsy_date_mri",
        "pathology_type_mri",
        "pathology_source_mri",
        "specimen_number_mri",
        "pathology_text_mri",
        "benign_or_malignant_mri",
        "type_comment_mri",
        "dcis_mri",
        "mbr_mri",
        "nuclear_grade_mri",
        "tubular_formation_mri",
        "mitosis_mri",
        "estrogen_receptor_status_mri",
        "progesterone_receptor_stat_mri",
        "her2_status_mri",
        "redcap_data_access_group_path",
        "break_the_glass_path",
        "date_of_birth_path",
        "mri_scan_date_path",
        "mr_indication_path",
        "treatment_status_path",
        "lymph_nodes_path",
        "mr_facility_path",
        "accession_number_path",
        "number_of_lesions_path",
        "type___m_path",
        "type___nme_path",
        "type___mnme_path",
        "type___inme_path",
        "type___iml_path",
        "type___nm_path",
        "distance_from_nipple_path",
        "image_finding_path",
        "position_path",
        "side_path",
        "small_path",
        "long_path",
        "mri_complete_path",
]

MAX_LESIONS = 5