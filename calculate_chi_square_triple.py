import os
import glob
import subprocess
import numpy as np
import json
import configparser
import importlib
import re
from plotting import extract_label_from_filename, extract_year_from_filename, rgb_to_hex, hsl_to_rgb, generate_combined_gnuplot_script, run_gnuplot
from six_digit_code import genenerate_six_digit_code_pn, genenerate_six_digit_code_p2n, genenerate_six_digit_code_ppn


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

def interpolate_simulation(energy_exp, simulation_data):
    """Linearly interpolation"""
    for i in range(1, len(simulation_data)):
        e1, cs1 = simulation_data[i - 1]
        e2, cs2 = simulation_data[i]
        
        if e1 <= energy_exp <= e2:
            return cs1 + (cs2 - cs1) * (energy_exp - e1) / (e2 - e1)
    return None  # If outside the range of simulation data

def calculate_combined_chi_squared(combined_directory, cleaned_external_files, simulation_data, error_threshold, code):

    chi_squared = 0.0
    dataset_chi_squared_list = []
    valid_datasets = 0.0
    output_file_path = os.path.join(combined_directory, f"chi_squared_values_{code}.txt")
    with open(output_file_path, "w") as output_file:
        output_file.write("#File Name\tChi-Squared Value\n")
        for cleaned_external_file in cleaned_external_files:
            experimental_data = load_experimental_data(cleaned_external_file)  # Load the external file
            valid_points = 0.0
            chi_squared_for_dataset = 0.0  # Initialize chi-squared for this dataset

            print(f"\nProcessing file: {cleaned_external_file}")

            for exp_point in experimental_data:
                try:
                    # Try to unpack assuming exp_point is iterable
                    energy_exp, _, cross_section_exp, delta_cross_exp, _ = exp_point
                except TypeError:
                    print(f"Skipping invalid data point in file {cleaned_external_file}: {exp_point}")
                    continue  # Skip to the next point if unpacking fails
                
                if delta_cross_exp < error_threshold * cross_section_exp:
                    print(f"Skipping data point due to small delta_cross_exp (< {error_threshold * 100}% of cross_section) for energy {energy_exp}")
                    continue

                sim_cross_section = interpolate_simulation(energy_exp, simulation_data)
            
                if sim_cross_section is not None and delta_cross_exp > 0:
                    chi_squared_for_dataset += ((cross_section_exp - sim_cross_section) ** 2) / (delta_cross_exp ** 2)
                    valid_points += 1 # Count this point as valid
                else:
                    print(f"Skipping data point due to invalid delta_cross_exp or no simulation match for energy {energy_exp}")

            if valid_points > 0:
                normalized_chi_squared = chi_squared_for_dataset / valid_points
                chi_squared += normalized_chi_squared
                dataset_chi_squared_list.append(normalized_chi_squared)
                valid_datasets += 1
                output_file.write(f"{cleaned_external_file}\t{normalized_chi_squared:.6f}\n")
                print(f"Valid points for {cleaned_external_file}: {valid_points}")
                print(f"Normalized chi-squared for dataset {cleaned_external_file}: {normalized_chi_squared:.6f}")
            else:
                print(f"No valid points in dataset {cleaned_external_file}, skipping normalization.")

    if valid_datasets > 0:
        chi_squared /=valid_datasets
    print("\nChi-squared values for each dataset:", dataset_chi_squared_list)
    print(f"Number of valid datasets: {valid_datasets}") 
    return chi_squared 

def load_experimental_data(file_path):
    experimental_data = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('#'):
                continue
            # Split the line into components (assuming they are space-separated)
            data = line.split()
            # Convert each component to a float, and make sure there are 5 columns
            if len(data) == 5:
                experimental_data.append([float(val) for val in data])
            else:
                print(f"Invalid data format in file {file_path}: {line.strip()}")
    return experimental_data

def load_simulation_data(file_path):
    return np.loadtxt(file_path, usecols=(0, 1))

def frange(start, stop, step):
    while start <= stop:
        yield start
        start += step

