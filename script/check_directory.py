import json


def check_directory_before_run(file_path):
    try:
        with open(file_path, "r") as file:
            content = file.read()
            print("Raw file content:", repr(content))
            userinputs = json.loads(content)
            print("JSON data loaded successfully:", userinputs)
            return userinputs  # Return the loaded data if needed
    except FileNotFoundError:
        print("Error: File not found.")
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
    except Exception as e:
        print("An unexpected error occurred:", e)
