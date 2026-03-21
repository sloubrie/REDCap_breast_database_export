MR_MAP = {
    1: "high-risk screening",
    2: "lesion follow-up",
    3: "recent cancer diagnosis",
    4: "symptoms",
    "1": "high-risk screening",
    "2": "lesion follow-up",
    "3": "recent cancer diagnosis",
    "4": "symptoms",
}

TX_MAP = {
        1: "pre-tx",
        2: "post-tx",
        "1": "pre-tx",
        "2": "post-tx",
    }

LN_MAP = {
        1: "not biopsied",
        2: "benign",
        3: "malignant",
        "1": "not biopsied",
        "2": "benign",
        "3": "malignant",
    }

MR_FACILITY_MAP = {
        1: "ROPCC",
        2: "KOP",
        3: "ACTRI",
        4: "Other",
        "1": "ROPCC",
        "2": "KOP",
        "3": "ACTRI",
        "4": "Other",
    }

# MRI lesion type map (one-hot → human-readable)
TYPE_MAP = {
        "type___m_mri": "mass",
        "type___nme_mri": "nme",
        "type___mnme_mri": "mass + nme",
        "type___inme_mri": "intervening nme",
        "type___iml_mri": "intramammary LN",
        "type___nm_mri": "non-mass",
    }

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