import re
import json
import os
import logging
from script.elem import elemtoz, PARTICLES

def open_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file {file_path}: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while opening {file_path}: {e}")
        return None


def get_number_from_string(x):
    return re.sub(r"\D+", "", x)


def get_str_from_string(x):
    return re.sub(r"\d+", "", str(x))


def split_by_number(x) -> list:
    ## retrun list for e.g.
    # ['Br', '077', '']
    # ['Br', '077', 'g']
    # ['Br', '077', 'm']
    return re.split(r"(\d+)", x)


def file_check(json_file_path):
    try:
        with open(json_file_path, "r") as file:
            content = file.read()
            print("Raw file content:", repr(content))
            userinputs = json.loads(content)
            print("JSON data loaded successfully:", userinputs)
        return userinputs

    except FileNotFoundError:
        print("Error: File not found.")

    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)

    except Exception as e:
        print("An unexpected error occurred:", e)


def clean_data_file(input_file, cleaned_file):
    with open(input_file, "r") as infile, open(cleaned_file, "w") as outfile:
        for line in infile:
            cleaned_line = " ".join(line.split())
            outfile.write(cleaned_line + "\n")


def generate_residual_product_fname(residual):
    ## Assuming the format as: "Mn052m"
    r = split_by_number(residual)
    z = elemtoz(r[0].capitalize()).zfill(3)
    a = r[1].zfill(3)

    if r[2]:
        fextention = {
            "m": "L01",
            "n": "L02",
            "l": "L03",
            "g": "L00",
        }
        return f"{z}{a}.{fextention[ r[2] ]}"
    else:
        return f"{z}{a}.tot"


def calc_mass(reaction, mass):
    if reaction == "pn":
        return str(int(mass))
    elif reaction == "ppn":
        return str(int(mass) - 1)
    elif reaction == "p2n":
        return str(int(mass) - 1)
    else:
        return None


def calc_z(reaction, element):
    if reaction == "pn":
        return str(int(elemtoz(element.capitalize())) + 1)
    elif reaction == "ppn":
        return str(int(elemtoz(element.capitalize())))
    elif reaction == "p2n":
        return str(int(elemtoz(element.capitalize())) + 1)
    else:
        return None


def calc_charge(projectile, outgoing, charge):
    return int(charge) - PARTICLES[projectile][1]


def genenerate_six_digit_code(reaction, element, mass):
    # assuming reaction: only "pn", "ppn", and "p2n" so far
    z = calc_z(reaction, element).zfill(3)
    a = calc_mass(reaction, mass).zfill(3)

    return f"{z}{a}"


def generate_six_digit_code_from_product_info(residual):
    ## Assuming the format as: "Mn052m"
    z = elemtoz(residual[0].capitalize()).zfill(3)
    a = residual[1].zfill(3)

    return f"{z}{a}{residual[2]}"


def setup_logging(log_directory, log_file_name):
    log_file_path = os.path.join(log_directory, log_file_name)
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file_path),  # Save the log in file
            logging.StreamHandler(),  # Show the log in terminal
        ],
    )
