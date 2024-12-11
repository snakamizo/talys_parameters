import os
import glob
import subprocess
import numpy as np
import json
import configparser
import importlib
import re
from config import CALC_PATH, EXFORTABLES_PATH, ERROR_TRHRESHOLD
from plotting import extract_year_from_filename, generate_combined_gnuplot_script, run_gnuplot, generate_chi_squared_gnuplot_script, generate_combined_chi_squared_gnuplot_script
from six_digit_code import genenerate_six_digit_code_pn, genenerate_six_digit_code_p2n, genenerate_six_digit_code_ppn
from check_directory import check_directory_before_run
from calculate_chi_square_total._chi_square_calculation import calculate_combined_chi_squared

def clean_data_file(input_file, cleaned_file):
    with open(input_file, 'r') as infile, open(cleaned_file, 'w') as outfile:
        for line in infile:
            cleaned_line = ' '.join(line.split())
            outfile.write(cleaned_line + '\n')

def search_for_specific_output_file(directory, product_six_digit_code):
    # Check if the last character of the six-digit code is a letter
    last_char = product_six_digit_code[-1]
    # Set the pattern based on the letter (if present)
    if last_char == 'g':
        pattern = os.path.join(directory, f"rp*{product_six_digit_code[:-1]}*.L00")
    elif last_char == 'm':
        pattern = os.path.join(directory, f"rp*{product_six_digit_code[:-1]}*.L*")
    else:
        pattern = os.path.join(directory, f"rp*{product_six_digit_code}*.tot")  

    matched_files = glob.glob(pattern)
    return matched_files[0] if matched_files else None


def load_simulation_data(file_path):
    return np.loadtxt(file_path, usecols=(0, 1))

def extract_code_from_filename(filename):
    # Get the base name of the file
    base_name = os.path.basename(filename)
    
    # Split by hyphens
    parts = base_name.split('-')
    
    # Ensure we have enough parts
    if len(parts) < 4:  # We expect at least four parts for a valid filename
        print(f"Could not extract code from file: {filename} - filename format is unexpected.")
        return None
    
    # Get the last part, which may contain the code
    last_part = parts[-1]
    
    # Remove any file extensions (if present)
    last_part = last_part.split('.')[0]  # Take the part before the first dot
    
    # Check if the last part is a valid code (8 or 9 alphanumeric characters)
    if re.match(r'^[A-Za-z0-9]{8,9}$', last_part):
        return last_part
    
    print(f"Could not extract code from file: {filename} - last part '{last_part}' is not valid.")
    return None

