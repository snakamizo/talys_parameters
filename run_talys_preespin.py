import os
import glob
import subprocess
import colorsys

def create_projectile_file(projectile, element, mass, energy, constant, output_file):
    with open(output_file, 'w') as f:
        f.write("#\n")
        f.write(f"#  {projectile}-{element}\n")  # Title line
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
        f.write(f"preeqspin {constant}\n")

def clean_data_file(input_file, cleaned_file):
    """Clean the data file by removing extra spaces."""
    with open(input_file, 'r') as infile, open(cleaned_file, 'w') as outfile:
        for line in infile:
            #Remove leading spaces and collapse multiple spaces into one
            cleaned_line = ' '.join(line.split())
            outfile.write(cleaned_line + '\n')

def search_for_specific_output_file(directory, product_six_digit_code):
    """Search for the rp*.tot file that contains the six-digit code in the filename."""
    # Check if the last character of the six-digit code is a letter
    last_char = product_six_digit_code[-1]

    # Set the pattern based on the letter (if present)
    if last_char == 'm':
        pattern = os.path.join(directory, f"rp*{product_six_digit_code[:-1]}*.L02")
    elif last_char == 'g':
        pattern = os.path.join(directory, f"rp*{product_six_digit_code[:-1]}*.L00")
    else:
        pattern = os.path.join(directory, f"rp*{product_six_digit_code}*.tot")  # Default case

    matched_files = glob.glob(pattern)
    return matched_files[0] if matched_files else None

def extract_label_from_filename(filename):
    """Extract the label in the format 'Steyn-D0629010 (2011)' from the filename."""
    base_name = os.path.basename(filename)
    parts = base_name.split('-')
    
    if len(parts) >= 5:
        author = parts[3]
        data = parts[4].split('.')[0]  # Exclude file extension
        year = parts[4].split('.')[1]
        return f"{author}-{data} ({year})"
    return base_name  # Return filename if pattern is unexpected

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
set title 'Cross Section Plot for TALYS and External Data'
set xlabel 'Energy (MeV)'
set ylabel 'Cross Section (mb)'
set grid

plot """
    
    # Add TALYS-generated data files to the plot using different colors
    for i, cleaned_output_file in enumerate(cleaned_output_files):
        label = f"preeqspin {round(1 + i , 4)}"  # Adjusting the label based on preeqspin values
        if i == 0:
            gnuplot_script += f"'{cleaned_output_file}' using 1:2 title '{label}' with lines"
        else:
            gnuplot_script += f", '{cleaned_output_file}' using 1:2 title '{label}' with lines"

    # Add external data files, labeled with their extracted names
    for index, cleaned_external_file in enumerate(cleaned_external_files):
        ext_label = extract_label_from_filename(cleaned_external_file)  # Use formatted label
        point_type = index + 7  # Different point types starting from 7

        # Generate a hue value between 0 and 1, spreading evenly across all external files
        hue = index / len(cleaned_external_files)  # Vary the hue across the rainbow
        saturation = 1  # Full saturation for bright colors
        lightness = 0.5  # Mid lightness for a vibrant look

        # Convert HSL to RGB
        r, g, b = hsl_to_rgb(hue, saturation, lightness)

        color = rgb_to_hex(r, g, b)  # Convert to hex
        gnuplot_script += f", '{cleaned_external_file}' using 1:3:4 with errorbars title '{ext_label}' pt {point_type} lc rgb '{color}'"
    return gnuplot_script

def run_gnuplot(gnuplot_script_content, script_file):
    """Save the GNUplot script to a file and run it."""
    with open(script_file, 'w') as f:
        f.write(gnuplot_script_content)

    #Run the gnuplot script
    result = subprocess.run(["gnuplot", script_file], capture_output=True, text=True)

    if result.returncode != 0:
        print("Gnuplot Error:", result.stderr)
    else:
        print("Gnuplot Output:", result.stdout)


def main():
    # User input
    projectile = input("Enter the projectile: ")
    element = input("Enter the element: ")
    element_caplitalized = element.capitalize()
    mass = int(input("Enter the mass: "))
    formatted_mass = f"{mass:03}"
    energy = input("Enter the energy: ")
    product_six_digit_code = input("Enter the Z&A of product in six digits: ")
    
    # Define the preeqspin
    constants = [round(x, 1) for x in list(frange(1, 4, 1))]

    # Define the combined output directory
    combined_directory = os.path.join(os.path.expanduser("~"), "Documents", "talys", f"{projectile}-{element}{mass}-({product_six_digit_code})_preeqspin")
    os.makedirs(combined_directory, exist_ok=True)
    
    # To store all the data files for plotting
    cleaned_output_files = []
    
    for constant in constants:
        # Create a unique directory for each M2constant
        home_directory = os.path.expanduser("~") 
        new_directory = os.path.join(combined_directory, f"{projectile}-{element}{mass}_preeqspin_{constant}")
        os.makedirs(new_directory, exist_ok=True)

        #Specify the output file name in the new directory
        output_file = os.path.join(new_directory, f"talys.inp") 

        # Create the file with the specified parameters
        create_projectile_file(projectile, element, mass, energy, constant, output_file)
    
        print(f"File '{output_file}' created successfully!")

        # Run the bash script with the output file as an argument
        bash_script = os.path.expanduser("~/Documents/run_talys.sh")
        subprocess.run([bash_script, output_file])

        # Step 1: Search for the "rp*.tot" file that contains the six-digit code
        data_file = search_for_specific_output_file(new_directory, product_six_digit_code)
        if not data_file:
            print(f"No 'rp*' files found for preeqspin {constant}.")
            continue


        # Clean the data file
        cleaned_output_file = os.path.join(new_directory, f"cleaned_{os.path.basename(data_file)}")
        clean_data_file(data_file, cleaned_output_file)

        # Collect the cleaned file for final plot
        cleaned_output_files.append(cleaned_output_file)

    # Step 3: Retrieve external data files from the specified directory
    external_directory = os.path.join(home_directory, "Documents", "exfortables", f"{projectile}", f"{element_caplitalized}"f"{formatted_mass}", "residual", product_six_digit_code)
    external_files = [f for f in glob.glob(os.path.join(external_directory, "*")) if not f.endswith('.list')] 

    if not external_files:
        print(f"No external data files found in the directory: {external_directory}")
        return
    
    # Clean external data files and store in cleaned_files_external
    cleaned_external_files = []
    for ext_file in external_files:
        cleaned_external_file = os.path.join(combined_directory, f"cleaned_{os.path.basename(ext_file)}")
        clean_data_file(ext_file, cleaned_external_file)
        cleaned_external_files.append(cleaned_external_file)
    print(f"Found {len(external_files)} external data files for plotting.")

    
    # Specify the output plot file
    plot_file = os.path.join(combined_directory, f"combined_cross_section_plot_{product_six_digit_code}.png")

    # Step 2: Generate the GNUplot script for the specific file
    gnuplot_script = generate_combined_gnuplot_script(cleaned_output_files, cleaned_external_files, plot_file)
   
    # Specify the location of the temporary gnuplot script file
    gnuplot_script_file = os.path.join(combined_directory, "gnuplot_combined_script.gp")

    # Step 3: Run the gnuplot script to display the plot
    run_gnuplot(gnuplot_script, gnuplot_script_file)

    print(f"Combined plot generated: {plot_file}")

def frange(start, stop, step):
    """Helper function to generate float ranges."""
    while start <= stop:
        yield start
        start += step
   

if __name__ == "__main__":
    main()