def generate_chi_squared_gnuplot_script(chi2_values, plot_file):
    gnuplot_script = f"""
set terminal pngcairo enhanced font 'Arial,10' size 800,600
set output '{plot_file}'
set title 'Chi-squared vs M2constant'
set xlabel 'M2constant'
set ylabel 'Chi-squared'
set grid
plot '-' using 1:2 with linespoints title 'Chi-squared'
"""
    # Add the m2constant and chi2_values pairs to the script
    for index, chi2_value in enumerate(chi2_values, start=1):
        gnuplot_script += f"{index} {chi2_value}\n"

    gnuplot_script += "e\n"
    
    return gnuplot_script

def generate_combined_chi_squared_gnuplot_script(chi2_value_averages, plot_file):
    gnuplot_script = f"""
set terminal pngcairo enhanced font 'Arial,10' size 800,600
set output '{plot_file}'
set title 'Chi-squared (Average of two data) vs Input file'
set xlabel 'Input file'
set ylabel 'Chi-squared'
set grid
plot '-' using 1:2 with linespoints title 'Chi-squared'
"""
    # Add the m2constant and chi2_values pairs to the script
    for index, chi2_value_average in enumerate(chi2_value_averages, start=1):
        gnuplot_script += f"{index} {chi2_value_average}\n"

    gnuplot_script += "e\n"
    
    return gnuplot_script

def extract_code_from_filename(filename):
    # Get the base name of the file
    base_name = os.path.basename(filename)
    
    # Split by hyphens
    parts = base_name.split('-')
    
    if len(parts) < 4:  # We expect at least four parts for a valid filename
        print(f"Could not extract code from file: {filename} - filename format is unexpected.")
        return None
    
    # Assuming the code is located in the second to last position
    # Check for the expected format in all parts
    for part in parts:
        if re.match(r'^[A-Za-z0-9]{8,9}$', part):
            return part

    print(f"Could not extract code from file: {filename} - no valid code found.")
    return None

# Example usage
filenames = [
    "p-C013-rp007013-Ramstroem-C0070003.1979",
    "p-C013-rp007013-Firouzbakht-T00160021.1991",
    "p-C013-rp007013-Wong-T0015002.1961",
    "p-C013-rp007013-Valentin-C0062005.1965",
    "p-C013-rp007013-Blaser-D0095003.1951",
    "p-C013-rp007013-Gibbons-T0010008.1959",
    "p-C013-rp007013-Kitwanga-O0065003.1989",
    "p-C013-rp007013-Lind-C1912008.1975"
]

for filename in filenames:
    code = extract_code_from_filename(filename)
    if code:
        print(f"Extracted code: {code}")
    else:
        print(f"Failed to extract code from: {filename}")

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
    try:
        with open(json_file_path, 'r') as file:
            content = file.read()
            print("Raw file content:", repr(content))
            userinputs = json.loads(content)
            print("JSON data loaded successfully:", userinputs)
    except FileNotFoundError:
        print("Error: File not found.")
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
    except Exception as e:
        print("An unexpected error occurred:", e)
        

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
        home_directory = os.path.expanduser("~")  
        combined_directory = os.path.join(os.path.expanduser("~"), "Documents", "talys", f"{projectile}-{element}{mass}_chisquared_triple_test")
        os.makedirs(combined_directory, exist_ok=True)
        
        cleaned_external_files = [[] for _ in range(3)]
        cleaned_all_external_files = [[] for _ in range(3)]
        cleaned_output_files = [[] for _ in range(3)]
        chi2_values = [[] for _ in range(3)]
        chi2_value_averages = []
        score_dict_filepath = os.path.join(os.path.expanduser("~"), "Documents", "talys", "score_dict.json")
        config = configparser.ConfigParser()
        config.read('config.ini')

        # Get the error threshold from the configuration file
        error_threshold = float(config['ChiSquaredConfig']['error_threshold'])

        for i, code in enumerate(product_six_digit_codes):
            external_directory = os.path.join(home_directory, "Documents", "exfortables", f"{projectile}", f"{element_capitalized}{formatted_mass}", "residual", code)
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