import os
import json
import logging
from concurrent.futures import ProcessPoolExecutor
import concurrent
from glob import glob
import numpy as np
import multiprocessing
from tqdm import tqdm

from config import (
    TALYS_INP_FILE_NAME,
    IAEA_MEDICAL_LIST,
    CALC_PATH,
    EXFORTABLES_PATH,
    ENERGY_RANGE_MIN,
    ENERGY_RANGE_MAX,
    ENERGY_STEP,
    ERROR_THRESHOLD,
    XS_THRESHOLD, 
    N,
)
from plotting import (
    retrieve_external_data,
    generate_combined_gnuplot_script,
    run_gnuplot,
    generate_chi_squared_gnuplot_script,
    generate_average_chi_squared_gnuplot_script,
    generate_total_average_chi_squared_gnuplot_script
)
from utils import (
    split_by_number,
    clean_data_file,
    genenerate_six_digit_code,
    setup_logging
)
from talys_modules import (
    create_talys_inp,
    run_talys,
    search_residual_output,
)
from score_table import get_score_tables

from chi_squared import (
    calculate_combined_chi_squared, 
    load_simulation_data,
)
from latex import (
    generate_latex_document,
    add_to_latex_document,
    end_latex_document,
    add_totalchi_to_latex_document,
)

parameter_check_cases = [
    {"ldmodel": 1, "colenhance": "n"},
    {"ldmodel": 1, "colenhance": "y"},
    {"ldmodel": 2, "colenhance": "n"},
    {"ldmodel": 2, "colenhance": "y"},
    {"ldmodel": 5, "colenhance": "n"},
]

