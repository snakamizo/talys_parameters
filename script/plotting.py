import os
import subprocess
import colorsys
import re
import glob
import logging
from script.utilities import clean_data_file
from script.talys_modules import extract_code_from_filename
from script.score_table import get_score_tables
from script.elem import ztoelem


def retrieve_external_data(
    exfortables_directory,
    output_directory,
    cleaned_selected_exfortables_files,
    cleaned_all_exfortables_files,
    product_six_digit_code,
    score_dict,
):
    all_exfortables_files = [
        f
        for f in glob.glob(os.path.join(exfortables_directory, "*"))
        if not f.endswith(".list")
    ]
    all_exfortables_files = sorted(
        all_exfortables_files, key=extract_year_from_filename
    )

    if not all_exfortables_files:
        logging.info(
            f"No experimental data files found in the directory: {exfortables_directory}"
        )
        return

    # check the score_table whether to include each external file
    selected_exfortables_files = all_exfortables_files.copy()
    for file in selected_exfortables_files:
        file_code = extract_code_from_filename(file)
        if not file_code:
            logging.info(f"Could not extract code from file: {file}")
            continue

        if file_code in score_dict:
            if score_dict[file_code] == 0:
                selected_exfortables_files.remove(file)
        else:
            logging.info(
                f"Code '{file_code}' not found in score dict, skipping file '{os.path.basename(file)}'"
            )
    logging.info(f"Selected experimental files: {selected_exfortables_files}")

    cleaned_all_exfortables_directory = os.path.join(
        output_directory, f"cleaned_all_exfortables_data{product_six_digit_code}"
    )
    os.makedirs(cleaned_all_exfortables_directory, exist_ok=True)
    cleaned_selected_exfortables_directory = os.path.join(
        output_directory, f"cleaned_selected_exfortables_data{product_six_digit_code}"
    )
    os.makedirs(cleaned_selected_exfortables_directory, exist_ok=True)

    for file in selected_exfortables_files:
        cleaned_selected_exfortables_file = os.path.join(
            cleaned_selected_exfortables_directory, f"cleaned_{os.path.basename(file)}"
        )
        clean_data_file(file, cleaned_selected_exfortables_file)
        cleaned_selected_exfortables_files.append(cleaned_selected_exfortables_file)

    for file in all_exfortables_files:
        cleaned_all_exfortables_file = os.path.join(
            cleaned_all_exfortables_directory,
            f"cleaned_{os.path.basename(file)}",
        )
        clean_data_file(file, cleaned_all_exfortables_file)
        cleaned_all_exfortables_files.append(cleaned_all_exfortables_file)

    logging.info(
        f"Found {len(cleaned_all_exfortables_files)} external data files for plotting."
    )


def extract_label_from_filename(filename, cleaned_selected_exfortables_files):
    base_name = os.path.basename(filename)
    parts = base_name.split("-")

    if len(parts) >= 5:
        author = parts[3]
        data = parts[4].split(".")[0]  # Exclude file extension
        year = parts[4].split(".")[1]
        cleaned_base_names = [
            os.path.basename(file) for file in cleaned_selected_exfortables_files
        ]
        weight = "w1" if base_name in cleaned_base_names else "w0"
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
    cleaned_output_files,
    cleaned_selected_exfortables_files,
    cleaned_all_exfortables_files,
    plot_file,
    element,
    mass,
    code,
):
    product_mass = int(code[3:6])
    product_element = ztoelem(int(code[:3]))
    isomer = code[-1] if code[-1].isalpha() else ""

    gnuplot_script = f"""
set terminal pngcairo enhanced font 'Arial,15' size 800,600
set output '{plot_file}'
set title 'Cross Section {mass}{element.capitalize()} → {product_mass}{product_element}{isomer}'
set xlabel 'Energy (MeV)' font 'Arial,15'
set ylabel 'Cross Section (mb)' font 'Arial,15'
set key font 'Arial,10' 
set grid
set xrange [0:60]

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
    for index, file in enumerate(cleaned_all_exfortables_files):
        ext_label = extract_label_from_filename(
            file, cleaned_selected_exfortables_files
        )
        logging.info(f"File: {file}, Extracted Label: {ext_label}")
        point_type = index + 7

        hue = 1 - index / len(cleaned_all_exfortables_files)
        saturation = 1
        lightness = 0.5

        r, g, b = hsl_to_rgb(hue, saturation, lightness)

        color = rgb_to_hex(r, g, b)
        gnuplot_script += f", '{file}' using 1:3:4 with errorbars title '{ext_label}' pt {point_type} lc rgb '{color}'"

    return gnuplot_script


def generate_chi_squared_gnuplot_script(chi2_values, plot_file, element, mass, code):
    product_mass = int(code[3:6])
    product_element = ztoelem(int(code[:3]))
    isomer = code[-1] if code[-1].isalpha() else ""
    gnuplot_script = f"""
