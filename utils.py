import os
import re
import json

from elem import elemtoz, PARTICLES


def open_json(file):
    if os.path.exists(file):
        with open(file) as json_file:
            # return json.load(json_file)
            try:
                return json.load(json_file)
            except ValueError:
                print(file, ": JSON decording has failed")

    else:
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
        return str(int(mass) - 1)
    elif reaction == "ppn":
        return str(int(mass) - 2)
    elif reaction == "p2n":
        return str(int(mass) - 2)
    else:
        return None


def calc_charge(projectile, outgoing, charge):
    return int(charge) - PARTICLES[projectile][1]


def genenerate_six_digit_code(reaction, element, mass):
    # assuming reaction: only "pn", "ppn", and "p2n" so far
    z = elemtoz(element.capitalize()).zfill(3)
    a = calc_mass(reaction, mass).zfill(3)

    return f"{z}{a}"




# def genenerate_six_digit_code_pn(element, formatted_mass):
#     capitalized_element = element.capitalize()
#     z = elemtoz(capitalized_element)
#     z_modified = f"{int(z) + 1:03}"

#     product_six_digit_code = z_modified + formatted_mass
#     return product_six_digit_code

# def genenerate_six_digit_code_p2n(element, formatted_mass):
#     capitalized_element = element.capitalize()
#     z = elemtoz(capitalized_element)
#     z_modified = f"{int(z) + 1:03}"
#     formatted_mass_modified = f"{int(formatted_mass) - 1:03}"

#     product_six_digit_code = z_modified + formatted_mass_modified
#     return product_six_digit_code


# def genenerate_six_digit_code_ppn(element, formatted_mass):
#     capitalized_element = element.capitalize()
#     z = elemtoz(capitalized_element)
#     formatted_mass_modified = f"{int(formatted_mass) - 1:03}"

#     product_six_digit_code = z + formatted_mass_modified
#     return product_six_digit_code
