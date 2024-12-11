import os

## [ChiSquaredConfig]
ERROR_THRESHOLD = 0.05
XS_THRESHOLD_PERCENTAGE = 5 # % 
FIT = "n"


TALYS_PATH = "/home/shuri/Documents/talys"
CALC_PATH = f"/home/shuri/Documents/talys/medical/calc026_a_fit_{FIT}"
EXFORTABLES_PATH = "/home/shuri/Documents/exfortables"
TALYS_INP_FILE_NAME = "talys.inp"
# GNUPLOT_OUTPUT_DIRECTORY_NAME = gnuplot_output_


IAEA_MEDICAL_LIST = "/home/shuri/Documents/calculate_chi_square_total/data/IAEA_medical_isotope.dat"

SCORE_JSON_PATH = "/home/shuri/Documents/talys/json"

ENERGY_RANGE_MIN = 1.0
ENERGY_RANGE_MAX = 60.0
ENERGY_STEP = 0.5



## Number of parallel processes
N = 5
TIMEOUT_SECONDS = 2000

LATEX_DOCUMENT_FILENAME = f"{os.path.basename(CALC_PATH)}.tex"