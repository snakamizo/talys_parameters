import os
import subprocess
import colorsys
import re
import glob

from utils import clean_data_file
from talys_modules import extract_code_from_filename
from score_table import get_score_tables


def load_experimental_data(file_path):
    experimental_data = []
    with open(file_path, "r") as file:
        for line in file:
            if line.startswith("#"):
                continue
            # Split the line into components (assuming they are space-separated)
            data = line.split()
            # Convert each component to a float, and make sure there are 5 columns
            if len(data) == 5:
                experimental_data.append([float(val) for val in data])
            else:
                print(f"Invalid data format in file {file_path}: {line.strip()}")
    return experimental_data


def retrieve_external_data(
    exfortables_directory,
    output_directory,
    cleaned_external_files,
    cleaned_all_external_files,
    product_six_digit_code,
    score_dict,
):
    all_external_files = [
        f
        for f in glob.glob(os.path.join(exfortables_directory, "*"))
        if not f.endswith(".list")
    ]

    if not all_external_files:
        print(f"No external data files found in the directory: {exfortables_directory}")
        return

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
            print(
                f"Code '{file_code}' not found in score dict, skipping file '{os.path.basename(ext_file)}'"
            )
    if not external_files:
        print("No external data files selected based on score_dict.")
        return

    cleaned_all_exfortables_directory = os.path.join(
        output_directory, f"cleaned_all_external_data{product_six_digit_code}"
    )
    os.makedirs(cleaned_all_exfortables_directory, exist_ok=True)
    cleaned_exfortables_directory = os.path.join(
        output_directory, f"cleaned_external_data{product_six_digit_code}"
    )
    os.makedirs(cleaned_exfortables_directory, exist_ok=True)

    # Check if we have any files left after exclusions
    if not external_files:
        print("No external data files selected.")
        return
    ext_files = sorted(external_files, key=extract_year_from_filename)
    for ext_file in ext_files:
        cleaned_external_file = os.path.join(
            cleaned_all_exfortables_directory, f"cleaned_{os.path.basename(ext_file)}"
        )
        clean_data_file(ext_file, cleaned_external_file)
        cleaned_external_files.append(cleaned_external_file)

    sorted_all_external_files = sorted(
        all_external_files, key=extract_year_from_filename
    )

    for sorted_all_external_file in sorted_all_external_files:
        cleaned_all_external_file = os.path.join(
            cleaned_exfortables_directory,
            f"cleaned_{os.path.basename(sorted_all_external_file)}",
        )
        clean_data_file(sorted_all_external_file, cleaned_all_external_file)
        cleaned_all_external_files.append(cleaned_all_external_file)

    print(f"Found {len(external_files)} external data files for plotting.")


def extract_label_from_filename(filename, cleaned_external_files):
    base_name = os.path.basename(filename)
    parts = base_name.split("-")

    if len(parts) >= 5:
        author = parts[3]
        data = parts[4].split(".")[0]  # Exclude file extension
        year = parts[4].split(".")[1]

        weight = "w1" if filename in cleaned_external_files else "w0"
        return f"{author}-{data} ({year}) {weight}"
    return base_name  # Return filename if pattern is unexpected


def extract_year_from_filename(filename):
    match = re.search(
        r"\.(\d{4})$", filename
    )  # Looks for a 4-digit year at the end of the filename
    if match:
        return int(match.group(1))
    return None


def rgb_to_hex(r, g, b):
    return f"#{r:02X}{g:02X}{b:02X}"


def hsl_to_rgb(h, s, l):
    """Convert HSL color to RGB."""
    rgb_float = colorsys.hls_to_rgb(h, l, s)
    return tuple(
        int(255 * x) for x in rgb_float
    )  # Convert float [0, 1] to int [0, 255]


def generate_combined_gnuplot_script(
    cleaned_output_files, cleaned_external_files, cleaned_all_external_files, plot_file
):
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
        label = f"Input {round(1 + i , 5)}"
        if i == 0:
            gnuplot_script += (
                f"'{cleaned_output_file}' using 1:2 title '{label}' with lines"
            )
        else:
            gnuplot_script += (
                f", '{cleaned_output_file}' using 1:2 title '{label}' with lines"
            )

    # Add external data files
    for index, cleaned_all_external_file in enumerate(cleaned_all_external_files):
        ext_label = extract_label_from_filename(
            cleaned_all_external_file, cleaned_external_files
        )
        point_type = index + 7

        hue = index / len(cleaned_all_external_files)
        saturation = 1
        lightness = 0.5

        r, g, b = hsl_to_rgb(hue, saturation, lightness)

        color = rgb_to_hex(r, g, b)
        gnuplot_script += f", '{cleaned_all_external_file}' using 1:3:4 with errorbars title '{ext_label}' pt {point_type} lc rgb '{color}'"

    return gnuplot_script


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


def run_gnuplot(gnuplot_script_content, script_file):
    with open(script_file, "w") as f:
        f.write(gnuplot_script_content)

    result = subprocess.run(["gnuplot", script_file], capture_output=True, text=True)

    if result.returncode != 0:
        print("Gnuplot Error:", result.stderr)
    else:
        print("Gnuplot Output:", result.stdout)
