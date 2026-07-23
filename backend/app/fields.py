"""Single source of truth for the application form.

The frontend renders its inputs from this schema and the Excel export
builds its columns from it, so the two can never drift apart.
"""
import os

# The printed form asks for the student's CET portal password. Collecting it
# on a public website means anyone with database access could log into a
# student's official CET account. Off by default; flip the env var if your
# office accepts that risk.
COLLECT_CET_PASSWORD = os.getenv("COLLECT_CET_PASSWORD", "false").lower() == "true"

YN = ["Yes", "No"]

SECTIONS = [
    {
        "id": "neet",
        "title": "NEET-UG Details",
        "help": "Copy these exactly from your NEET score card.",
        "fields": [
            {"k": "neet_roll", "l": "NEET Roll No", "req": True},
            {"k": "neet_appno", "l": "NEET Application No.", "req": True},
            {"k": "dob_neet", "l": "Date of Birth (as per NEET)", "t": "date", "req": True},
            {"k": "neet_rank", "l": "NEET Rank (All India Rank)", "req": True},
            {"k": "neet_marks", "l": "NEET Marks", "req": True},
            {"k": "pcb_total", "l": "PCB Total (out of 720)"},
            {"k": "phy_pct", "l": "Physics Percentile Score"},
            {"k": "che_pct", "l": "Chemistry Percentile Score"},
            {"k": "bio_pct", "l": "Biology Percentile Score"},
            {"k": "tot_pct", "l": "Total Percentile Score"},
        ],
    },
    {
        "id": "personal",
        "title": "Personal Information",
        "help": "Your name must match the NEET score card letter for letter.",
        "fields": [
            {"k": "full_name", "l": "Full name of candidate", "hint": "as per NEET score card", "req": True, "w": 2},
            {"k": "name_changed", "l": "Name changed after 10th or after marriage?", "t": "sel", "o": YN},
            {"k": "father_name", "l": "Father's first name", "req": True},
            {"k": "mother_name", "l": "Mother's first name", "req": True},
            {"k": "gender", "l": "Gender", "t": "sel", "o": ["Male", "Female", "Other"], "req": True},
            {"k": "dob", "l": "Date of Birth", "t": "date", "req": True},
            {"k": "cet_mobile", "l": "CET registration mobile number", "req": True},
            {"k": "alt_contact", "l": "Alternate contact number"},
            {"k": "cet_email", "l": "CET registered Email ID", "t": "email", "req": True},
            {"k": "alt_email", "l": "Alternate Email ID", "t": "email"},
            {"k": "aadhaar", "l": "Aadhaar card number", "hint": "kept confidential"},
            {"k": "religion", "l": "Religion"},
            {"k": "mother_tongue", "l": "Mother tongue"},
            {"k": "apaar_id", "l": "APAAR ID"},
        ],
    },
    {
        "id": "address",
        "title": "Permanent Address",
        "help": "Address as written on your domicile certificate.",
        "fields": [
            {"k": "address", "l": "Full address", "t": "area", "req": True, "w": 3},
            {"k": "city", "l": "City", "req": True},
            {"k": "taluka", "l": "Taluka", "req": True},
            {"k": "district", "l": "District", "req": True},
            {"k": "state", "l": "State", "req": True},
            {"k": "pincode", "l": "Pin code", "req": True},
        ],
    },
    {
        "id": "reservation",
        "title": "Reservation and Category",
        "help": "Fill only the certificate details you actually hold. Leave the rest blank.",
        "fields": [
            {"k": "nationality", "l": "Nationality", "t": "sel", "o": ["Indian", "Other country"], "req": True},
            {"k": "domicile_mh", "l": "Domicile of Maharashtra?", "t": "sel", "o": YN, "req": True},
            {"k": "oci", "l": "OCI card holder?", "t": "sel", "o": YN},
            {"k": "nri", "l": "Applying as NRI?", "t": "sel", "o": YN},
            {"k": "region_res", "l": "Region of residence", "t": "sel",
             "o": ["Nagarpalika", "Mahanagarpalika", "Gram Panchayat"]},
            {"k": "category", "l": "Category of candidate", "t": "sel", "req": True,
             "o": ["Open / General", "SC", "ST", "OBC", "VJ(A)", "NT(B)", "NT(C)", "NT(D)",
                   "SEBC", "SBC", "EWS"]},
            {"k": "sub_category", "l": "Sub category (if any)"},

            {"k": "has_caste_cert", "l": "Possess caste certificate?", "t": "sel", "o": YN},
            {"k": "caste_cert_no", "l": "Caste certificate number (outward no.)"},
            {"k": "caste_cert_date", "l": "Caste certificate issuing date", "t": "date"},
            {"k": "caste_cert_auth", "l": "Caste certificate issuing authority"},
            {"k": "caste_cert_dist", "l": "Caste certificate issuing district / taluka"},

            {"k": "has_caste_val", "l": "Possess caste validity?", "t": "sel", "o": YN},
            {"k": "caste_val_no", "l": "Caste validity number (VC no.)"},
            {"k": "caste_val_date", "l": "Caste validity issuing date", "t": "date"},
            {"k": "caste_val_auth", "l": "Caste validity issuing authority"},
            {"k": "caste_val_dist", "l": "Caste validity issuing district / taluka"},

            {"k": "has_ncl", "l": "Possess NCL certificate?", "hint": "needed for VJ / NT / OBC / SBC",
             "t": "sel", "o": ["Yes", "No", "Not applicable"]},
            {"k": "ncl_no", "l": "NCL certificate number (outward no.)"},
            {"k": "ncl_date", "l": "NCL certificate issuing date", "t": "date"},
            {"k": "ncl_auth", "l": "NCL certificate issuing authority"},
            {"k": "ncl_dist", "l": "NCL certificate issuing district / taluka"},

            {"k": "annual_income", "l": "Annual family income"},
            {"k": "income_1yr", "l": "Income certificate (1 year valid)", "t": "sel", "o": YN},
            {"k": "income_3yr", "l": "Income certificate (1 to 3 year valid)", "t": "sel", "o": YN},

            {"k": "minority_religious", "l": "Religious minority quota", "t": "sel",
             "o": ["Not claiming", "Muslim", "Jain", "Christian"]},
            {"k": "minority_linguistic", "l": "Claim linguistic minority?",
             "hint": "affidavit compulsory", "t": "sel", "o": YN},
            {"k": "orphan", "l": "Is the candidate an orphan?", "t": "sel", "o": YN},
            {"k": "orphan_cert", "l": "Orphan certificate available?", "t": "sel",
             "o": ["Yes", "No", "Not applicable"]},
            {"k": "pwd", "l": "Person with disability (PWD)?", "t": "sel", "o": YN},
        ],
    },
    {
        "id": "ssc",
        "title": "SSC / 10th Qualification",
        "fields": [
            {"k": "ssc_year", "l": "Year of passing", "req": True},
            {"k": "ssc_language", "l": "One of the languages studied"},
            {"k": "ssc_state", "l": "State of SSC passing", "req": True},
            {"k": "ssc_district", "l": "District of SSC passing", "req": True},
            {"k": "ssc_taluka", "l": "Taluka of SSC passing"},
            {"k": "ssc_out_of", "l": "10th marks out of"},
            {"k": "ssc_obtained", "l": "10th marks obtained"},
            {"k": "ssc_percent", "l": "10th percentage"},
        ],
    },
    {
        "id": "hsc",
        "title": "HSC / 12th Qualification",
        "help": "Your Home University is decided by the district where you passed 12th.",
        "fields": [
            {"k": "hsc_exam", "l": "HSC / 12th equivalent examination"},
            {"k": "hsc_year", "l": "Passing year", "req": True},
            {"k": "hsc_rollno", "l": "Roll no. / seat no.", "req": True},
            {"k": "hsc_state", "l": "State of HSC passing", "req": True},
            {"k": "hsc_district", "l": "District of HSC passing", "hint": "12th pass district", "req": True},
            {"k": "hsc_taluka", "l": "Taluka of HSC passing"},
            {"k": "hsc_phy_obt", "l": "Physics — marks obtained"},
            {"k": "hsc_phy_out", "l": "Physics — marks out of"},
            {"k": "hsc_che_obt", "l": "Chemistry — marks obtained"},
            {"k": "hsc_che_out", "l": "Chemistry — marks out of"},
            {"k": "hsc_bio_obt", "l": "Biology — marks obtained"},
            {"k": "hsc_bio_out", "l": "Biology — marks out of"},
            {"k": "hsc_eng_obt", "l": "English — marks obtained"},
            {"k": "hsc_eng_out", "l": "English — marks out of"},
            {"k": "hsc_out_of", "l": "12th total marks out of"},
            {"k": "hsc_obtained", "l": "12th total marks obtained"},
            {"k": "hsc_percent", "l": "12th percentage"},
        ],
    },
    {
        "id": "parallel",
        "title": "Parallel Reservation",
        "help": "A hilly area claim needs 11th and 12th studied in a hilly area.",
        "fields": [
            {"k": "claim_exception", "l": "Claiming a specified (parallel) reservation?", "t": "sel", "o": YN},
            {"k": "hilly_area", "l": "Claiming hilly area reservation?", "t": "sel", "o": YN},
            {"k": "hilly_village", "l": "Hilly area village"},
            {"k": "hilly_taluka", "l": "Hilly area taluka"},
            {"k": "pwd_reservation", "l": "Claiming PWD reservation?", "t": "sel", "o": YN},
            {"k": "pwd_cert", "l": "Disability certificate available (42% or above)?",
             "t": "sel", "o": ["Yes", "No", "Not applicable"]},
            {"k": "defence_res", "l": "Claiming defence reservation?", "t": "sel", "o": YN},
            {"k": "defence_type", "l": "Defence certificate type", "t": "sel",
             "o": ["D1 — Ex-serviceman", "D2 — Current serviceman",
                   "D3 — Other state / transfer", "Not applicable"]},
        ],
    },
    {
        "id": "course",
        "title": "Course Choice and Application Fees",
        "fields": [
            {"k": "group_a", "l": "Group A — MBBS / BDS", "t": "sel", "o": YN},
            {"k": "group_b", "l": "Group B — BAMS / BHMS", "t": "sel", "o": YN},
            {"k": "group_c", "l": "Group C — BPT", "t": "sel", "o": YN},
            {"k": "quota", "l": "Applying for", "t": "sel", "o": ["State quota", "IQ quota", "Both"], "req": True},
            {"k": "app_fees", "l": "Application fees paid"},
            {"k": "fee_date", "l": "Fee payment date", "t": "date"},
        ],
    },
]

