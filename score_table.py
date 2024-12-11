import os
from glob import glob
import json
from datetime import datetime

from config import SCORE_JSON_PATH
from utils import open_json


def get_latest(evaluations):
    eval_dates = []
    for e in evaluations:
        date_str = e["Date"]
        date_object = datetime.strptime(date_str, "%Y-%m-%d").date()
        eval_dates += [date_object]

    latest = max(eval_dates)

    return evaluations[eval_dates.index(latest)]


def get_score_tables():
    files = glob(os.path.join(SCORE_JSON_PATH, "*.json"))
    score_dict = {}
    # print(files)
    for file in files:
        json_cont = open_json(file)
        # get subentry number
        subent = json_cont["Subentry"]

        # get latest evaluation
        if len(json_cont["Evaluations"]) >= 1:
            latest_eval = get_latest(json_cont["Evaluations"])

        score_dict[subent] = latest_eval["Weight"]

    return score_dict


if __name__ == "__main__":
    score_dict = get_score_tables()
    print(json.dumps(score_dict, indent=1))