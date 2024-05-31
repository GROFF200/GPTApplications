#Reads the GPT analysis data and writes the entries to finalreport.txt in descending order

import json
import glob
import os
import re
from datetime import datetime

def extract_json_score(text):
    # Updated regex pattern to match the entire JSON object with the "result" key
    json_matches = re.findall(r'\{.*?"result"\s*:\s*([\d.]+).*?\}', text, re.DOTALL)
    
    if json_matches:
        # Taking the last match since you want the last occurrence of the score
        last_match = json_matches[-1]
        try:
            # Constructing the JSON string from the last match
            json_str = '{"result": ' + last_match + '}'
            json_data = json.loads(json_str)
            return json_data.get("result")
        except json.JSONDecodeError:
            print(f"JSON decode error in file: {text[:100]}")  # Showing first 100 characters for context
            return None
    return None



def read_score_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        return extract_json_score(content)

def find_most_recent_file(files):
    # Sort the files based on the timestamp in their filenames
    sorted_files = sorted(files, key=extract_timestamp, reverse=True)
    # Return the last file in the sorted list, which should be the most recent one with a valid timestamp
    return sorted_files[-1] if sorted_files else None

def extract_timestamp(file):
    basename = os.path.basename(file)  # Get the basename of the file
    timestamp_str = os.path.splitext(basename)[0].split('-info.txt.')[-1]  # Extract the timestamp part
    try:
        return datetime.strptime(timestamp_str, "%m%d%Y%H%M")  # Convert to datetime object
    except ValueError:
        # If parsing fails, return a default datetime far in the past
        return datetime.min


def generate_report(stockinfo_dir, report_file):
    stock_scores = {}

    # Iterate over each symbol's directory
    for symbol_dir in glob.glob(f'{stockinfo_dir}/gptanalysis/*'):
        symbol = os.path.basename(symbol_dir)
        files = glob.glob(f'{symbol_dir}/{symbol}-info.txt.*')
        most_recent_file = find_most_recent_file(files)

        if most_recent_file:
            print(f"Reading file for symbol: {symbol}, path: {most_recent_file}")  # Debugging
            score = read_score_from_file(most_recent_file)
            print(f"Extracted score for {symbol}: {score}")  # Debugging
            if score is not None:
                stock_scores[symbol] = score

    # Sort stocks based on score
    sorted_stocks = sorted(stock_scores.items(), key=lambda x: x[1], reverse=True)

    # Write report
    with open(report_file, 'w') as report:
        report.write("Stocks Ranked from Highest to Lowest:\n")
        for symbol, score in sorted_stocks:
            report.write(f"{symbol}: {score}\n")

# Update the path to the stockinfo directory and report file name as needed
generate_report('stockinfo', 'finalreport.txt')
