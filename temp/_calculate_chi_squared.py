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
        f.write(f"m2constant {m2constant}\n")

def clean_data_file(input_file, cleaned_file):
    with open(input_file, 'r') as infile, open(cleaned_file, 'w') as outfile:
        for line in infile:
            cleaned_line = ' '.join(line.split())
            outfile.write(cleaned_line + '\n')

def search_for_specific_output_file(directory, product_six_digit_code):
    # Check if the last character of the six-digit code is a letter
    last_char = product_six_digit_code[-1]
    # Set the pattern based on the letter (if present)
    if last_char == 'm':
        pattern = os.path.join(directory, f"rp*{product_six_digit_code[:-1]}*.L02")
    elif last_char == 'g':
        pattern = os.path.join(directory, f"rp*{product_six_digit_code[:-1]}*.L00")
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
    """Generate a GNUplot script to plot the data."""
    gnuplot_script = f"""
set terminal pngcairo enhanced font 'Arial,10' size 800,600
set output '{plot_file}'
set title 'Cross Section Plot'
set xlabel 'Energy (MeV)'
set ylabel 'Cross Section (mb)'
set grid

set xrange [0:30]

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
    """Save the GNUplot script to a file and run it."""
    with open(script_file, 'w') as f:
        f.write(gnuplot_script_content)

    result = subprocess.run(["gnuplot", script_file], capture_output=True, text=True)

    if result.returncode != 0:
        print("Gnuplot Error:", result.stderr)
    else:
        print("Gnuplot Output:", result.stdout)

def interpolate_simulation(energy_exp, simulation_data):
    """Linearly interpolate the simulated cross section at experimental energy."""
    for i in range(1, len(simulation_data)):
        e1, cs1 = simulation_data[i - 1]
        e2, cs2 = simulation_data[i]
        
        if e1 <= energy_exp <= e2:
            # Linear interpolation
            return cs1 + (cs2 - cs1) * (energy_exp - e1) / (e2 - e1)
    return None  # If outside the range of simulation data

def calculate_chi_squared(exp_data, sim_data, chi_squared):
    """Calculate chi-squared between experimental and simulated data."""
    
    # Print the experimental data to debug the structure
    print("Experimental Data:", exp_data)
    print("Experimental Data Shape:", exp_data.shape)

    for exp_point in exp_data:
        try:
            # Try to unpack assuming exp_point is iterable
            energy_exp, _, cross_section_exp, delta_cross_exp, _ = exp_point
        except TypeError:
            print(f"Skipping invalid data point: {exp_point}")
            continue  # Skip to the next point if unpacking fails
        
        sim_cross_section = interpolate_simulation(energy_exp, sim_data)
            
        if sim_cross_section is not None and delta_cross_exp > 0:
            chi_squared += ((cross_section_exp - sim_cross_section) ** 2) / (delta_cross_exp ** 2)
    
    return chi_squared

def load_experimental_data(file_path):
    """Load experimental data from file."""
    return np.loadtxt(file_path, usecols=(0, 1, 2, 3, 4))

def load_simulation_data(file_path):
    """Load simulation data from file."""
    return np.loadtxt(file_path, usecols=(0, 1))

def frange(start, stop, step):
    """Helper function to generate float ranges."""
    while start <= stop:
        yield start
        start += step

def generate_chi_squared_gnuplot_script(m2constants, chi2_values, plot_file):
    """Generate a GNUplot script to plot chi-squared values."""
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

def main():
    projectile = input("Enter the projectile: ")
    element = input("Enter the element: ")
    element_capitalized = element.capitalize()
    mass = int(input("Enter the mass: "))
    formatted_mass = f"{mass:03}"
    energy = input("Enter the energy: ")
    product_six_digit_code = input("Enter the Z&A of product in six digits: ")
    m2constants = [round(x,1) for x in list(frange(0.2, 1, 0.2))]

    # Define the combined output directory
    home_directory = os.path.expanduser("~")  
    combined_directory = os.path.join(os.path.expanduser("~"), "Documents", "talys", f"{projectile}-{element}{mass}-({product_six_digit_code})_chisquared")
    os.makedirs(combined_directory, exist_ok=True)
    
    # Retrieve external data files
    external_directory = os.path.join(home_directory, "Documents", "exfortables", f"{projectile}", f"{element_capitalized}"f"{formatted_mass}", "residual", product_six_digit_code)
    external_files = [f for f in glob.glob(os.path.join(external_directory, "*")) if not f.endswith('.list')] 

    if not external_files:
        print(f"No external data files found in the directory: {external_directory}")
        return
    
    cleaned_external_files = []
    for ext_file in external_files:
        cleaned_external_file = os.path.join(combined_directory, f"cleaned_{os.path.basename(ext_file)}")
        clean_data_file(ext_file, cleaned_external_file)
        cleaned_external_files.append(cleaned_external_file)

    print(f"Found {len(external_files)} external data files for plotting.")

    cleaned_output_files = []
    
    chi2_values = []
    
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
        data_file = search_for_specific_output_file(new_directory, product_six_digit_code)
        if not data_file:
            print(f"No 'rp*' files found with the six-digits '{product_six_digit_code}' in the directory.")
            return

        cleaned_output_file = os.path.join(new_directory, f"cleaned_{os.path.basename(data_file)}")
        clean_data_file(data_file, cleaned_output_file)
        cleaned_output_files.append(cleaned_output_file)

        chi_squared = 0.0

        simulation_data = load_simulation_data(cleaned_output_file)  # Load the cleaned .tot file
        for j, cleaned_external_file in enumerate(cleaned_external_files):
            experimental_data = load_experimental_data(cleaned_external_files[j])  # Load the first external file as an example
            chi2_value = calculate_chi_squared(experimental_data, simulation_data, chi_squared)
            chi2_values.append(chi2_value)
    
    
    # Plot xs of TALYS calculation and experimental data
    plot_file = os.path.join(combined_directory, f"combined_cross_section_plot_{product_six_digit_code}.png")
    gnuplot_script1 = generate_combined_gnuplot_script(cleaned_output_files, cleaned_external_files, plot_file)
    gnuplot_script_file1 = os.path.join(combined_directory, f"combined_cross_section_plot_{product_six_digit_code}.gp")
    run_gnuplot(gnuplot_script1, gnuplot_script_file1)

    # Plot chi-squared vs m2constant
    chi_squared_plot_file = os.path.join(combined_directory, "chi_squared_vs_m2constant.png")
    gnuplot_script2 = generate_chi_squared_gnuplot_script(m2constants, chi2_values, chi_squared_plot_file)
    gnuplot_script_file2 = os.path.join(combined_directory, "chi_squared_vs_m2constant.gp")
    run_gnuplot(gnuplot_script2, gnuplot_script_file2)    

if __name__ == "__main__":
    main()