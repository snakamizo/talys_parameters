import os
import glob
import subprocess
import colorsys
import numpy as np

def create_projectile_file(projectile, element, mass, energy, m2constant, output_file):
    with open(output_file, 'w') as f:
        f.write("#\n")
        f.write(f"#  {projectile}-{element}\n")
        f.write("#\n")
        f.write("# General\n")
        f.write("#\n")
        f.write(f"projectile {projectile}\n")
        f.write(f"element {element}\n")
        f.write(f"mass {mass}\n")
        f.write(f"energy {energy}\n")
        f.write("#\n")
        f.write("# Parameters\n")
        f.write("#\n")
        f.write("Maxlevelsres 20\n")
        f.write(f"m2constant {m2constant}\n")
        f.write("ldmodel 1\n")
        f.write("colenhance n\n")
        f.write("strength 9\n")
        f.write("fismodel 5\n")
        f.write("alphaomp 6\n")
        f.write("rwdadjust p 1.01244\n")
        f.write("awdadjust p 0.92997\n")
        f.write("rvadjust n 0.92437\n")
        f.write("gadjust 40 90 1.08918\n")
        f.write("gadjust 40 89 1.16020\n")
        f.write("gadjust 39 89 0.99689\n")

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

def extract_label_from_filename(filename):
    base_name = os.path.basename(filename)
    parts = base_name.split('-')
    
    if len(parts) >= 5:
        author = parts[3]
        data = parts[4].split('.')[0]  # Exclude file extension
        year = parts[4].split('.')[1]
        return f"{author}-{data} ({year})"
    return base_name   # Return filename if pattern is unexpected

def rgb_to_hex(r, g, b):
    return f'#{r:02X}{g:02X}{b:02X}' 

def hsl_to_rgb(h, s, l):
    """Convert HSL color to RGB."""
    rgb_float = colorsys.hls_to_rgb(h, l, s)
    return tuple(int(255 * x) for x in rgb_float)  # Convert float [0, 1] to int [0, 255]

def generate_combined_gnuplot_script(cleaned_output_files, cleaned_external_files, plot_file):

    gnuplot_script = f"""
set terminal pngcairo enhanced font 'Arial,10' size 800,600
set output '{plot_file}'
set title 'Cross Section Plot'
set xlabel 'Energy (MeV)'
set ylabel 'Cross Section (mb)'
set grid
set xrange [0:40]

plot """
    # Add TALYS-generated data files
    for i, cleaned_output_file in enumerate(cleaned_output_files):
        label = f"m2constant {round(0.2 + i*0.2 , 1)}"  # Adjusting the label based on preeqspin values
        if i == 0:
            gnuplot_script += f"'{cleaned_output_file}' using 1:2 title '{label}' with lines"
        else:
            gnuplot_script += f", '{cleaned_output_file}' using 1:2 title '{label}' with lines"

    # Add external data files
    for index, cleaned_external_file in enumerate(cleaned_external_files):
        ext_label = extract_label_from_filename(cleaned_external_file)  
        point_type = index + 7  

        hue = index / len(cleaned_external_files)  
        saturation = 1  
        lightness = 0.5

        r, g, b = hsl_to_rgb(hue, saturation, lightness)

        color = rgb_to_hex(r, g, b) 
        gnuplot_script += f", '{cleaned_external_file}' using 1:3:4 with errorbars title '{ext_label}' pt {point_type} lc rgb '{color}'"
    
    
    return gnuplot_script

def run_gnuplot(gnuplot_script_content, script_file):

    with open(script_file, 'w') as f:
        f.write(gnuplot_script_content)

    result = subprocess.run(["gnuplot", script_file], capture_output=True, text=True)

    if result.returncode != 0:
        print("Gnuplot Error:", result.stderr)
    else:
        print("Gnuplot Output:", result.stdout)

def interpolate_simulation(energy_exp, simulation_data):
    """Linearly interpolation"""
    for i in range(1, len(simulation_data)):
        e1, cs1 = simulation_data[i - 1]
        e2, cs2 = simulation_data[i]
        
        if e1 <= energy_exp <= e2:
            return cs1 + (cs2 - cs1) * (energy_exp - e1) / (e2 - e1)
    return None  # If outside the range of simulation data

