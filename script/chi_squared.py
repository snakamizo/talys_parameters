import os
import numpy as np
import logging

from config import XS_THRESHOLD_PERCENTAGE, ERROR_THRESHOLD


def interpolate_simulation(energy_exp, simulation_data):
    """Linearly interpolation"""
    logging.debug(
        f"Interpolating for energy: {energy_exp} with simulation data: {simulation_data[:5]}..."
    )
    for i in range(1, len(simulation_data)):
        e1, cs1 = simulation_data[i - 1]
        e2, cs2 = simulation_data[i]

        if e1 <= energy_exp <= e2:
            result = cs1 + (cs2 - cs1) * (energy_exp - e1) / (e2 - e1)
            logging.debug(f"Interpolated value: {result} for range ({e1}, {e2})")
            return result
    logging.warning(f"No interpolation match for energy: {energy_exp}")
    return None  # If outside the range of simulation data


def calculate_combined_chi_squared(
    output_directory,
    cleaned_external_files,
    simulation_data,
    code,
    projectile,
    target,
    i,
    cross_section_sim_max,
):
    chi_squared = 0.0
    dataset_chi_squared_list = []
    valid_datasets = 0.0
    output_file_path = os.path.join(
        output_directory,
        f"chi_squared_values_{projectile}-{target[1]}{target[0]}{code}_{i}.txt",
    )

    logging.debug(
        f"Starting chi-squared calculation for {len(cleaned_external_files)} files."
    )
    logging.debug(f"Simulation data: {simulation_data[:5]}")

    with open(output_file_path, "w") as output_file:
        output_file.write("#File Name\tChi-Squared Value\n")
        for cleaned_external_file in cleaned_external_files:
            logging.debug(
                f"Loading experimental data from file: {cleaned_external_file}"
            )
            experimental_data = load_experimental_data(cleaned_external_file)
            logging.debug(
                f"Experimental data points loaded: {len(experimental_data)} from {cleaned_external_file}"
            )
            valid_points = 0.0
            chi_squared_for_dataset = 0.0

            logging.info(f"\nProcessing file: {cleaned_external_file}")

            for exp_point in experimental_data:
                try:
                    # Try to unpack assuming exp_point is iterable
                    energy_exp, _, cross_section_exp, delta_cross_exp, _ = exp_point
                except TypeError:
                    logging.info(
                        f"Skipping invalid data point in file {cleaned_external_file}: {exp_point}"
                    )
                    continue  # Skip to the next point if unpacking fails
                logging.debug(f"Evaluating experimental point: {exp_point}")

                if (
                    delta_cross_exp < ERROR_THRESHOLD * cross_section_exp
                    or cross_section_exp
                    < XS_THRESHOLD_PERCENTAGE * 0.01 * cross_section_sim_max
                ):
                    logging.info(
                        f"Skipping data point due to small delta_cross_exp (< {ERROR_THRESHOLD * 100}% of cross_section) for energy {energy_exp} or the cross section value under {XS_THRESHOLD_PERCENTAGE} * 0.01 * {cross_section_sim_max}"
                    )
                    continue

                sim_cross_section = interpolate_simulation(energy_exp, simulation_data)

                if sim_cross_section is not None and delta_cross_exp > 0:
                    chi_squared_for_dataset += (
                        (cross_section_exp - sim_cross_section) ** 2
                    ) / (delta_cross_exp**2)
                    valid_points += 1  # Count this point as valid
                else:
                    logging.info(
                        f"Skipping data point due to invalid delta_cross_exp or no simulation match for energy {energy_exp}"
                    )

            if valid_points > 0:
                normalized_chi_squared = chi_squared_for_dataset / valid_points
                chi_squared += normalized_chi_squared
                dataset_chi_squared_list.append(normalized_chi_squared)
                valid_datasets += 1
                output_file.write(
                    f"{os.path.basename(cleaned_external_file)}\t{normalized_chi_squared:.6f}\n"
                )
                logging.info(
                    f"Valid points for {cleaned_external_file}: {valid_points}"
                )
                logging.info(
                    f"Normalized chi-squared for dataset {cleaned_external_file}: {normalized_chi_squared:.6f}"
                )
            else:
                logging.info(
                    f"No valid points in dataset {cleaned_external_file}, skipping normalization."
                )

    if valid_datasets > 0:
        chi_squared /= valid_datasets
    logging.info(f"Chi-squared values for each dataset: {dataset_chi_squared_list}")
    logging.info(f"Number of valid datasets: {valid_datasets}")
    logging.debug(
        f"Final combined chi-squared: {chi_squared}, from {valid_datasets} datasets."
    )
    return chi_squared


def load_simulation_data(file_path):
    logging.debug(f"Loading simulation data from {file_path}")
    try:
        data = np.loadtxt(file_path, usecols=(0, 1))
        logging.debug(f"Simulation data loaded: {data[:5]} (first 5 rows)")
        return data
    except Exception as e:
        logging.error(f"Failed to load simulation data from {file_path}: {e}")
        return []


def load_experimental_data(file_path):
    experimental_data = []
    logging.debug(f"Loading experimental data from {file_path}")
    with open(file_path, "r") as file:
        for line in file:
            if line.startswith("#"):
                continue
            # Split the line into components (assuming they are space-separated)
            data = line.split()
            if len(data) == 5:
                experimental_data.append([float(val) for val in data])
            else:
                logging.warning(
                    f"Invalid format at {line} in {file_path}: {line.strip()}"
                )

    return experimental_data
