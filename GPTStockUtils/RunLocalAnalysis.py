# Goes through the entire S&P 500 and uses Yahoo Finance Data information to determine if stocks might be a good purchase.
# Alapaca Market API is also used to get historical market data and sentiment analysis.
# If a stock passes the first set of checks, then GPT is used to give an analysis and a score which is saved to a text file.

import requests
import json
import datetime
import re
import os
import glob
import shutil
from openai import OpenAI
from pathlib import Path
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import yfinance as yf
import random
import time
import csv

url = 'https://data.alpaca.markets/v1beta1/news'
api_key = '<key here>'
api_secret = '<key here>'

# Initialize Alpaca StockHistoricalDataClient
alpacaClient = StockHistoricalDataClient(api_key, api_secret)

# Initialize OpenAI client
client = OpenAI(api_key="<key here>")

# Global variable to keep track of the number of requests
request_counter = 0

#Use GPT if true, or the LocalLLM instance if false
useGPT = True

def parse_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        stock_dict = {}
        for row in reader:
            try:
                exchange, ticker = row['Exchange:Ticker'].split(':')
                if exchange not in ['NYSE', 'NASDAQ', 'NasdaqGS', 'NasdaqCM']:
                    continue
            except ValueError:
                continue
            industry = row['Industry Group']
            sector = row['Primary Sector']
            stock_dict[ticker] = {'Industry': industry, 'Sector': sector}
        return stock_dict

def parse_pedata_file(filename):
    with open(filename, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        pe_data_dict = {}
        for row in reader:
            row = {key.strip('\ufeff'): value for key, value in row.items()}
            try:
                industry = row['Industry Name']
                pe_data_dict[industry] = {
                    'Number of Firms': row['Number of firms'],
                    'Percent of Money Losing Firms': row['% of Money Losing firms (Trailing)'],
                    'Current PE': row['Current PE'],
                    'Trailing PE': row['Trailing PE'],
                    'Forward PE': row['Forward PE'],
                    'Aggregate Market Cap / Net Income (All Firms)': row['Aggregate Mkt Cap/ Net Income (all firms)'],
                    'Aggregate Market Cap / Trailing Net Income (Only Money Making Firms)': row['Aggregate Mkt Cap/ Trailing Net Income (only money making firms)'],
                    'Expected Growth - Next 5 Years': row['Expected growth - next 5 years'],
                    'PEG Ratio': row['PEG Ratio']
                }
            except KeyError as e:
                print(f"KeyError: {e} - this key was not found in the row: {row}")
                continue
        return pe_data_dict

def get_stock_symbols(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip().split(',')

def fetch_news(api_key, api_secret, url, symbol):
    headers = {'Apca-Api-Key-Id': api_key, 'Apca-Api-Secret-Key': api_secret}
    response = requests.get(url + '?symbols=' + symbol, headers=headers)
    news = json.loads(response.text)['news']
    return ' '.join([news_item['headline'] + ": " + news_item['summary'] for news_item in news])

def fetch_market_data(symbol):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=14)
    request_params = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Day, start=start_date, end=end_date)
    stock_bars = alpacaClient.get_stock_bars(request_params).df
    return ' '.join([f"{row.name[1].strftime('%Y-%m-%d')}: Open={row['open']}, High={row['high']}, Low={row['low']}, Close={row['close']}, Volume={row['volume']}" for _, row in stock_bars.iterrows()])

def fetch_finance_data(symbol):
    global request_counter  # Use the global request counter

    # Increment the request counter
    request_counter += 1

    # Sleep after every two requests
    if request_counter > 4:
        sleep_time = random.randint(10, 45)
        print(f"Sleeping for {sleep_time} seconds to avoid rate limiting...")
        request_counter = 0
        time.sleep(sleep_time)

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        key_data = {
              "Symbol": info.get("symbol"),
              "Current Price": info.get("currentPrice"),
              "Previous Close": info.get("previousClose"),
              "Open": info.get("open"),
              "Day's Range": f"{info.get('dayLow')} - {info.get('dayHigh')}",
              "52 Week Range": f"{info.get('fiftyTwoWeekLow')} - {info.get('fiftyTwoWeekHigh')}",
              "Volume": info.get("volume"),
              "Average Volume": info.get("averageVolume"),
              "Market Cap": info.get("marketCap"),
              "Beta": info.get("beta"),
              "PE Ratio (TTM)": info.get("trailingPE"),
              "EPS (TTM)": info.get("trailingEps"),
              "Dividend & Yield": f"{info.get('dividendRate')} ({info.get('dividendYield')})",
              "50-Day Moving Average": info.get("fiftyDayAverage"),
              "200-Day Moving Average": info.get("twoHundredDayAverage"),
              "Earnings Date": info.get("earningsDate"),
              "Forward Dividend & Yield": f"{info.get('forwardDividendRate')} ({info.get('forwardDividendYield')})",
              "Ex-Dividend Date": info.get("exDividendDate"),
              "1y Target Est": info.get("targetMeanPrice"),
              "Current Ratio": info.get("currentRatio"),
              "EPS Growth": info.get("earningsGrowth"),
              "Institutional Ownership": info.get("heldPercentInstitutions"),
              "Total Debt": info.get("totalDebt"),
              "Total Cash": info.get("totalCash"),
              "Earnings Quarterly Growth": info.get("earningsQuarterlyGrowth"),
              "Revenue Growth": info.get("revenueGrowth"),
              "Price to Sales": info.get("priceToSalesTrailing12Months"),
              "Enterprise to EBITDA": info.get("enterpriseToEbitda"),
              "Held Percent Insiders": info.get("heldPercentInsiders"),
              "Overall Risk": info.get("overallRisk"),
        }
        # Format the extracted data into a string for the prompt
        stock_data_str = ', '.join([f"{key}: {value}" for key, value in key_data.items()])
        print("YF INFO: "+stock_data_str)
        key_data = {key: info.get(key) for key in ['currentPrice', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'volume', 'averageVolume', 'marketCap', 'beta', 'trailingPE', 'trailingEps', 'dividendRate', 'dividendYield', 'fiftyDayAverage', 'twoHundredDayAverage', 'earningsDate', 'forwardDividendRate', 'forwardDividendYield', 'exDividendDate', 'targetMeanPrice', 'currentRatio', 'earningsGrowth','heldPercentInstitutions','totalDebt','totalCash','earningsQuarterlyGrowth','revenueGrowth','priceToSalesTrailing12Months','enterpriseToEbitda','heldPercentInsiders','overallRisk']}
        return ', '.join([f"{key}: {value}" for key, value in key_data.items()])
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error encountered: {e}. Retrying...")
        return fetch_finance_data(symbol)  # Retry fetching data
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def send_request_to_server(system_prompt, user_prompt):
    server_url = "http://127.0.0.1:8080/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    response = requests.post(server_url, headers=headers, data=json.dumps({"model": "mistral", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]}))
    response_json = response.json()
    return response_json['choices'][0]['message']['content'] if 'choices' in response_json and response_json['choices'] else "No response"



def parse_finance_data(finance_data_str):
    data_dict = {}
    for item in finance_data_str.split(', '):
        key, value = item.split(': ', 1)
        data_dict[key] = value
    return data_dict