def calculate_combined_chi_squared(cleaned_external_files, simulation_data):
    
    # Print the experimental data to debug the structure
    #print("Experimental Data:", experimental_data)
    #print("Experimental Data Shape:", experimental_data.shape)

    chi_squared = 0.0
    dataset_chi_squared_list = []
    valid_datasets = 0.0
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

def generate_chi_squared_gnuplot_script(m2constants, chi2_values, plot_file):
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
    for m2constant, chi2_value in zip(m2constants, chi2_values):
        gnuplot_script += f"{m2constant} {chi2_value}\n"

    gnuplot_script += "e\n"
    
    return gnuplot_script

def generate_combined_chi_squared_gnuplot_script(m2constants, chi2_value_averages, plot_file):
    gnuplot_script = f"""
set terminal pngcairo enhanced font 'Arial,10' size 800,600
set output '{plot_file}'
set title 'Chi-squared (Average of two data) vs M2constant'
set xlabel 'M2constant'
set ylabel 'Chi-squared'
set grid
plot '-' using 1:2 with linespoints title 'Chi-squared'
"""
    # Add the m2constant and chi2_values pairs to the script
    for m2constant, chi2_value_average in zip(m2constants, chi2_value_averages):
        gnuplot_script += f"{m2constant} {chi2_value_average}\n"

    gnuplot_script += "e\n"
    
    return gnuplot_script

def retrieve_external_data(external_directory, combined_directory, cleaned_external_files):
    
    all_external_files = [f for f in glob.glob(os.path.join(external_directory, "*")) if not f.endswith('.list')] 

    if not all_external_files:
        print(f"No external data files found in the directory: {external_directory}")
        return

    # Ask the user whether to include each external file
    external_files = []
    for ext_file in all_external_files:
        include_file = input(f"Do you want to include the file '{os.path.basename(ext_file)}'? (y/n): ").strip().lower()
        if include_file == 'y':
            external_files.append(ext_file)

    # Check if we have any files left after exclusions
    if not external_files:
        print("No external data files selected.")
        return

    for ext_file in external_files:
        cleaned_external_file = os.path.join(combined_directory, f"cleaned_{os.path.basename(ext_file)}")
        clean_data_file(ext_file, cleaned_external_file)
        cleaned_external_files.append(cleaned_external_file)

    print(f"Found {len(external_files)} external data files for plotting.")



