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

    # Define getters and setters
    def get_fred_api_key(self) -> str:
        return self.fred_api_key
    def set_fred_api_key(self, fred_api_key):
        self.fred_api_key = fred_api_key
    
    def get_fred_base_url(self) -> str:
        return self.fred_base_url
    def set_fred_base_url(self, fred_base_url):
        self.fred_base_url = fred_base_url

    def get_fred_series_all(self):
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
    
    def get_ons_data(self, dataset_id: str, series_id: str) -> pd.DataFrame:
        """Get data from ONS API, return as pandas dataframe
        """

        try:
            # Use ONS API to get monthly data
            url = f'https://api.allorigins.win/raw?url=https://api.ons.gov.uk/timeseries/{series_id}/dataset/{dataset_id}/data'
            # read data at api into dataframe, relevant data is in the 'months' key
            # Make a GET request to fetch the raw JSON content
            json_data = requests.get(url).json()
        except:
            url = 'https://api.ons.gov.uk/timeseries/{series_id}/dataset/{dataset_id}/data'
            json_data = requests.get(url).json()

        # Extract data from the 'months' key
        months_data = json_data['months']

        # Convert the JSON data to a pandas DataFrame
        df = pd.DataFrame.from_dict(months_data)

        # Clean data set, convert date from yyyy mmm to yyyy-mm-dd
        df['date'] = pd.to_datetime(df['date'], format='%Y %b')

        # drop unnecessary columns
        df.drop(columns=['label', 'quarter', 'sourceDataset', 'updateDate'], inplace=True)

        # convert value column to float
        df['value'] = df['value'].astype(float)

        return df
