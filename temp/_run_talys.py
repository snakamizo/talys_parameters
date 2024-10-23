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

def generate_gnuplot_script(data_file, plot_file):
    """Generate a GNUplot script to plot the data."""
    gnuplot_script = f"""
set terminal pngcairo enhanced font 'Arial,10' size 800,600
set output '{plot_file}'
set title 'Cross Section Plot'
set xlabel 'Energy (MeV)'
set ylabel 'Cross Section (mb)'
set grid

plot '{data_file}' using 1:2 title '{os.path.basename(data_file)}' with lines
"""
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
    #constant = input("Enter the M2 constant: ")
    
    # Define the directory structure using the home directory
    home_directory = os.path.expanduser("~")  # Get the current user's home directory
    new_directory = os.path.join(home_directory, "Documents", "talys", f"{projectile}-{element}{mass}")

    #Create the new directory (including all parent directory
    os.makedirs(new_directory, exist_ok=True)

    #Specify the output file name in the new directory
    output_file = os.path.join(new_directory, f"talys.inp") 

    # Create the file with the specified parameters
    create_projectile_file(projectile, element, mass, energy, output_file)
    
    print(f"File '{output_file}' created successfully!")

    # Run the bash script with the output file as an argument
    bash_script = os.path.expanduser("./run_talys.sh")
    subprocess.run([bash_script, output_file])

    # Step 1: Search for the "rp*.tot" file that contains the six-digit code
    data_files = search_for_specific_output_files(new_directory, product_six_digit_code)

    if not data_files:
        print(f"No 'rp*.tot' files found with the six-digits '{product_six_digit_code}' in the directory.")
        return

    # Since we"re filtering the six-digit code, we expect only one file.
    data_file = data_files[0]

    # Clean the data file
    cleaned_file = os.path.join(new_directory, f"cleaned_{os.path.basename(data_file)}")
    clean_data_file(data_file, cleaned_file)

    # Specify the output plot file
    plot_file = os.path.join(new_directory, f"cross_section_plot_{product_six_digit_code}.png")

    # Step 2: Generate the GNUplot script for the specific file
    gnuplot_script = generate_gnuplot_script(cleaned_file, plot_file)

    # Specify the location of the temporary gnuplot script file
    gnuplot_script_file = os.path.join(new_directory, "gnuplot_script.gp")

    # Step 3: Run the gnuplot script to display the plot
    run_gnuplot(gnuplot_script, gnuplot_script_file)

    print(f"Plot generated: {plot_file}")

if __name__ == "__main__":
    main()