def main():
    projectile = input("Enter the projectile: ")
    element = input("Enter the element: ")
    element_capitalized = element.capitalize()
    mass = int(input("Enter the mass: "))
    formatted_mass = f"{mass:03}"
    energy = input("Enter the energy: ")
    product_six_digit_code1 = input("Enter the Z&A of product1 in six digits: ")
    product_six_digit_code2 = input("Enter the Z&A of product2 in six digits: ")
    m2constants = [round(x,1) for x in list(frange(0.2, 1, 0.2))]

    # Define the combined output directory
    home_directory = os.path.expanduser("~")  
    combined_directory = os.path.join(os.path.expanduser("~"), "Documents", "talys", f"{projectile}-{element}{mass}_chisquared_double_ex3")
    os.makedirs(combined_directory, exist_ok=True)
    
    cleaned_external_files1 = []
    cleaned_external_files2 = []
    external_directory1 = os.path.join(home_directory, "Documents", "exfortables", f"{projectile}", f"{element_capitalized}"f"{formatted_mass}", "residual", product_six_digit_code1)
    external_directory2 = os.path.join(home_directory, "Documents", "exfortables", f"{projectile}", f"{element_capitalized}"f"{formatted_mass}", "residual", product_six_digit_code2)

    retrieve_external_data(external_directory1, combined_directory, cleaned_external_files1)
    retrieve_external_data(external_directory2, combined_directory, cleaned_external_files2)

    cleaned_output_files1 = []
    cleaned_output_files2 = []
    
    chi2_values1 = []
    chi2_values2 = []
    chi2_value_averages = []
    
    for m2constant in m2constants:
        # Define the directory structure 
        new_directory = os.path.join(combined_directory, f"{projectile}-{element}{mass}_chisquared_{m2constant}")

        #Create the new directory (including all parent directory
        os.makedirs(new_directory, exist_ok=True)

        #Specify the output file name in the new directory
        output_file = os.path.join(new_directory, f"talys.inp") 

        # Create the file with the specified parameters
        create_projectile_file(projectile, element, mass, energy, m2constant, output_file)
        print(f"File '{output_file}' created successfully!")

        # Run the bash script
        bash_script = os.path.expanduser("~/Documents/run_talys.sh")
        subprocess.run([bash_script, output_file])

        # Search for the "rp*" file that contains the six-digit code
        data_file1 = search_for_specific_output_file(new_directory, product_six_digit_code1)
        if not data_file1:
            print(f"No 'rp*' files found with the six-digits '{product_six_digit_code1}' in the directory.")
            return
        data_file2 = search_for_specific_output_file(new_directory, product_six_digit_code2)
        if not data_file2:
            print(f"No 'rp*' files found with the six-digits '{product_six_digit_code2}' in the directory.")
            return

        cleaned_output_file1 = os.path.join(new_directory, f"cleaned_{os.path.basename(data_file1)}")
        clean_data_file(data_file1, cleaned_output_file1)
        cleaned_output_files1.append(cleaned_output_file1)

        cleaned_output_file2 = os.path.join(new_directory, f"cleaned_{os.path.basename(data_file2)}")
        clean_data_file(data_file2, cleaned_output_file2)
        cleaned_output_files2.append(cleaned_output_file2)

        simulation_data1 = load_simulation_data(cleaned_output_file1)  # Load the cleaned .tot file
        combined_chi_squared1 = calculate_combined_chi_squared(cleaned_external_files1, simulation_data1)
        chi2_values1.append(combined_chi_squared1)

        simulation_data2 = load_simulation_data(cleaned_output_file2)  # Load the cleaned .tot file
        combined_chi_squared2 = calculate_combined_chi_squared(cleaned_external_files2, simulation_data2)
        chi2_values2.append(combined_chi_squared2)

        chi2_value_average = (combined_chi_squared1 + combined_chi_squared2) / 2.0
        chi2_value_averages.append(chi2_value_average)
    
    # Plot xs of TALYS calculation and experimental data
    plot_file = os.path.join(combined_directory, f"combined_cross_section_plot_{product_six_digit_code1}.png")
    gnuplot_script1 = generate_combined_gnuplot_script(cleaned_output_files1, cleaned_external_files1, plot_file)
    gnuplot_script_file1 = os.path.join(combined_directory, f"combined_cross_section_plot_{product_six_digit_code1}.gp")
    run_gnuplot(gnuplot_script1, gnuplot_script_file1)

    plot_file = os.path.join(combined_directory, f"combined_cross_section_plot_{product_six_digit_code2}.png")
    gnuplot_script2 = generate_combined_gnuplot_script(cleaned_output_files2, cleaned_external_files2, plot_file)
    gnuplot_script_file2 = os.path.join(combined_directory, f"combined_cross_section_plot_{product_six_digit_code2}.gp")
    run_gnuplot(gnuplot_script2, gnuplot_script_file2)

    # Plot chi-squared vs m2constant
    chi_squared_plot_file = os.path.join(combined_directory, f"chi_squared_vs_m2constant_{product_six_digit_code1}.png")
    gnuplot_script2 = generate_chi_squared_gnuplot_script(m2constants, chi2_values1, chi_squared_plot_file)
    gnuplot_script_file2 = os.path.join(combined_directory, "chi_squared_vs_m2constant.gp")
    run_gnuplot(gnuplot_script2, gnuplot_script_file2)   

    chi_squared_plot_file = os.path.join(combined_directory, f"chi_squared_vs_m2constant_{product_six_digit_code2}.png")
    gnuplot_script2 = generate_chi_squared_gnuplot_script(m2constants, chi2_values2, chi_squared_plot_file)
    gnuplot_script_file2 = os.path.join(combined_directory, "chi_squared_vs_m2constant.gp")
    run_gnuplot(gnuplot_script2, gnuplot_script_file2) 

    chi_squared_combined_plot_file = os.path.join(combined_directory, f"chi_squared_average_vs_m2constant_{product_six_digit_code2}.png")
    gnuplot_script3 =generate_combined_chi_squared_gnuplot_script(m2constants, chi2_value_averages, chi_squared_combined_plot_file)
    gnuplot_script_file3 = os.path.join(combined_directory, "chi_squared_average_vs_m2constant.gp")
    run_gnuplot(gnuplot_script3, gnuplot_script_file3) 
  

if __name__ == "__main__":
    main()