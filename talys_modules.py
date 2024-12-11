import os
from subprocess import Popen, PIPE
from glob import glob

from config import TALYS_PATH, N


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
            f.write("fit  y\n")

        print(f"File '{input_file}' created successfully!")


def run_talys(input_file, calc_directory):
    
    p = Popen([os.path.join(TALYS_PATH, "bin/talys")], 
            cwd = calc_directory,  
            stdin=open(input_file),
            stdout=PIPE,
            stderr=PIPE)
    
    stdout, stderr = p.communicate()
    
    with open(os.path.join(calc_directory, 'output.txt'), 'w') as outfile: 
        outfile.write(stderr.decode("utf-8"))
        outfile.write(stdout.decode("utf-8"))

    return 



def search_residual_output(directory, product_six_digit_code):
    # Check if the last character of the six-digit code is a letter
    last_char = product_six_digit_code[-1]
    # Set the pattern based on the letter (if present)
    if last_char == "g":
        pattern = os.path.join(directory, f"rp*{product_six_digit_code[:-1]}*.L00")
    elif last_char == "m":
        pattern = os.path.join(directory, f"rp*{product_six_digit_code[:-1]}*.L*")
    else:
        pattern = os.path.join(directory, f"rp*{product_six_digit_code}*.tot")

    matched_files = glob.glob(pattern)
    return matched_files[0] if matched_files else None


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

    # Assuming the code is located in the second to last position
    # Check for the expected format in all parts
    for part in parts:
        if re.match(r"^[A-Za-z0-9]{8,9}$", part):
            return part

    print(f"Could not extract code from file: {filename} - no valid code found.")
    return None


# def create_projectile_file1(projectile, element, mass, energy, output_file):
#     with open(output_file, 'w') as f:
#         f.write("#\n")
#         f.write(f"#  {projectile}-{element}\n")
#         f.write("#\n")
#         f.write("# General\n")
#         f.write("#\n")
#         f.write(f"projectile {projectile}\n")
#         f.write(f"element {element}\n")
#         f.write(f"mass {mass}\n")
#         f.write(f"energy {energy}\n")
#         f.write("#\n")
#         f.write("# Parameters\n")
#         f.write("#\n")
#         f.write("ldmodel 1\n")
#         f.write("colenhance n\n")
#         f.write("rwdadjust p 1.01244\n")
#         f.write("awdadjust p 0.92997\n")
#         f.write("rvadjust n 0.92437\n")
#         f.write("gadjust 40 90 1.08918\n")
#         f.write("gadjust 40 89 1.16020\n")
#         f.write("gadjust 39 89 0.99689\n")


# def create_projectile_file2(projectile, element, mass, energy, output_file):
#     with open(output_file, 'w') as f:
#         f.write("#\n")
#         f.write(f"#  {projectile}-{element}\n")
#         f.write("#\n")
#         f.write("# General\n")
#         f.write("#\n")
#         f.write(f"projectile {projectile}\n")
#         f.write(f"element {element}\n")
#         f.write(f"mass {mass}\n")
#         f.write(f"energy {energy}\n")
#         f.write("#\n")
#         f.write("# Parameters\n")
#         f.write("#\n")
#         f.write("ldmodel 1\n")
#         f.write("colenhance y\n")
#         f.write("rwdadjust p 0.95307\n")
#         f.write("awdadjust p 0.69077\n")
#         f.write("rvadjust n 0.70940\n")
#         f.write("gadjust 40 90 1.32264\n")
#         f.write("gadjust 40 89 1.94442\n")
#         f.write("gadjust 39 89 0.20806\n")

# def create_projectile_file3(projectile, element, mass, energy, output_file):
#     with open(output_file, 'w') as f:
#         f.write("#\n")
#         f.write(f"#  {projectile}-{element}\n")
#         f.write("#\n")
#         f.write("# General\n")
#         f.write("#\n")
#         f.write(f"projectile {projectile}\n")
#         f.write(f"element {element}\n")
#         f.write(f"mass {mass}\n")
#         f.write(f"energy {energy}\n")
#         f.write("#\n")
#         f.write("# Parameters\n")
#         f.write("#\n")
#         f.write("ldmodel 2\n")
#         f.write("colenhance n\n")
#         f.write("rwdadjust p 0.93951\n")
#         f.write("awdadjust p 0.89624\n")
#         f.write("rvadjust n 0.93520\n")
#         f.write("gadjust 40 90 1.12391\n")
#         f.write("gadjust 40 89 1.22095\n")
#         f.write("gadjust 39 89 0.91306\n")

# def create_projectile_file4(projectile, element, mass, energy, output_file):
#     with open(output_file, 'w') as f:
#         f.write("#\n")
#         f.write(f"#  {projectile}-{element}\n")
#         f.write("#\n")
#         f.write("# General\n")
#         f.write("#\n")
#         f.write(f"projectile {projectile}\n")
#         f.write(f"element {element}\n")
#         f.write(f"mass {mass}\n")
#         f.write(f"energy {energy}\n")
#         f.write("#\n")
#         f.write("# Parameters\n")
#         f.write("#\n")
#         f.write("ldmodel 2\n")
#         f.write("colenhance y\n")
#         f.write("rwdadjust p 0.92715\n")
#         f.write("awdadjust p 0.99703\n")
#         f.write("rvadjust n 0.92399\n")
#         f.write("gadjust 40 90 1.10283\n")
#         f.write("gadjust 40 89 1.07922\n")
#         f.write("gadjust 39 89 1.10589\n")

# def create_projectile_file5(projectile, element, mass, energy, output_file):
#     with open(output_file, 'w') as f:
#         f.write("#\n")
#         f.write(f"#  {projectile}-{element}\n")
#         f.write("#\n")
#         f.write("# General\n")
#         f.write("#\n")
#         f.write(f"projectile {projectile}\n")
#         f.write(f"element {element}\n")
#         f.write(f"mass {mass}\n")
#         f.write(f"energy {energy}\n")
#         f.write("#\n")
#         f.write("# Parameters\n")
#         f.write("#\n")
#         f.write("ldmodel 5\n")
#         f.write("colenhance n\n")
#         f.write("rwdadjust p 0.89916\n")
#         f.write("awdadjust p 0.96301\n")
#         f.write("rvadjust n 0.80958\n")
#         f.write("gadjust 40 90 1.29725\n")
#         f.write("gadjust 40 89 1.69950\n")
#         f.write("gadjust 39 89 0.41586\n")
