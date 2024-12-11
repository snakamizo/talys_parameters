import os
import json
import logging
from concurrent.futures import ProcessPoolExecutor
import concurrent
from glob import glob
import numpy as np
from tqdm import tqdm
from copy import deepcopy
import multiprocessing
from config import (
    TALYS_INP_FILE_NAME,
    IAEA_MEDICAL_LIST,
    CALC_PATH,
    EXFORTABLES_PATH,
    ENERGY_RANGE_MIN,
    ENERGY_RANGE_MAX,
    ENERGY_STEP,
    N,
    TIMEOUT_SECONDS,
)
from script.plotting import (
    retrieve_external_data,
    generate_combined_gnuplot_script,
    run_gnuplot,
    generate_chi_squared_gnuplot_script,
    generate_total_average_chi_squared_gnuplot_script,
    generate_mass_chi_squared_gnuplot_script,
    generate_ratio_gnuplot_script,
)
from script.utilities import (
    split_by_number,
    clean_data_file,
    setup_logging,
    generate_six_digit_code_from_product_info,
)
from script.talys_modules import (
    create_talys_inp,
    run_talys,
    search_residual_output,
)
from script.score_table import get_score_tables

from script.chi_squared import (
    calculate_combined_chi_squared,
    load_simulation_data,
)
from script.latex import (
    generate_latex_document,
    add_to_latex_document1,
    end_latex_document,
    add_totalchi_to_latex_document,
    add_masschi_to_latex_document,
    add_ratio_to_latex_document,
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
        with open(filepath, "r") as f:
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
        target = split_by_number(l[0])
        residual = split_by_number(l[3])

        if (
            target[1] == "000"
            or projectile == "g"
            or projectile == "n"
            or projectile == "d"
            or projectile == "p"
            or projectile == "h"
            or (target == ["I", "127", ""] and residual == ["Xe", "122", ""])
            or residual == ["Ba", "128", ""]
            or (
                projectile == "p"
                and target == ["Th", "232", ""]
                and residual == ["Ra", "225", ""]
            )
            or (
                projectile == "p"
                and target == ["Tl", "203", ""]
                and residual == ["Pb", "202", "m"]
            )
            or (
                projectile == "d"
                and target == ["Yb", "176", ""]
                and residual == ["Lu", "177", "g"]
            )
            or (target == ["Th", "232", ""] and residual == ["Ac", "225", ""])
            or (target == ["Th", "232", ""] and residual == ["Th", "227", ""])
        ):
            # int(elemtoz(target[0])) != int(elemtoz(residual[0])) or
            # int(target[1]) != int(residual[1]) + 1):
            continue

        medical_reactions += [
            {
                "projectile": projectile,
                "element": target[0],
                "mass": target[1],
                "target": target,
                "residual": residual,
            }
        ]

    return medical_reactions


def process(
    input,
    score_dict,
    gnuplot_output_directory,
    chi2_value_total_averages,
    chi2_values_list,
):
    logging.info(input)

    projectile = input["projectile"]
    element = input["element"]
    mass = int(input["mass"])
    target = input["target"]
    residual = input["residual"]
    residual_mass = int(residual[1])
    logging.info(f"residual == {residual_mass}, type: {type(residual_mass)}")

    energy_range = f"{ENERGY_RANGE_MIN} {ENERGY_RANGE_MAX} {ENERGY_STEP}"

    product_six_digit_code = generate_six_digit_code_from_product_info(residual)
    logging.info("Generated six-digit code: %s", product_six_digit_code)

    cleaned_selected_exfortables_files = []
    cleaned_all_exfortables_files = []

    exfortables_directory = os.path.join(
        EXFORTABLES_PATH,
        f"{projectile}",
        f"{element.capitalize()}{mass:03}",
        "residual",
        product_six_digit_code,
    )
    retrieve_external_data(
        exfortables_directory,
        CALC_PATH,
        cleaned_selected_exfortables_files,
        cleaned_all_exfortables_files,
        product_six_digit_code,
        score_dict,
    )

    cleaned_output_files = []
    chi2_values = []

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
            logging.info(
                f"Directory {calc_directory} already exists, skipping the calculation."
            )

        # Search for and clean data files for each six-digit code
        data_file = search_residual_output(calc_directory, product_six_digit_code)
        if not data_file:
            logging.info(
                f"No 'rp*' files found with the six-digits '{product_six_digit_code}' in the directory."
            )
            continue
        cleaned_output_file = os.path.join(
            calc_directory, f"cleaned_{os.path.basename(data_file)}"
        )
        clean_data_file(data_file, cleaned_output_file)
        cleaned_output_files.append(cleaned_output_file)

        simulation_data = load_simulation_data(cleaned_output_file)
        cross_section_sim_max = np.max(simulation_data[:, 1])
        logging.debug(f"Maximum simulation cross-section: {cross_section_sim_max}")
        combined_chi_squared = calculate_combined_chi_squared(
            CALC_PATH,
            cleaned_selected_exfortables_files,
            simulation_data,
            product_six_digit_code,
            projectile,
            target,
            i,
            cross_section_sim_max,
        )
        chi2_values.append(combined_chi_squared)

    chi2_values_array = np.array(chi2_values, dtype=float)
    logging.info(
        f"chi2_values_array = {chi2_values_array}, type: {chi2_values_array.dtype}"
    )
    for idx, value in enumerate(chi2_values_array):
        chi2_value_total_averages[idx] += value

    chi2_value_array_with_mass = np.concatenate(
        [np.array([residual_mass], dtype=np.float64), chi2_values_array]
    )
    logging.info(f"chi2_value_array_with_mass: {chi2_value_array_with_mass}")
    chi2_values_list.append(chi2_value_array_with_mass)

    gnuplot_each_output_directory = os.path.join(
        gnuplot_output_directory,
        f"gnuplot_output_{projectile}-{mass}{element}_{residual[1]}{residual[2]}{residual[0]}",
    )
    os.makedirs(gnuplot_each_output_directory, exist_ok=True)

    plot_file = os.path.join(
        gnuplot_each_output_directory,
        f"combined_cross_section_plot_{product_six_digit_code}.png",
    )
    gnuplot_script = generate_combined_gnuplot_script(
        cleaned_output_files,
        cleaned_selected_exfortables_files,
        cleaned_all_exfortables_files,
        plot_file,
        element,
        mass,
        product_six_digit_code,
    )
    gnuplot_script_file = os.path.join(
        gnuplot_each_output_directory,
        f"combined_cross_section_plot_{product_six_digit_code}.gp",
    )
    run_gnuplot(gnuplot_script, gnuplot_script_file)

    # Plot chi-squared vs m2constant

    chi_squared_plot_file = os.path.join(
        gnuplot_each_output_directory,
        f"chi_squared_vs_input_{product_six_digit_code}.png",
    )
    gnuplot_script = generate_chi_squared_gnuplot_script(
        chi2_values, chi_squared_plot_file, element, mass, product_six_digit_code
    )
    gnuplot_script_file = os.path.join(
        gnuplot_each_output_directory, f"chi_squared_vs_input.gp"
    )
    run_gnuplot(gnuplot_script, gnuplot_script_file)

    add_to_latex_document1(
        gnuplot_output_directory,
        gnuplot_each_output_directory,
        projectile,
        mass,
        element,
        residual,
    )


def main():
    ## get nuclides to calculate
    medical_isotope_reactions = get_IAEA_medical_isotope_nuclides()

    # medical_isotope_reactions = [
    # {"projectile": "p", "element": "n", "mass": 14, "target": ['N', '014', ''], "residual": ['C', '011', '']},
    # {"projectile": "p", "element": "o", "mass": 18, "target": ['O', '018', ''], "residual": ['F', '018', '']},
    # {"projectile": "p", "element": "ni", "mass": 64, "target": ['Ni', '064', ''], "residual": ['Cu', '064', '']},
    # {"projectile": "p", "element": "ga", "mass": 69, "target": ['Ga', '069', ''], "residual": ['Ge', '068', '']},
    # {"projectile": "p", "element": "y", "mass": 89, "target": ['Y', '089', ''], "residual": ['Zr', '089', '']},
    # {"projectile": "p", "element": "y", "mass": 89, "target": ['Y', '089', ''], "residual": ['Zr', '088', '']},
    # {"projectile": "p", "element": "y", "mass": 89, "target": ['Y', '089', ''], "residual": ['Y', '088', '']},
    # {"projectile": "p", "element": "mo", "mass": 100, "target": ['Mo', '100', ''], "residual": ['Tc', '099', 'm']},
    # {"projectile": "p", "element": "te", "mass": 124, "target": ['Te', '124', ''], "residual": ['I', '123', '']}
    # ]
    num_reactions = len(medical_isotope_reactions)
    os.makedirs(CALC_PATH, exist_ok=True)
    score_dict = get_score_tables()

    setup_logging(CALC_PATH, "log.txt")
    logging.info(f"Number of valid medical isotope reactions: {num_reactions}")
    # logging.info(f"Weight_list: {score_dict}")

    gnuplot_output_directory = os.path.join(
        CALC_PATH, "gnuplot_output_excluding0_Th_out"
    )
    os.makedirs(gnuplot_output_directory, exist_ok=True)
    generate_latex_document(gnuplot_output_directory)

    in_process_targets = []

    manager = multiprocessing.Manager()
    chi2_value_total_averages = manager.list(np.zeros(5))
    chi2_values_list = manager.list()
    skipped_reactions = manager.list()

    with concurrent.futures.ProcessPoolExecutor(max_workers=N) as executor:
        futures = []
        with tqdm(
            total=len(medical_isotope_reactions), desc="Processing reactions"
        ) as progress_bar:
            for input in medical_isotope_reactions:
                target_identifier = (
                    f"{input['projectile']}-{input['element']}{input['mass']}"
                )

                if target_identifier in in_process_targets:
                    skipped_reactions.append(input)
                    continue

                in_process_targets.append(target_identifier)
                futures.append(
                    executor.submit(
                        process,
                        input,
                        score_dict,
                        gnuplot_output_directory,
                        chi2_value_total_averages,
                        chi2_values_list,
                    )
                )

            # Wait for all futures to complete
            for future in concurrent.futures.as_completed(futures):
                progress_bar.update(1)
                result_input = medical_isotope_reactions[futures.index(future)]
                result_target_identifier = f"{result_input['projectile']}-{result_input['element']}{result_input['mass']}"

                # in_process_targets.remove(result_target_identifier)
                # future.result()

                try:
                    future.result(timeout=TIMEOUT_SECONDS)
                except concurrent.futures.TimeoutError:
                    logging.error(f"Processing timed out for: {result_input}")
                    skipped_reactions.append(result_input)
                except Exception as e:
                    logging.error(f"Error processsing {result_input}: {e}")
                finally:
                    if result_target_identifier in in_process_targets:
                        in_process_targets.remove(result_target_identifier)

    logging.debug(f"Skipped Reactionsss: {skipped_reactions}")
    for input in skipped_reactions:
        try:
            process(
                input,
                score_dict,
                gnuplot_output_directory,
                chi2_value_total_averages,
                chi2_values_list,
            )
        except Exception as e:
            logging.error(f"Error retrying {input}: {e}")

    chi2_values_list = [arr for arr in chi2_values_list if not np.all(arr[1:6] == 0)]
    num_reactions = len(chi2_values_list)

    chi2_value_total_averages = np.array(chi2_value_total_averages)
    chi2_value_total_averages /= num_reactions

    chi_squared_total_average_plot_file = os.path.join(
        gnuplot_output_directory, "chi_squared_total_average_vs_input.png"
    )
    gnuplot_script4 = generate_total_average_chi_squared_gnuplot_script(
        chi2_value_total_averages, chi_squared_total_average_plot_file
    )
    gnuplot_script_file4 = os.path.join(
        gnuplot_output_directory, "chi_squared_total_average_vs_input.gp"
    )
    run_gnuplot(gnuplot_script4, gnuplot_script_file4)

    logging.info(f"The list chi2_values_list contains {len(chi2_values_list)} arrays.")

    add_totalchi_to_latex_document(gnuplot_output_directory)
    logging.info(f"chi2_values_list: {chi2_values_list}")

    # add_table_to_latex_document(gnuplot_output_directory, chi2_values_list)

    for j in range(1, 6):
        chi_squared_value_mass_plot_file = os.path.join(
            gnuplot_output_directory, f"chi_squared_value_vs_mass_inp{j}.png"
        )
        gnuplot_script5 = generate_mass_chi_squared_gnuplot_script(
            chi2_values_list, chi_squared_value_mass_plot_file, j
        )
        gnuplot_script_file5 = os.path.join(
            gnuplot_output_directory, f"chi_squared_value_vs_mass_inp{j}.gp"
        )
        run_gnuplot(gnuplot_script5, gnuplot_script_file5)
        add_masschi_to_latex_document(gnuplot_output_directory, j)

    for _, column_idx in enumerate([1, 3, 4, 5], start=1):
        ratio_plot_file = os.path.join(
            gnuplot_output_directory, f"ratio_vs_mass_col{column_idx}.png"
        )
        gnuplot_script_ratio = generate_ratio_gnuplot_script(
            chi2_values_list,
            ratio_plot_file,
            numerator_idx=column_idx,
            denominator_idx=2,
        )
        gnuplot_script_file_ratio = os.path.join(
            gnuplot_output_directory, f"ratio_vs_mass_col{column_idx}.gp"
        )
        run_gnuplot(gnuplot_script_ratio, gnuplot_script_file_ratio)
        add_ratio_to_latex_document(gnuplot_output_directory, column_idx)

    end_latex_document(gnuplot_output_directory)
    logging.info("All process finished.")


if __name__ == "__main__":
    main()
