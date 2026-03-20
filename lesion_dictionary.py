LESION_FIELD_LABELS = {
    "distance_from_nipple": "Distance from nipple",
    "position": "Lesion position",
    "side": "Breast side",
    "image_finding": "Imaging finding",
    "small": "Short axis",
    "long": "Long axis",
    "type___m": "Mass",
    "type___nme": "Non-mass enhancement",
    "type___mnme": "Mass + NME",
    "type___inme": "Internal NME",
    "type___iml": "Irregular mass lesion",
    "type___nm": "Non-mass (other)",
    "benign_or_malignant": "Benign vs malignant",
    "type_comment": "Pathology comment",
    "dcis": "DCIS",
    "mbr": "Modified Bloom–Richardson grade",
    "nuclear_grade": "Nuclear grade",
    "tubular_formation": "Tubular formation",
    "mitosis": "Mitosis score",
    "estrogen_receptor_status": "ER status",
    "progesterone_receptor_stat": "PR status",
    "her2_status": "HER2 status",
}

def describe_field(field_name: str) -> str:
    return LESION_FIELD_LABELS.get(field_name, field_name)