set terminal pngcairo enhanced font 'Arial,15' size 800,600
set output '{plot_file}'
set title 'Chi-squared vs Input file {mass}{element.capitalize()} → {product_mass}{product_element}{isomer}'
set xlabel 'Input file'
set ylabel 'Chi-squared'
set xtics 1
unset xtics 1
set grid
plot '-' using 1:2 with linespoints pt 7 title 'Chi-squared'
"""
    # Add the m2constant and chi2_values pairs to the script
    for index, chi2_value in enumerate(chi2_values, start=1):
        gnuplot_script += f"{index} {chi2_value}\n"

    gnuplot_script += "e\n"

    return gnuplot_script


def generate_average_chi_squared_gnuplot_script(chi2_value_averages, plot_file):
    gnuplot_script = f"""
set terminal pngcairo enhanced font 'Arial,15' size 800,600
set output '{plot_file}'
set title 'Chi-squared (Average of pn, p2n, ppn data) vs Input file'
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


def generate_total_average_chi_squared_gnuplot_script(chi2_value_averages, plot_file):
    gnuplot_script = f"""
set terminal pngcairo enhanced font 'Arial,15' size 800,600
set output '{plot_file}'
set title 'Chi-squared (Average of total data) vs Input file'
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
        logging.info(f"Gnuplot Error: {result.stderr}")
    else:
        logging.info(f"Gnuplot Outputted: {result.stdout}")


def generate_mass_chi_squared_gnuplot_script(chi2_values_list, plot_file, j):
    gnuplot_script = f"""
set terminal pngcairo enhanced font 'Arial,15' size 800,600
set output '{plot_file}'
set title 'Chi-squared (Average of total data) vs Residual mass (Input {j})'
set xlabel 'Residual Mass'
set ylabel 'Chi-squared'
set grid
set xrange [0:240]
set yrange [0:250]
plot '-' using 1:2 notitle with points pt 7 ps 1.5
"""
    if not chi2_values_list or j < 1:
        logging.info(f"chi2_values_list: {chi2_values_list}, j={j}")
    for item in chi2_values_list:
        if len(item) > j:
            residual_mass = item[0]
            chi2_value = item[j]
            gnuplot_script += f"{residual_mass} {chi2_value}\n"
        else:
            logging.warning(f"Skipping item {item} as it doesn't have index {j}")

    gnuplot_script += "e\n"

    return gnuplot_script


def generate_ratio_gnuplot_script(
    chi2_values_list, output_file, numerator_idx, denominator_idx
):
    gnuplot_script = f"""
set terminal png size 800,600
set output '{output_file}'
set title 'Ratio Input {numerator_idx} / Input {denominator_idx} vs Residual Mass'
set xlabel 'Residual Mass'
set ylabel 'Ratio to input 2'
set yrange [0:18]
plot '-' using 1:2 notitle with points pt 7 ps 1.5
"""

    for array in chi2_values_list:
        if array[denominator_idx] != 0:
            gnuplot_script += (
                f"{array[0]} {array[numerator_idx]/array[denominator_idx]}\n"
                if array[denominator_idx] != 0
                else ""
            )
    gnuplot_script += "e\n"

    return gnuplot_script