def load_score_dict(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            score_dict = json.load(f)
        print(f"Score dictionary loaded from {filepath}")
        return score_dict
    else:
        print(f"Score dictionary file not found at {filepath}")
        return {}

def get_IAEA_medical_isotope_nuclides() -> list:
    # format
    # Br000	p	X	Se072
    medical_reactions = []

    f = open(IAEA_MEDICAL_LIST, "r")

    for line in f.readlines():
        l = line.split()
        projectile = l[1]
        target = split_by_number( l[0] )
        residual = split_by_number( l[3] )

        medical_reactions += [ {"projectile": projectile, "element": target[0], "mass": target[1], "target": target, "residual": residual} ]

    return medical_reactions

def process(input, score_dict, gnuplot_output_directory, chi2_value_total_averages, chi2_values_list):
    logging.info(input)
    projectile = input["projectile"]
    element = input["element"]
    mass = int(input["mass"])
    residual = input["residual"]
    residual_element = residual[0]
    residual_mass = residual[1]

    energy_range = f"{ENERGY_RANGE_MIN} {ENERGY_RANGE_MAX} {ENERGY_STEP}"

    product_six_digit_codes = [
        genenerate_six_digit_code("pn", element, f"{mass:03}"),
        genenerate_six_digit_code("p2n", element, f"{mass:03}"),
        genenerate_six_digit_code("ppn", element, f"{mass:03}")
    ]
    logging.info("Generated six-digit codes: %s", product_six_digit_codes)
    cleaned_selected_exfortables_files = [[] for _ in range(3)]
    cleaned_all_exfortables_files = [[] for _ in range(3)]
    for i, code in enumerate(product_six_digit_codes):
        exfortables_directory = os.path.join(
            EXFORTABLES_PATH,
            f"{projectile}",
            f"{element.capitalize()}{mass:03}",
            "residual",
            code,
        )
        retrieve_external_data(
            exfortables_directory,
            CALC_PATH,
            cleaned_selected_exfortables_files[i],
            cleaned_all_exfortables_files[i],
            code,
            score_dict,
        )
        
    cleaned_output_files = [[] for _ in range(3)]
    chi2_values = [[] for _ in range(3)]
    chi2_value_averages = []

    for i in range(len(parameter_check_cases)): 
        calc_directory = os.path.join(
            CALC_PATH, f"{projectile}-{element}{mass}_chisquared_{i}"
        )
        if not os.path.exists(calc_directory):
            os.makedirs(calc_directory, exist_ok=True)
            input_file = os.path.join(calc_directory, TALYS_INP_FILE_NAME)
            create_talys_inp(input_file, input, energy_range, parameter_check_cases[i])
            run_talys(input_file, calc_directory)
        else:
            logging.info(f"Directory {calc_directory} already exists, skipping the calculation.")
    
        # Search for and clean data files for each six-digit code
        for j, code in enumerate(product_six_digit_codes):
            data_file = search_residual_output(calc_directory, code)
            if not data_file:
                logging.info(
                    f"No 'rp*' files found with the six-digits '{code}' in the directory."
                )
                continue
            cleaned_output_file = os.path.join(
                calc_directory, f"cleaned_{os.path.basename(data_file)}"
            )
            clean_data_file(data_file, cleaned_output_file)
            cleaned_output_files[j].append(cleaned_output_file)

            simulation_data = load_simulation_data(cleaned_output_file)
            combined_chi_squared = calculate_combined_chi_squared(
                CALC_PATH,
                cleaned_selected_exfortables_files[j],
                simulation_data,
                ERROR_THRESHOLD,
                XS_THRESHOLD,
                code,
            )
            chi2_values[j].append(combined_chi_squared)

        chi2_value_average = sum(chi2_values[j][-1] for j in range(3)) / 3.0
        chi2_value_averages.append(chi2_value_average)
        
    chi2_value_averages_array = np.array(chi2_value_averages)
    chi2_value_total_averages += chi2_value_averages_array
    chi2_value_averages_array_with_mass = ({residual_mass}, chi2_value_averages_array)
    chi2_values_list.append()

    gnuplot_each_output_directory = os.path.join(gnuplot_output_directory, f"gnuplot_output {projectile}-{mass}{element}")
    os.makedirs(gnuplot_each_output_directory, exist_ok=True)

    for j, code in enumerate(product_six_digit_codes):
        plot_file = os.path.join(
            gnuplot_each_output_directory, f"combined_cross_section_plot_{code}.png"
        )
        gnuplot_script = generate_combined_gnuplot_script(
            cleaned_output_files[j],
            cleaned_selected_exfortables_files[j],
            cleaned_all_exfortables_files[j],
            plot_file,
            element,
            mass,
            code
        )
        gnuplot_script_file = os.path.join(
            gnuplot_each_output_directory, f"combined_cross_section_plot_{code}.gp"
        )
        run_gnuplot(gnuplot_script, gnuplot_script_file)
    
    # Plot chi-squared vs m2constant
    for j, code in enumerate(product_six_digit_codes):
        chi_squared_plot_file = os.path.join(
            gnuplot_each_output_directory, f"chi_squared_vs_input_{code}.png"
        )
        gnuplot_script = generate_chi_squared_gnuplot_script(
            chi2_values[j], 
            chi_squared_plot_file,
            element,
            mass,
            code
        )
        gnuplot_script_file = os.path.join(
            gnuplot_each_output_directory, f"chi_squared_vs_input_{j+1}.gp"
        )
        run_gnuplot(gnuplot_script, gnuplot_script_file)

    chi_squared_average_plot_file = os.path.join(
        gnuplot_each_output_directory, f"chi_squared_average_vs_input.png"
    )
    gnuplot_script3 = generate_average_chi_squared_gnuplot_script(
        chi2_value_averages, chi_squared_average_plot_file
    )
    gnuplot_script_file3 = os.path.join(
        gnuplot_each_output_directory, "chi_squared_average_vs_input.gp"
    )
    run_gnuplot(gnuplot_script3, gnuplot_script_file3)

    add_to_latex_document(gnuplot_output_directory, gnuplot_each_output_directory, projectile, mass, element)


def main():
    ## get nuclides to calculate
    # medical_isotope_reactions = get_IAEA_medical_isotope_nuclides()
    medical_isotope_reactions = [
    {"projectile": "p", "element": "c", "mass": 13},
    {"projectile": "p", "element": "o", "mass": 18},
    {"projectile": "p", "element": "ni", "mass": 64},
    {"projectile": "p", "element": "ga", "mass": 69},
    {"projectile": "p", "element": "y", "mass": 89},
    {"projectile": "p", "element": "kr", "mass": 82},
    {"projectile": "p", "element": "cd", "mass": 111},
    {"projectile": "p", "element": "cd", "mass": 112},
    {"projectile": "p", "element": "te", "mass": 123},
    {"projectile": "p", "element": "te", "mass": 124}
]
    os.makedirs(CALC_PATH, exist_ok=True)

    ## get score table in Python dictionary
    score_dict = get_score_tables()
    
    setup_logging(CALC_PATH, "log.txt")

    gnuplot_output_directory = os.path.join(CALC_PATH, "gnuplot_output")
    os.makedirs(gnuplot_output_directory, exist_ok=True)
    generate_latex_document(gnuplot_output_directory)
    number_of_average_chi_squared_run = 0.0

    in_process_targets = set()
    skipped_reactions = []
    chi2_values_list = []

    manager = multiprocessing.Manager()
    chi2_value_total_averages = manager.list(np.zeros(5))

    with concurrent.futures.ProcessPoolExecutor(max_workers=N) as executor:
        futures = []
        with tqdm(total=len(medical_isotope_reactions), desc="Processing reactions") as progress_bar:
            for input in medical_isotope_reactions:
                target_identifier = f"{input['element']}{input['mass']}"

                if target_identifier in in_process_targets:
                    skipped_reactions.append(input)
                    continue

                in_process_targets.add(target_identifier)
                futures.append(executor.submit(process, input, score_dict, gnuplot_output_directory, chi2_value_total_averages, chi2_values_list))

            # Wait for all futures to complete
            for future in concurrent.futures.as_completed(futures):
                progress_bar.update(1)
                result_input = medical_isotope_reactions[futures.index(future)]
                result_target_identifier = f"{result_input['element']}{result_input['mass']}"

                in_process_targets.remove(result_target_identifier)
                future.result()

    for input in skipped_reactions:
        process(input, score_dict, gnuplot_output_directory, chi2_value_total_averages, number_of_average_chi_squared_run)

    chi2_value_total_averages /= number_of_average_chi_squared_run
    chi_squared_total_average_plot_file = os.path.join(
        gnuplot_output_directory, f"chi_squared_total_average_vs_input.png"
    )
    gnuplot_script4 = generate_total_average_chi_squared_gnuplot_script(chi2_value_total_averages, chi_squared_total_average_plot_file)
    gnuplot_script_file4 = os.path.join(
        gnuplot_output_directory, "chi_squared_total_average_vs_input.gp"
    )
    run_gnuplot(gnuplot_script4, gnuplot_script_file4)

    add_totalchi_to_latex_document(gnuplot_output_directory)
    end_latex_document(gnuplot_output_directory)
    logging.info("All process finished.")
   
if __name__ == "__main__":
    main()