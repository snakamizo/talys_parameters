import os
from subprocess import Popen, PIPE
import glob
from pathlib import Path
import re
import logging
from config import TALYS_PATH, FIT


def create_talys_inp(input_file, inputs, energy_range, parameters):
    if not inputs:
        return
    else:
        projectile = inputs.get("projectile")
        element = inputs.get("element")
        mass = inputs.get("mass")

        ldmodel = parameters.get("ldmodel")
        colenhance = parameters.get("colenhance")

        with open(input_file, "w") as f:
            f.write("#\n")
            f.write(f"#  {projectile}-{element}\n")
            f.write("#\n")
            f.write("# General\n")
            f.write("#\n")
            f.write(f"projectile {projectile}\n")
            f.write(f"element {element}\n")
            f.write(f"mass {mass}\n")
            f.write(f"energy {energy_range}\n")
            f.write("#\n")
            f.write("# Parameters\n")
            f.write("#\n")
            f.write(f"ldmodel {ldmodel}\n")
            f.write(f"colenhance {colenhance}\n")
            f.write(f"fit {FIT}\n")
            f.write("partable y\n")
            f.write("channels y\n")
            f.write("sacs y\n")

        logging.info(f"File '{input_file}' created successfully!")


def run_talys(input_file, calc_directory):

    p = Popen(
        [os.path.join(TALYS_PATH, "bin/talys")],
        cwd=calc_directory,
        stdin=open(input_file),
        stdout=PIPE,
        stderr=PIPE,
    )

    stdout, stderr = p.communicate()

    with open(os.path.join(calc_directory, "output.txt"), "w") as outfile:
        outfile.write(stderr.decode("utf-8"))
        outfile.write(stdout.decode("utf-8"))

    return


def search_residual_output(directory, product_six_digit_code):
    # Check if the last character of the six-digit code is a letter
    matched_files = []
    last_char = product_six_digit_code[-1]
    # Set the pattern based on the letter (if present)
    if last_char == "g":
        pattern = os.path.join(directory, f"rp*{product_six_digit_code[:-1]}*.L00")
        matched_files = glob.glob(pattern)
    elif last_char == "m":
        pattern = os.path.join(directory, f"rp*{product_six_digit_code[:-1]}*.L*")
        matched_files = [
            file for file in glob.glob(pattern) if not file.endswith(".L00")
        ]
    else:
        pattern = os.path.join(directory, f"rp*{product_six_digit_code}*.tot")
        matched_files = glob.glob(pattern)

    if len(matched_files) > 0:
        return matched_files[0]

    else:
        return None


def extract_code_from_filename(filename):
    # Get the base name of the file
    base_name = os.path.basename(filename)

    # Split by hyphens
    parts = base_name.split("-")

    if len(parts) < 4:  # We expect at least four parts for a valid filename
        print(
            f"Could not extract code from file: {filename} - filename format is unexpected."
        )
        return None

    # Check the last part (before the year) for the expected format
    code_part = parts[-1].split(".")[0]  # Remove file extension
    if re.match(r"^[A-Za-z0-9]{8,9}$", code_part):
        return code_part

    print(f"Could not extract code from file: {filename} - no valid code found.")
    return None