DOCUMENTS = [
    "Admit card / hall ticket of NEET-UG",
    "NEET-UG marksheet",
    "H.S.C. (or equivalent) marksheet",
    "S.S.C. passing certificate (for date of birth)",
    "School leaving certificate — H.S.C.",
    "Nationality certificate / passport / domicile",
    "Domicile certificate (Maharashtra only)",
    "Caste certificate",
    "Caste validity certificate",
    "Non-creamy layer certificate",
    "Medical fitness certificate (Annexure-H)",
    "Minority certificate with affidavit (Annexure-G)",
    "Defence quota certificate D1 / D2 / D3 (Annexure-F)",
    "Hilly area certificate",
]
DOC_STATUS = ["Have it", "Applying for it", "Not applicable"]

if COLLECT_CET_PASSWORD:
    for _s in SECTIONS:
        if _s["id"] == "personal":
            _s["fields"].append({"k": "cet_password", "l": "CET registration password"})


def all_fields():
    out = []
    for s in SECTIONS:
        out.extend(s["fields"])
    return out


def field_labels():
    """Ordered {key: label} for every scalar field."""
    return {f["k"]: f["l"] for f in all_fields()}


def schema_payload():
    return {
        "sections": SECTIONS,
        "documents": DOCUMENTS,
        "doc_status": DOC_STATUS,
    }
