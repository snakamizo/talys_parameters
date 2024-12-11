import os
import json
import logging
import numpy as np
from concurrent.futures import ProcessPoolExecutor

from config import (
    TALYS_INP_FILE_NAME,
    IAEA_MEDICAL_LIST,
    CALC_PATH,
    ENERGY_RANGE_MIN,
    ENERGY_RANGE_MAX,
    ENERGY_STEP,
    N,
)
from plotting import (
    load_experimental_data,
    retrieve_external_data,
    generate_combined_gnuplot_script,
    run_gnuplot,
    generate_combined_gnuplot_script,
    generate_chi_squared_gnuplot_script,
    generate_combined_chi_squared_gnuplot_script,
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


parameter_check_cases = [
    {"ldmodel": 1, "colenhance": "n"},
    {"ldmodel": 1, "colenhance": "y"},
    {"ldmodel": 2, "colenhance": "n"},
    {"ldmodel": 2, "colenhance": "y"},
    {"ldmodel": 5, "colenhance": "n"},
]

def interpolate_simulation(energy_exp, simulation_data):
    """Linearly interpolation"""
    for i in range(1, len(simulation_data)):
        e1, cs1 = simulation_data[i - 1]
        e2, cs2 = simulation_data[i]

        if e1 <= energy_exp <= e2:
            return cs1 + (cs2 - cs1) * (energy_exp - e1) / (e2 - e1)
    return None  # If outside the range of simulation data


def calculate_combined_chi_squared(
    output_directory, cleaned_external_files, simulation_data, ERROR_THRESHOLD, code
):
    chi_squared = 0.0
    dataset_chi_squared_list = []
    valid_datasets = 0.0
    output_file_path = os.path.join(
        output_directory, f"chi_squared_values_{code}.txt"
    )

    with open(output_file_path, "w") as output_file:
        output_file.write("#File Name\tChi-Squared Value\n")
        for cleaned_external_file in cleaned_external_files:
            experimental_data = load_experimental_data(
                cleaned_external_file
            )  # Load the external file
            valid_points = 0.0
            chi_squared_for_dataset = 0.0  # Initialize chi-squared for this dataset

            print(f"\nProcessing file: {cleaned_external_file}")

            for exp_point in experimental_data:
                try:
                    # Try to unpack assuming exp_point is iterable
                    energy_exp, _, cross_section_exp, delta_cross_exp, _ = exp_point
                except TypeError:
                    print(
                        f"Skipping invalid data point in file {cleaned_external_file}: {exp_point}"
                    )
                    continue  # Skip to the next point if unpacking fails

                if delta_cross_exp < ERROR_THRESHOLD * cross_section_exp:
                    print(
                        f"Skipping data point due to small delta_cross_exp (< {ERROR_THRESHOLD * 100}% of cross_section) for energy {energy_exp}"
                    )
                    continue

                sim_cross_section = interpolate_simulation(energy_exp, simulation_data)

                if sim_cross_section is not None and delta_cross_exp > 0:
                    chi_squared_for_dataset += (
                        (cross_section_exp - sim_cross_section) ** 2
                    ) / (delta_cross_exp**2)
                    valid_points += 1  # Count this point as valid
                else:
                    print(
                        f"Skipping data point due to invalid delta_cross_exp or no simulation match for energy {energy_exp}"
                    )

            if valid_points > 0:
                normalized_chi_squared = chi_squared_for_dataset / valid_points
                chi_squared += normalized_chi_squared
                dataset_chi_squared_list.append(normalized_chi_squared)
                valid_datasets += 1
                output_file.write(
                    f"{cleaned_external_file}\t{normalized_chi_squared:.6f}\n"
                )
                print(f"Valid points for {cleaned_external_file}: {valid_points}")
                print(
                    f"Normalized chi-squared for dataset {cleaned_external_file}: {normalized_chi_squared:.6f}"
                )
            else:
                print(
                    f"No valid points in dataset {cleaned_external_file}, skipping normalization."
                )

    if valid_datasets > 0:
        chi_squared /= valid_datasets
    print("\nChi-squared values for each dataset:", dataset_chi_squared_list)
    print(f"Number of valid datasets: {valid_datasets}")
    return chi_squared

def load_simulation_data(file_path):
    return np.loadtxt(file_path, usecols=(0, 1))

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



def main():
    ## get nuclides to calculate
    # medical_isotope_reactions = get_IAEA_medical_isotope_nuclides()
    medical_isotope_reactions = [
    {"projectile": "p", "element": "ga", "mass": 69},
    {"projectile": "p", "element": "y", "mass": 89},
    {"projectile": "p", "element": "te", "mass": 124}
]
    ## get score table in Python dictionary
    score_dict = get_score_tables()

    setup_logging(CALC_PATH, "log.txt")

    for input in medical_isotope_reactions:
        logging.info(input)
        projectile = input["projectile"]
        element = input["element"]
        mass = int(input["mass"])

        ################### Do we need this part?
        output_directory = os.path.join(
            CALC_PATH,
            f"{projectile}-{element}{mass}_chisquared_triple_test",
        )
        os.makedirs(output_directory, exist_ok=True)

        energy_range = f"{ENERGY_RANGE_MIN} {ENERGY_RANGE_MAX} {ENERGY_STEP}"

        for i in range(len(parameter_check_cases)): 
            calc_directory = os.path.join(
                output_directory, f"{projectile}-{element}{mass}_chisquared_{i}"
            )  # CALC_PATH
            os.makedirs(calc_directory, exist_ok=True)

            ## create input
            input_file = os.path.join(calc_directory, TALYS_INP_FILE_NAME)
            create_talys_inp(input_file, input, energy_range, parameter_check_cases[i])

            # actual run
            run_talys(input_file, calc_directory)


        # cleaned_external_files = [[] for _ in range(3)]
        # cleaned_all_external_files = [[] for _ in range(3)]
        # cleaned_output_files = [[] for _ in range(3)]
        # chi2_values = [[] for _ in range(3)]
        # chi2_value_averages = []

        # product_six_digit_codes = [
        #     genenerate_six_digit_code("pn", element, f"{mass:03}"),
        #     genenerate_six_digit_code("p2n", element, f"{mass:03}"),
        #     genenerate_six_digit_code("ppn", element, f"{mass:03}"),
        # ]

        # for i, code in enumerate(product_six_digit_codes):
        #     exfortables_directory = os.path.join(
        #         EXFOR_TABLES_PATH,
        #         f"{projectile}",
        #         f"{element.capitalize()}{mass:03}",
        #         "residual",
        #         code,
        #     )
        #     retrieve_external_data(
        #         exfortables_directory,
        #         output_directory,
        #         cleaned_external_files[i],
        #         cleaned_all_external_files[i],
        #         code,
        #         score_dict,
        #     )
        #     # Search for and clean data files for each six-digit code
        #     for j, code in enumerate(product_six_digit_codes):
        #         data_file = search_residual_output(calc_directory, code)
        #         if not data_file:
        #             print(
        #                 f"No 'rp*' files found with the six-digits '{code}' in the directory."
        #             )
        #             continue
        #         cleaned_output_file = os.path.join(
        #             calc_directory, f"cleaned_{os.path.basename(data_file)}"
        #         )
        #         clean_data_file(data_file, cleaned_output_file)
        #         cleaned_output_files[j].append(cleaned_output_file)

        #         simulation_data = load_simulation_data(cleaned_output_file)
        #         combined_chi_squared = calculate_combined_chi_squared(
        #             output_directory,
        #             cleaned_external_files[j],
        #             simulation_data,
        #             ERROR_THRESHOLD,
        #             code,
        #         )
        #         chi2_values[j].append(combined_chi_squared)

        #     chi2_value_average = sum(chi2_values[j][-1] for j in range(3)) / 3.0
        #     chi2_value_averages.append(chi2_value_average)

        # # Plot xs of TALYS calculation and experimental data
        # for j, code in enumerate(product_six_digit_codes):
        #     plot_file = os.path.join(
        #         output_directory, f"combined_cross_section_plot_{code}.png"
        #     )
        #     gnuplot_script = generate_combined_gnuplot_script(
        #         cleaned_output_files[j],
        #         cleaned_external_files[j],
        #         cleaned_all_external_files[j],
        #         plot_file,
        #     )
        #     gnuplot_script_file = os.path.join(
        #         output_directory, f"combined_cross_section_plot_{code}.gp"
        #     )
        #     run_gnuplot(gnuplot_script, gnuplot_script_file)

        # # Plot chi-squared vs m2constant
        # for j, code in enumerate(product_six_digit_codes):
        #     chi_squared_plot_file = os.path.join(
        #         output_directory, f"chi_squared_vs_input_{code}.png"
        #     )
        #     gnuplot_script = generate_chi_squared_gnuplot_script(
        #         chi2_values[j], chi_squared_plot_file
        #     )
        #     gnuplot_script_file = os.path.join(
        #         output_directory, f"chi_squared_vs_input_{j+1}.gp"
        #     )
        #     run_gnuplot(gnuplot_script, gnuplot_script_file)

        # chi_squared_combined_plot_file = os.path.join(
        #     output_directory, f"chi_squared_average_vs_input.png"
        # )
        # gnuplot_script3 = generate_combined_chi_squared_gnuplot_script(
        #     chi2_value_averages, chi_squared_combined_plot_file
        # )
        # gnuplot_script_file3 = os.path.join(
        #     output_directory, "chi_squared_average_vs_input.gp"
        # )
        # run_gnuplot(gnuplot_script3, gnuplot_script_file3)


if __name__ == "__main__":
    main()