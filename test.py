import json
from score_table import get_score_tables  # Assuming get_score_tables is in score_table.py

def main():
    # Retrieve score_dict using get_score_tables function
    score_dict = get_score_tables()
    
    # Print the score_dict in a formatted JSON style for readability
    print("Score Dictionary Contents:")
    print(json.dumps(score_dict, indent=2))

if __name__ == "__main__":
    main()