def safe_float_conversion(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int_conversion(value, default=0):
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default

def get_gpt_response(system_prompt, user_prompt):
    max_retries = 3
    retry_delay = 10  # seconds
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                #model="gpt-4-1106-preview",
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Moving to the next stock.")
    return None

def analyze_stock(symbol, stock_dict, pe_data_dict):
    print("Fetching finance data...")
    finance_data_str = fetch_finance_data(symbol)
    print("FINANCE DATA: "+finance_data_str)
    finance_data = parse_finance_data(finance_data_str)

    # Convert to float if the value is not 'None', an empty string, or None
    current_price_str = finance_data.get("currentPrice", "0")
    pe_ratio_str = finance_data.get("trailingPE", "0");
    market_cap_str = finance_data.get("marketCap", "0")
    beta_str = finance_data.get("beta", "0")

    current_price = safe_float_conversion(finance_data.get("currentPrice", "0"))
    pe_ratio = safe_float_conversion(finance_data.get("trailingPE", "0"))
    market_cap = safe_float_conversion(finance_data.get("marketCap", "0"))
    beta = safe_float_conversion(finance_data.get("beta", "0"))

    total_debt = safe_float_conversion(finance_data.get("totalDebt", "0"))
    total_cash = safe_float_conversion(finance_data.get("totalCash", "0"))
    earnings_growth_q = safe_float_conversion(finance_data.get("earningsQuarterlyGrowth", "0"))
    revenue_growth = safe_float_conversion(finance_data.get("revenueGrowth", "0"))
    enterprise_to_ebitda = safe_float_conversion(finance_data.get("enterpriseToEbitda", "0"))
    held_percent_insiders = safe_float_conversion(finance_data.get("heldPercentInsiders", "0").strip('%'), 0.0) / 100
    overall_risk = safe_int_conversion(finance_data.get("overallRisk", 0))
 
    #------------
    # Get the industry mappings from here:
    # https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/pedata.html
    #------------

    # Skip if current price is below threshold
    if current_price < 25:
        print(f"Skipping {symbol}: Current price {current_price} below threshold.")
        return

    industry_used_for_pe = False

    # Getting industry information
    if symbol in stock_dict:
        industry = stock_dict[symbol].get('Industry')
        if industry and industry in pe_data_dict:
            industry_pe = safe_float_conversion(pe_data_dict[industry].get("Trailing PE", "0"))
            if industry_pe > 0:  # Valid industry PE found
                print(f"{symbol} is in the {industry} industry with an industry P/E of {industry_pe}.")
                if pe_ratio > industry_pe * 1.5:  # Adjust multiplier as needed
                    print(f"Skipping {symbol}: P/E Ratio {pe_ratio} is high compared to the industry average of {industry_pe}.")
                    return
                industry_used_for_pe = True
            else:
                print(f"Industry P/E data not available or invalid for {industry}. Falling back to general P/E check.")
        else:
            print(f"Industry P/E data not found for {industry}. Proceeding with general P/E check.")
    else:
        print(f"Industry data not found for {symbol}. Proceeding with general P/E check.")

    # Fall back to general P/E ratio check if industry-specific check wasn't applicable
    if not industry_used_for_pe and (pe_ratio < 10 or pe_ratio > 26):
        print(f"Skipping {symbol}: P/E Ratio {pe_ratio} out of desired range.")
        return

    if industry_used_for_pe:
        percent_money_losing_firms = safe_float_conversion(pe_data_dict[industry].get('Percent of Money Losing Firms', '0'), 0.0)
        if percent_money_losing_firms > 50:  # Threshold can be adjusted
             print(f"Skipping {symbol}: Over {percent_money_losing_firms}% of firms in the industry are losing money.")
             return

        # Checking PEG Ratio if industry PEG is not available
        general_peg_ratio = safe_float_conversion(finance_data.get("PEG Ratio", "0"))
        if general_peg_ratio > 2:  
            print(f"Skipping {symbol}: High PEG Ratio {general_peg_ratio}.")
            return

    if industry_used_for_pe and "Enterprise to EBITDA" in pe_data_dict[industry]:
        industry_ebitda_ratio = safe_float_conversion(pe_data_dict[industry].get("Enterprise to EBITDA", "0"))
        if enterprise_to_ebitda > industry_ebitda_ratio * 1.5:  # Adjust based on context
            print(f"Skipping {symbol}: EV/EBITDA ratio {enterprise_to_ebitda} is high compared to the industry average.")
            return

    # Checking for revenue growth 
    revenue_growth = safe_float_conversion(finance_data.get("revenueGrowth", "0"))
    if revenue_growth < 0:  
        print(f"Skipping {symbol}: Negative revenue growth {revenue_growth}.")
        return

    # Skip based on Market Cap
    if market_cap < 1000000000:  # $1 billion
        print(f"Skipping {symbol}: Market Cap {market_cap} below threshold.")
        return

    # Skip based on Beta
    if beta > 2:
        print(f"Skipping {symbol}: Beta {beta} too high.")
        return

    #Skip if current debt ratio is too high
    current_ratio_str = finance_data.get("currentRatio", "0")
    current_ratio = safe_float_conversion(current_ratio_str, 0.0)
    if current_ratio < .9:  # Example threshold
        print(f"Skipping {symbol}: Current Ratio {current_ratio} is below threshold.")
        return

    #Skip if profits aren't increasing
    eps_growth_str = finance_data.get("earningsGrowth", "0")
    eps_growth = safe_float_conversion(eps_growth_str, 0.0)
    if eps_growth <= 0:  # Looking for positive growth
        print(f"Skipping {symbol}: EPS Growth {eps_growth} is not positive.")
        return

    #Skip if too many hedge fund managers own it as their goals don't align with mine
    institutional_ownership_str = finance_data.get("heldPercentInstitutions", "0").replace('%', '')
    institutional_ownership = safe_float_conversion(institutional_ownership_str, 0.0) / 100
    if institutional_ownership > 0.75:  # Example threshold, adjust based on your strategy
       print(f"Skipping {symbol}: Institutional Ownership {institutional_ownership} is very high.")
       return

    if total_debt > 2 * total_cash:
       print(f"Skipping {symbol}: High debt level compared to cash.")
       return

    if earnings_growth_q <= 0 and revenue_growth <= 0:
       print(f"Skipping {symbol}: Negative earnings and revenue growth.")
       return
    
    if overall_risk > 5:
        print(f"Skipping {symbol}: High overall risk.")
        return

    # Fetch sentiment and market data
    sentiment_data = fetch_news(api_key, api_secret, url, symbol)
    print("SENTIMENT DATA: "+sentiment_data)
    market_data = fetch_market_data(symbol)
    print("MARKET DATA: "+market_data)
    responseText = ""
    # Prepare the analysis request
    if useGPT:
        system_prompt = Path('prompts/GPT-system-prompt.txt').read_text(encoding='utf-8')
        print("System_prompt: "+system_prompt)
        user_prompt_template = Path('prompts/GPT-user-prompt.txt').read_text(encoding='utf-8')
        print("GPT prompt template: "+user_prompt_template)
        print ("sentiment_data: "+sentiment_data)
        print("market_data: "+market_data)
        print("finance_data: "+finance_data_str)
        user_prompt = user_prompt_template.format(
            sentiment=sentiment_data, market=market_data, finance=finance_data_str, symbol=symbol
        )
        print("Sending to GPT: "+user_prompt)
        print("Sending to GPT: " + user_prompt.encode('utf-8', 'ignore').decode('utf-8'))
        responseText = get_gpt_response(system_prompt, user_prompt)
    else:
        system_prompt = Path('prompts/local-system-prompt.txt').read_text()
        user_prompt = Path('prompts/local-analysis-prompt.txt').read_text().format(
            sentiment=sentiment_data, market=market_data, finance=finance_data, symbol=symbol
        )
        response = send_request_to_server(system_prompt, user_prompt)
        responseText = response

    print("RESPONSE: "+responseText)
    # Log and save the response
    timestamp = datetime.now().strftime("%m%d%Y%H%M")
    output_dir = Path(f"stockinfo/{'gptanalysis' if useGPT else 'localllmanalysis'}/{symbol}")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{symbol}-info.txt.{timestamp}"
    output_path.write_text(responseText, encoding='utf-8')
    return responseText


def copy_file(source, destination):
    shutil.copy(source, destination)
    print(f"Copied {source} to {destination}")

def main():
    if (useGPT):
         print("Using GPT for analysis...")
    #Getting P/E data for industry
    stock_dict = parse_file('indname.csv')
    pe_data_dict = parse_pedata_file('pedata.csv')
    list_dir = "lists"
    main_stocks_file = "stocks.txt"
    stock_files = sorted(glob.glob(os.path.join(list_dir, "stocks-*.txt")))
    for stock_file in stock_files:
        copy_file(stock_file, main_stocks_file)

        stock_symbols = get_stock_symbols(main_stocks_file)
        for symbol in stock_symbols:
            print(f"Analyzing stock: {symbol}")
            analysis_response = analyze_stock(symbol.strip(), stock_dict, pe_data_dict)

    print("All stocks have been processed.")



if __name__ == "__main__":
    main()
