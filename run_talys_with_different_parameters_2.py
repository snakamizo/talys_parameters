import os
import glob
import subprocess

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
        f.write(f"M2constant {constant}\n")

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

def generate_gnuplot_script(data_files, plot_file):
    """Generate a GNUplot script to plot the data."""
    gnuplot_script = f"""
set terminal pngcairo enhanced font 'Arial,10' size 800,600
set output '{plot_file}'
set title 'Cross Section Plot for Different M2constants'
set xlabel 'Energy (MeV)'
set ylabel 'Cross Section (mb)'
set grid
"""
    # Add each data file to the plot
    for i, data_file in enumerate(data_files):
        label = f"M2constant {round(3 - i * 0.2, 1)}" #Adjusting the label based on M2constant values
        if i == 0:
            gnuplot_script += f"plot '{data_file}' using 1:2 title '{label}' with lines"
        else:
            gnuplot_script += f", '{data_file}' using 1:2 title '{label}' with lines"

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
    mass = input("Enter the mass: ")
    energy = input("Enter the energy: ")
    product_six_digit_code = input("Enter the Z&A of product in six digits: ")
    
    # Define the M2constant
    constants = [round(x, 1) for x in list(frange(3, 1, -0.2))]

    # Define the combined output directory
    combined_directory = os.path.join(os.path.expanduser("~"), "Documents", "talys", f"{projectile}-{element}{mass}-({product_six_digit_code})_M2_3to1_02")
    os.makedirs(combined_directory, exist_ok=True)
    
    # To store all the data files for plotting
    all_data_files = []
    
    for constant in constants:
        # Create a unique directory for each M2constant
        new_directory = os.path.join(combined_directory, f"{projectile}-{element}{mass}_M2_{constant}")
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
        data_files = search_for_specific_output_files(new_directory, product_six_digit_code)
        if not data_files:
            print(f"No 'rp*.tot' files found for M2constant {constant}.")
            continue

        # Since we"re filtering the six-digit code, we expect only one file.
        data_file = data_files[0]

        # Clean the data file
        cleaned_file = os.path.join(new_directory, f"cleaned_{os.path.basename(data_files[0])}")
        clean_data_file(data_files[0], cleaned_file)

        # Collect the cleaned file for final plot
        all_data_files.append(cleaned_file)

    # If we have multiple data files, generate a combined plot
    if all_data_files:
        combined_plot_file = os.path.join(combined_directory, "combined_cross_section_plot.png")
        gnuplot_script = generate_gnuplot_script(all_data_files, combined_plot_file)

        # Specify the location of the temporary gnuplot script file
        gnuplot_script_file = os.path.join(combined_directory, "gnuplot_combined_script.gp")

        # Step 3: Run the gnuplot script to display the plot
        run_gnuplot(gnuplot_script, gnuplot_script_file)

        print(f"Combined plot generated: {combined_plot_file}")
    else:
        print("No valid data files found to plot.")

def frange(start, stop, step):
    """Helper function to generate float ranges."""
    while start > stop:
        yield start
        start += step

if __name__ == "__main__":
    main()