def load_score_dict(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            score_dict = json.load(f)
        print(f"Score dictionary loaded from {filepath}")
        return score_dict
    else:
        print(f"Score dictionary file not found at {filepath}")
        return {}

def retrieve_external_data(external_directory, combined_directory, cleaned_external_files, cleaned_all_external_files, product_six_digit_code, score_dict_filepath):
    
    all_external_files = [f for f in glob.glob(os.path.join(external_directory, "*")) if not f.endswith('.list')] 

    if not all_external_files:
        print(f"No external data files found in the directory: {external_directory}")
        return

    score_dict = load_score_dict(score_dict_filepath)

    # Ask the user whether to include each external file
    external_files = []
    for ext_file in all_external_files:
        file_code = extract_code_from_filename(ext_file)
        if not file_code:
            print(f"Could not extract code from file: {ext_file}")
            continue

        if file_code in score_dict:
            if score_dict[file_code] == 1:
                external_files.append(ext_file)
        else:
            print(f"Code '{file_code}' not found in score dict, skipping file '{os.path.basename(ext_file)}'")
    if not external_files:
        print("No external data files selected based on score_dict.")
        return

    cleaned_all_external_directory = os.path.join(combined_directory, f"cleaned_all_external_data{product_six_digit_code}")
    os.makedirs(cleaned_all_external_directory, exist_ok=True)
    cleaned_external_directory = os.path.join(combined_directory, f"cleaned_external_data{product_six_digit_code}")
    os.makedirs(cleaned_external_directory, exist_ok=True)

    # Check if we have any files left after exclusions
    if not external_files:
        print("No external data files selected.")
        return
    ext_files = sorted(external_files, key=extract_year_from_filename)
    for ext_file in ext_files:
        cleaned_external_file = os.path.join(cleaned_all_external_directory, f"cleaned_{os.path.basename(ext_file)}")
        clean_data_file(ext_file, cleaned_external_file)
        cleaned_external_files.append(cleaned_external_file)

    sorted_all_external_files = sorted(all_external_files, key=extract_year_from_filename)

    for sorted_all_external_file in sorted_all_external_files:
        cleaned_all_external_file = os.path.join(cleaned_external_directory, f"cleaned_{os.path.basename(sorted_all_external_file)}")
        clean_data_file(sorted_all_external_file, cleaned_all_external_file)
        cleaned_all_external_files.append(cleaned_all_external_file)

    print(f"Found {len(external_files)} external data files for plotting.")

def main():
    json_file_path = os.path.join(os.path.expanduser("~"), "Documents", "calculate_chi_square_total", "userinput.json")
    userinputs = check_directory_before_run(json_file_path)

    for userinput in userinputs:
        projectile = userinput["projectile"]
        element = userinput["element"]
        element_capitalized = element.capitalize()
        mass = int(userinput["mass"])
        formatted_mass = f"{mass:03}"
        energy = userinput["energy"]
        product_six_digit_codes = [
            genenerate_six_digit_code_pn(element, formatted_mass), 
            genenerate_six_digit_code_p2n(element, formatted_mass), 
            genenerate_six_digit_code_ppn(element, formatted_mass)
        ]
        try:
            create_module = importlib.import_module(f'create_projectile_files_{element}')
        except ModuleNotFoundError:
            print(f"Module for element '{element}' not found. Skipping.")
            continue

        # Define the combined output directory
        combined_directory = os.path.join(CALC_PATH, f"{projectile}-{element}{mass}_chisquared_triple_test")
        os.makedirs(combined_directory, exist_ok=True)
        
        cleaned_external_files = [[] for _ in range(3)]
        cleaned_all_external_files = [[] for _ in range(3)]
        cleaned_output_files = [[] for _ in range(3)]
        chi2_values = [[] for _ in range(3)]
        chi2_value_averages = []
        score_dict_filepath = os.path.join(os.path.expanduser("~"), "Documents", "talys", "score_dict.json")
        config = configparser.ConfigParser()
        config.read('config.ini')
        error_threshold = float(config['ChiSquaredConfig']['error_threshold'])

        for i, code in enumerate(product_six_digit_codes):
            external_directory = os.path.join(EXFORTABLES_PATH, f"{projectile}", f"{element_capitalized}{formatted_mass}", "residual", code)
            retrieve_external_data(external_directory, combined_directory, cleaned_external_files[i], cleaned_all_external_files[i], code, score_dict_filepath)
        
        for i in range(1, 6):  # Loop through 1 to 5
            function_name = f"create_projectile_file{i}" 
            function_to_call = getattr(create_module, function_name, None)

            if function_to_call is None:
                print(f"Function '{function_name}' not found in module for element '{element}'. Skipping.")
                continue

            # Create and run the projectile file
            new_directory = os.path.join(combined_directory, f"{projectile}-{element}{mass}_chisquared_{i}")
            os.makedirs(new_directory, exist_ok=True)

            # Create and run the projectile file 
            output_file = os.path.join(new_directory, f"talys.inp") 
            function_to_call(projectile, element, mass, energy, output_file)
            print(f"File '{output_file}' created successfully!")
            subprocess.run([os.path.expanduser("~/Documents/run_talys.sh"), output_file])

            # Search for and clean data files for each six-digit code
            for j, code in enumerate(product_six_digit_codes):
                data_file = search_for_specific_output_file(new_directory, code)
                if not data_file:
                    print(f"No 'rp*' files found with the six-digits '{code}' in the directory.")
                    continue
                cleaned_output_file = os.path.join(new_directory, f"cleaned_{os.path.basename(data_file)}")
                clean_data_file(data_file, cleaned_output_file)
                cleaned_output_files[j].append(cleaned_output_file)

                simulation_data = load_simulation_data(cleaned_output_file)
                combined_chi_squared = calculate_combined_chi_squared(combined_directory, cleaned_external_files[j], simulation_data, error_threshold, code)
                chi2_values[j].append(combined_chi_squared)

            chi2_value_average = sum(chi2_values[j][-1] for j in range(3)) / 3.0
            chi2_value_averages.append(chi2_value_average)
        
        # Plot xs of TALYS calculation and experimental data
        for j, code in enumerate(product_six_digit_codes):
            plot_file = os.path.join(combined_directory, f"combined_cross_section_plot_{code}.png")
            gnuplot_script = generate_combined_gnuplot_script(cleaned_output_files[j], cleaned_external_files[j], cleaned_all_external_files[j], plot_file)
            gnuplot_script_file = os.path.join(combined_directory, f"combined_cross_section_plot_{code}.gp")
            run_gnuplot(gnuplot_script, gnuplot_script_file)
        
        # Plot chi-squared vs m2constant
        for j, code in enumerate(product_six_digit_codes):
            chi_squared_plot_file = os.path.join(combined_directory, f"chi_squared_vs_input_{code}.png")
            gnuplot_script = generate_chi_squared_gnuplot_script(chi2_values[j], chi_squared_plot_file)
            gnuplot_script_file = os.path.join(combined_directory, f"chi_squared_vs_input_{j+1}.gp")
            run_gnuplot(gnuplot_script, gnuplot_script_file)
        
        chi_squared_combined_plot_file = os.path.join(combined_directory, f"chi_squared_average_vs_input.png")
        gnuplot_script3 =generate_combined_chi_squared_gnuplot_script(chi2_value_averages, chi_squared_combined_plot_file)
        gnuplot_script_file3 = os.path.join(combined_directory, "chi_squared_average_vs_input.gp")
        run_gnuplot(gnuplot_script3, gnuplot_script_file3) 
    

if __name__ == "__main__":
    main()