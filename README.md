# REDCap_breast_database_export
Shell/Python scripts to automatically pull database report from REDCap and format it

This project downloads REDCap records via API, reshapes them from
wide (one row per event) to long (one row per lesion), validates the
result, and saves clean outputs.

## Usage

1. Add your REDCap API token to `src/config.py` or export it as an environment variable.
2. Run the pipeline:
