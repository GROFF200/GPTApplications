# Used to create the config.json used by MonitorStocks.py.  
# Note that this app creates config_new.json, so you'll need to copy the file over manually
# It can cross reference finalreport.txt also, if you choose to do that.  Otherwise it just refreshes existing entries.

import json
import time
import random
import yfinance as yf


def calculate_low_exit_point(entry_point, beta, stock_price):
    if stock_price < 50:
        percentage = 0.95
    elif stock_price < 100:
        percentage = 0.96
    else:
        percentage = 0.97

    if beta > 1:
        percentage -= 0.01

    return entry_point * percentage

def get_user_confirmation(prompt, accept_all_option=False):
    # If accept_all_option is True and the user previously chose 'A', skip the prompt.
    if accept_all_option and get_user_confirmation.all_chosen:
        return True

    response = input(f"{prompt} (Y/N{'/A' if accept_all_option else ''}): ").strip().upper()
    
    if response == 'A' and accept_all_option:
        get_user_confirmation.all_chosen = True
        return True

    return response == 'Y'

def update_config():
    cross_ref = get_user_confirmation("Cross reference finalreport.txt?")

    with open('config.json', 'r') as file:
        config = json.load(file)

    final_report_symbols = {}
    if cross_ref:
        with open('finalreport.txt', 'r') as file:
            for line in file.readlines():
                parts = line.strip().split(': ')
                if len(parts) == 2 and float(parts[1]) >= 5:
                    final_report_symbols[parts[0]] = True


        get_user_confirmation.all_chosen = False
        # Remove symbols not in finalreport.txt if the user agrees
        for symbol in list(config.keys()):
            if symbol not in final_report_symbols and get_user_confirmation(f"Remove {symbol} from config?", True):
                del config[symbol]

        get_user_confirmation.all_chosen = False
        # Add new symbols from finalreport.txt if the user agrees
        for symbol in final_report_symbols:
            if symbol not in config and get_user_confirmation(f"Add {symbol} to config?", True):
                # Initialize with placeholder values
                config[symbol] = {
                    'entry_point': 0,  # These will be updated below
                    'high_exit_point': 0,
                    'low_exit_point': 0
                }

    # Process all stocks, including any new additions
    sorted_config = dict(sorted(config.items()))
    for symbol in sorted_config:
        print(f"Updating {symbol}...")
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            # Print the full content of the info dictionary
            print(f"FULL TICKER INFO for {symbol}:")
            for key, value in info.items():
               print(f"{key}: {value}")
            fifty_day_avg = info.get("fiftyDayAverage", 0)
            two_hundred_day_avg = info.get("twoHundredDayAverage", 0)
            fifty_two_week_high = info.get("fiftyTwoWeekHigh", 0)
            current_price = info.get("currentPrice", 0)
            beta = info.get("beta", 1)

            entry_point = min(fifty_day_avg, two_hundred_day_avg)
            high_exit_point = max(fifty_day_avg, two_hundred_day_avg, fifty_two_week_high * 0.95)
            low_exit_point = calculate_low_exit_point(entry_point, beta, current_price)

            sorted_config[symbol]['entry_point'] = round(entry_point, 2)
            sorted_config[symbol]['high_exit_point'] = round(high_exit_point, 2)
            sorted_config[symbol]['low_exit_point'] = round(low_exit_point, 2)

            sleep_duration = random.randint(15, 45)
            print(f"Sleeping for {sleep_duration} seconds...")
            time.sleep(sleep_duration)
        except Exception as e:
            print(f"An error occurred while updating {symbol}: {e}")

    with open('config_new.json', 'w') as new_file:
        json.dump(sorted_config, new_file, indent=4)

    print("Configuration update completed.")

update_config()
