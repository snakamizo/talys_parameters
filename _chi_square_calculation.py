import os

def interpolate_simulation(energy_exp, simulation_data):
    """Linearly interpolation"""
    for i in range(1, len(simulation_data)):
        e1, cs1 = simulation_data[i - 1]
        e2, cs2 = simulation_data[i]
        
        if e1 <= energy_exp <= e2:
            return cs1 + (cs2 - cs1) * (energy_exp - e1) / (e2 - e1)
    return None  # If outside the range of simulation data

def calculate_combined_chi_squared(combined_directory, cleaned_external_files, simulation_data, error_threshold, code):

    chi_squared = 0.0
    dataset_chi_squared_list = []
    valid_datasets = 0.0
    output_file_path = os.path.join(combined_directory, f"chi_squared_values_{code}.txt")
    with open(output_file_path, "w") as output_file:
        output_file.write("#File Name\tChi-Squared Value\n")
        for cleaned_external_file in cleaned_external_files:
            experimental_data = load_experimental_data(cleaned_external_file)  # Load the external file
            valid_points = 0.0
            chi_squared_for_dataset = 0.0  # Initialize chi-squared for this dataset

            print(f"\nProcessing file: {cleaned_external_file}")

            for exp_point in experimental_data:
                try:
                    # Try to unpack assuming exp_point is iterable
                    energy_exp, _, cross_section_exp, delta_cross_exp, _ = exp_point
                except TypeError:
                    print(f"Skipping invalid data point in file {cleaned_external_file}: {exp_point}")
                    continue  # Skip to the next point if unpacking fails
                
                if delta_cross_exp < error_threshold * cross_section_exp:
                    print(f"Skipping data point due to small delta_cross_exp (< {error_threshold * 100}% of cross_section) for energy {energy_exp}")
                    continue

                sim_cross_section = interpolate_simulation(energy_exp, simulation_data)
            
                if sim_cross_section is not None and delta_cross_exp > 0:
                    chi_squared_for_dataset += ((cross_section_exp - sim_cross_section) ** 2) / (delta_cross_exp ** 2)
                    valid_points += 1 # Count this point as valid
                else:
                    print(f"Skipping data point due to invalid delta_cross_exp or no simulation match for energy {energy_exp}")

            if valid_points > 0:
                normalized_chi_squared = chi_squared_for_dataset / valid_points
                chi_squared += normalized_chi_squared
                dataset_chi_squared_list.append(normalized_chi_squared)
                valid_datasets += 1
                output_file.write(f"{cleaned_external_file}\t{normalized_chi_squared:.6f}\n")
                print(f"Valid points for {cleaned_external_file}: {valid_points}")
                print(f"Normalized chi-squared for dataset {cleaned_external_file}: {normalized_chi_squared:.6f}")
            else:
                print(f"No valid points in dataset {cleaned_external_file}, skipping normalization.")

    if valid_datasets > 0:
        chi_squared /=valid_datasets
    print("\nChi-squared values for each dataset:", dataset_chi_squared_list)
    print(f"Number of valid datasets: {valid_datasets}") 
    return chi_squared

def load_experimental_data(file_path):
    experimental_data = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('#'):
                continue
            # Split the line into components (assuming they are space-separated)
            data = line.split()
            # Convert each component to a float, and make sure there are 5 columns
            if len(data) == 5:
                experimental_data.append([float(val) for val in data])
            else:
                print(f"Invalid data format in file {file_path}: {line.strip()}")
    return experimental_data

