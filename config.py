import os

## [ChiSquaredConfig]
ERROR_THRESHOLD = 0.05
XS_THRESHOLD_PERCENTAGE = 5  # %
FIT = "n"


# HOME_DIR = "/home/shuri/Documents"
HOME_DIR = "/Users/okumuras/Documents/codes"
TALYS_PATH = os.path.join(HOME_DIR, "talys")
CALC_PATH = os.path.join(HOME_DIR, f"medical/calc026_a_fit_{FIT}")
EXFORTABLES_PATH = os.path.join(HOME_DIR, "exfortables")
TALYS_INP_FILE_NAME = "talys.inp"


IAEA_MEDICAL_LIST = "./data/IAEA_medical_isotope.dat"
SCORE_JSON_PATH = os.path.join(HOME_DIR, "talys/json")

ENERGY_RANGE_MIN = 1.0
ENERGY_RANGE_MAX = 60.0
ENERGY_STEP = 0.5


## Number of parallel processes
N = 5
TIMEOUT_SECONDS = 2000
LATEX_DOCUMENT_FILENAME = f"{os.path.basename(CALC_PATH)}.tex"
