import os
import glob
import subprocess # Import subprocess to call bash script

def create_projectile_file(projectile, element, mass, energy, output_file):
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
        #f.write("#\n")
        #f.write("# Parameters\n")
        #f.write("#\n")
        #f.write(f"M2constant {constant}\n")

def clean_data_file(input_file, cleaned_file):
    """Clean the data file by removing extra spaces."""
    with open(input_file, 'r') as infile, open(cleaned_file, 'w') as outfile:
        for line in infile:
            #Remove leading spaces and collapse multiple spaces into one
            cleaned_line = ' '.join(line.split())
            outfile.write(cleaned_line + '\n')

def search_for_specific_output_files(directory, product_six_digit_code):
    """Search for the rp*.tot file that contains the six-digit code in the filename."""
    pattern = os.path.join(directory, f"rp*{product_six_digit_code}*.tot")
    return glob.glob(pattern)

def extract_label_from_filename(filename):
    """Extract the label in the format 'Steyn-D0629010 (2011)' from the filename."""
    base_name = os.path.basename(filename)
    parts = base_name.split('-')
    
    if len(parts) >= 5:
        author = parts[3]
        data = parts[4].split('.')[0]  # Exclude file extension
        year = parts[4].split('.')[1]
        return f"{author}-{data} ({year})"
    return base_name   # Return filename if pattern is unexpected

def generate_combined_gnuplot_script(data_files, external_files, talys_output_file, plot_file):
    """Generate a GNUplot script to plot the data."""
    gnuplot_script = f"""
set terminal pngcairo enhanced font 'Arial,10' size 800,600
set output '{plot_file}'
set title 'Cross Section Plot'
set xlabel 'Energy (MeV)'
set ylabel 'Cross Section (mb)'
set grid
"""
    # Add each TALYS-generated data file to the plot using different colors
    plot_lines = []
    for data_file in data_files:
        plot_lines.append(f"'{data_file}' using 1:2 title '{os.path.basename(data_file)}' with lines")

    # Add external data files, labeled with their extracted names
    for index, ext_file in enumerate(external_files):
        ext_label = extract_label_from_filename(ext_file)  # Use formatted label
        point_type = index + 7  # Different point types starting from 7
        # Properly format the RGB color
        r = (index * 40) % 256
        g = 255
        b = (255 - index * 40) % 256
        color = f"rgb '{r},{g},{b}'"  # Ensure valid RGB format
        plot_lines.append(f"'{ext_file}' using 1:3:4 with errorbars title '{ext_label}' pt {point_type} lc {color}")

    # Add TALYS output to the plot if it exists
    if talys_output_file:
        plot_lines.append(f"'{talys_output_file}' using 1:2 title 'TALYS Output' with linespoints lw 2 lc rgb 'red'")
    
    gnuplot_script += "plot " + ", ".join(plot_lines) + "\n"
    return gnuplot_script


def run_gnuplot(gnuplot_script_content, script_file):
    """Save the GNUplot script to a file and run it."""
    with open(script_file, 'w') as f:
        f.write(gnuplot_script_content)

    #Run the gnuplot script
    subprocess.run(["gnuplot", script_file])


def main():
    # User input
    projectile = input("Enter the projectile: ")
    element = input("Enter the element: ")
    element_caplitalized = element.capitalize()
    mass = int(input("Enter the mass: "))
    formatted_mass = f"{mass:03}"
    energy = input("Enter the energy: ")
    product_six_digit_code = input("Enter the Z&A of product in six digits: ")
    #constant = input("Enter the M2 constant: ")
    
    # Define the directory structure using the home directory
    home_directory = os.path.expanduser("~")  # Get the current user's home directory
    new_directory = os.path.join(home_directory, "Documents", "talys", f"{projectile}-{element}{mass}_plotdata2")

    #Create the new directory (including all parent directory
    os.makedirs(new_directory, exist_ok=True)

    #Specify the output file name in the new directory
    output_file = os.path.join(new_directory, f"talys.inp") 

    # Create the file with the specified parameters
    create_projectile_file(projectile, element, mass, energy, output_file)
    
    print(f"File '{output_file}' created successfully!")

    # Run the bash script with the output file as an argument
    bash_script = os.path.expanduser("~/Documents/run_talys.sh")
    subprocess.run([bash_script, output_file])

    # Step 1: Search for the "rp*.tot" file that contains the six-digit code
    data_files = search_for_specific_output_files(new_directory, product_six_digit_code)

    if not data_files:
        print(f"No 'rp*.tot' files found with the six-digits '{product_six_digit_code}' in the directory.")
        return

    # Step 2: Clean each data file and store them in a list for plotting
    cleaned_files = []
    for data_file in data_files:
        cleaned_file = os.path.join(new_directory, f"cleaned_{os.path.basename(data_file)}")
        clean_data_file(data_file, cleaned_file)
        cleaned_files.append(cleaned_file)

    # Step 3: Retrieve external data files from the specified directory
    external_directory = os.path.join(home_directory, "Documents", "exfortables", f"{projectile}", f"{element_caplitalized}"f"{formatted_mass}", "residual", product_six_digit_code)
    external_files = [f for f in glob.glob(os.path.join(external_directory, "*")) if not f.endswith('.list')] 

    if not external_files:
        print(f"No external data files found in the directory: {external_directory}")
        return
    
    # Clean external data files and store in cleaned_files_external
    cleaned_external_files = []
    for ext_file in external_files:
        cleaned_file = os.path.join(new_directory, f"cleaned_{os.path.basename(ext_file)}")
        clean_data_file(ext_file, cleaned_file)
        cleaned_external_files.append(cleaned_file)

    print(f"Found {len(external_files)} external data files for plotting.")

    # Specify the output plot file
    plot_file = os.path.join(new_directory, f"combined_cross_section_plot_{product_six_digit_code}.png")

    # Step 2: Generate the GNUplot script for the specific file
    gnuplot_script = generate_combined_gnuplot_script(cleaned_files, external_files, talys_output_file, plot_file)

    # Specify the location of the temporary gnuplot script file
    gnuplot_script_file = os.path.join(new_directory, "gnuplot_script.gp")

    # Step 3: Run the gnuplot script to display the plot
    run_gnuplot(gnuplot_script, gnuplot_script_file)

    print(f"Combined plot generated: {plot_file}")

if __name__ == "__main__":
    main()
