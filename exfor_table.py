import os
import re


def extract_code_from_filename(filename):
    # Get the base name of the file
    base_name = os.path.basename(filename)

    # Split by hyphens
    parts = base_name.split("-")

    # Ensure we have enough parts
    if len(parts) < 4:  # We expect at least four parts for a valid filename
        print(
            f"Could not extract code from file: {filename} - filename format is unexpected."
        )
        return None

    # Get the last part, which may contain the code
    last_part = parts[-1]

    # Remove any file extensions (if present)
    last_part = last_part.split(".")[0]  # Take the part before the first dot

    # Check if the last part is a valid code (8 or 9 alphanumeric characters)
    if re.match(r"^[A-Za-z0-9]{8,9}$", last_part):
        return last_part

    print(
        f"Could not extract code from file: {filename} - last part '{last_part}' is not valid."
    )
    return None

