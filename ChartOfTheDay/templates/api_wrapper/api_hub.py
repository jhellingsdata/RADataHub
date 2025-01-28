import requests
import urllib.parse
import pandas as pd
from typing import Optional

############## For Importing ##############
# To import this file, use the following code:

# import sys, importlib
# # Option 1. Append absolute path to folder holding api_wrapper
# absolute_path_to_api_wrapper = "/Users/joshhellings/Documents/ECO/RADataHub/ChartOfTheDay/templates/api_wrapper/"
# sys.path.append(absolute_path_to_api_wrapper)

# # # Option 2. Append relative path
# # sys.path.append('../api_wrapper/')

# from api_hub import DataAPI

############################################

class EconDataAPI:
    def __init__(self):
        self.fred_api_key = '838a40e4f5a37b6b4d8c9cfc4b1abaff'
        self.fred_base_url = 'https://api.stlouisfed.org/fred/series/observations'

        self.fred_series = {
            "cpi": {
                "name": "Consumer Price Index for All Urban Consumers: All Items in U.S. City Average",
                "id": "CPIAUCSL",
                "frequency": "Monthly",
                "units": "Index 1982-1984=100, Seasonally Adjusted",
            },
            "fed_rate": [{
                "name": "Federal Funds Effective Rate",
                "id": "DFF",
                "frequency": "Daily, 7-Day",
                "units": "Percent, Not Seasonally Adjusted",
            }, {
                "name": "Federal Funds Effective Rate",
                "id": "FEDFUNDS",
                "frequency": "Monthly",
                "units": "Percent, Not Seasonally Adjusted",
            }, {
                "name": "Federal Funds Target Range - Upper Limit",
                "id": "DFEDTARU",
                "frequency": "Daily, 7-Day",
                "units": "Percent, Not Seasonally Adjusted",
            }]
        }

        self.quarters_lookup = {
            'Q1': '01-01',
            'Q2': '04-01',
            'Q3': '07-01',
            'Q4': '10-01',
            'q1': '01-01',
            'q2': '04-01',
            'q3': '07-01',
            'q4': '10-01'
        }

    # Define getters and setters
    def get_fred_api_key(self) -> str:
        '''Returns API key set for FRED.'''
        return self.fred_api_key
    def set_fred_api_key(self, fred_api_key):
        '''Update currently stored API key for FRED.

        Args:
            fred_api_key: Active API key to use when downloading FRED data. Find out more at https://fred.stlouisfed.org/docs/api/api_key.html
        '''
        self.fred_api_key = fred_api_key
    
    def get_fred_base_url(self) -> str:
        return self.fred_base_url
    def set_fred_base_url(self, fred_base_url):
        self.fred_base_url = fred_base_url

    def get_fred_series_all(self) -> list:
        '''Returns a list of previously saved series codes for FRED.'''
        return self.fred_series.keys()

    # return type either dict or list of dicts
    def get_fred_series(self, series: str) -> Optional[dict]:
        return self.fred_series[series]
        
    def _fetch_data(self, api_query_url: str):
        # Generic method to fetch data given a URL
        response = requests.get(api_query_url)
        return response.json()
        
    def get_fred_data(self, series):
        params = {
            'series_id': series,
            'api_key': self.fred_api_key,
            'file_type': 'json',
        }
        encoded_params = urllib.parse.urlencode(params)
        api_query_url = f"https://api.allorigins.win/raw?url={urllib.parse.quote(self.fred_base_url + '?' + encoded_params)}"
        
        data = self._fetch_data(api_query_url)
        
        # Extract data from the 'observations' key
        observations_data = data['observations']
        
        df = pd.DataFrame.from_dict(observations_data)
        df.drop(columns=['realtime_start', 'realtime_end'], inplace=True, errors='ignore')

        # Enforce column types
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = df['value'].astype(float)
        # Add column with just year in yyyy format
        df['year'] = df['date'].dt.year
        
        return df
    
    def get_ons_data(self, series_id: str, time_period: str) -> pd.DataFrame:
        """Get data from ONS API, return as pandas dataframe

        Args:
            dataset_id (str): The dataset ID (no longer needed)
            series_id (str): The series ID
            time_period (str): The time period to retrieve data for. Options are 'm' for monthly, 'q' for quarterly, and 'y' for yearly.
        """

        try:
            # Use ONS API to get monthly data
            # url = f'https://eco-cors-proxy.netlify.app/proxy?url=https://api.ons.gov.uk/timeseries/{series_id}/dataset/{dataset_id}/data'
            url = f'https://eco-cors-proxy.netlify.app/proxy?url=https://economicsobservatory.github.io/api/ons.html?code={series_id}&format=json&data_only=true'
            # read data at api into dataframe, relevant data is in the 'months' key
            # Make a GET request to fetch the raw JSON content
            response = requests.get(url)
            json_data = response.json()
        except:
            print('Failed to make API call')
            return response.status_code, response.text
            # url = f'https://api.ons.gov.uk/timeseries/{series_id}/dataset/{dataset_id}/data'
            # json_data = requests.get(url).json()
        time_period = time_period.lower()
        if time_period == 'm':
            # Extract data from the 'months' key
            series_data = json_data['months']
            # Convert the JSON data to a pandas DataFrame
            df = pd.DataFrame.from_dict(series_data)
            # Clean data set, convert date from yyyy mmm to yyyy-mm-dd
            df['date'] = pd.to_datetime(df['date'], format='%Y %b')
            # drop unnecessary columns
            df.drop(columns=['label', 'quarter', 'sourceDataset', 'updateDate'], inplace=True)

        elif time_period == 'q':
            # Extract data from the 'quarters' key
            series_data = json_data['quarters']
            df = pd.DataFrame.from_dict(series_data)

            # Replace string in `date` according to the lookup
            df['year'] + df['quarter'].map(self.quarters_lookup)

        elif time_period == 'y':
            # Extract data from the 'years' key
            series_data = json_data['years']
            df = pd.DataFrame.from_dict(series_data)
        
        # convert value column to float
        df['value'] = df['value'].astype(float)

        return df
