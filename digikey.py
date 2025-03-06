# Author: Budianto
# Date: 2025-03-25
# Description: A simple Python script to interact with the Digi-Key API.


import requests
import time
import json

remove_duplicates = lambda lst: list(dict.fromkeys(lst))

class DigiKeyAPI:
    def __init__(self, client_id, client_secret):
        """
        Initializes the DigiKeyAPI instance with the provided client ID and client secret.
        Raises a ValueError if either the client ID or client secret is not provided.
        
        Args:
            client_id (str): The client ID for the Digi-Key API.
            client_secret (str): The client secret for the Digi-Key API.
        """
        if not client_id or not client_secret:
            raise ValueError("CLIENT_ID and CLIENT_SECRET must be provided.")
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = 0
        self.results = None

    def get_access_token(self):
        """
        Retrieves an access token from the Digi-Key API.
        The access token is required for making authenticated requests to the API.
        
        Returns:
            str: The access token.
        """
        url = "https://api.digikey.com/v1/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            token_info = response.json()
            self.access_token = token_info["access_token"]
            # Calculate the expiration time
            expires_in = token_info.get("expires_in", 3600)  # Defaulting to 3600 seconds if not provided
            self.token_expires_at = time.time() 
            print(f"Token acquired at: {time.time()}")
            self.token_expires_at += (expires_in - 20)
            expires_at_formatted = time.strftime('%H:%M:%S', time.localtime(self.token_expires_at))
            print(f"Access token will expire at: {expires_at_formatted}")
            
        else:
            print(f"Error obtaining access token: {response.status_code} - {response.text}")

    def is_token_expired(self):
        return time.time() >= self.token_expires_at

    def ensure_token(self):
        if self.access_token is None or self.is_token_expired():
            self.get_access_token()

    def search_digikey_product_details(self, product_number):
        self.ensure_token()  # Ensure we have a valid token

        url = f"https://api.digikey.com/products/v4/search/{product_number}/productdetails"
        headers = {
            "accept": "application/json",
            "X-DIGIKEY-Client-Id": self.client_id,
            "Authorization": f"Bearer {self.access_token}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            self.results = response.json()
            return response.json()
        elif response.status_code == 429:
            print(f"Error: {response.status_code} - {response.text}")
            return None
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

    def search_by_keyword(self, keyword):
        self.ensure_token()  # Ensure we have a valid token

        url = "https://api.digikey.com/products/v4/search/keyword"
        headers = {
            "accept": "application/json",
            "X-DIGIKEY-Client-Id": self.client_id,
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        body = {
            "Keywords": str(keyword),
        }
        

        response = requests.post(url, headers=headers, data=json.dumps(body))

        if response.status_code == 200:
            self.results = response.json()
            return response.json()
        elif response.status_code == 429:
            print(f"Error (MORE THAN LIMIT): {response.status_code} - {response.text}")
            return None
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    
    def extractHST(self):
        key = "HtsusCode"
        hts = remove_duplicates(self.find_values_by_key(key))
        if hts == None:
            return None
        return [x.replace(".","") for x in hts if x is not None]
        
    def find_values_by_key(self, target_key):
        found_values = []

        def recursive_search(d):
            for key, value in d.items():
                if key == target_key:
                    found_values.append(value)
                if isinstance(value, dict):
                    recursive_search(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            recursive_search(item)

        recursive_search(self.results)
        return found_values


if __name__ == "__main__":
    CLIENT_ID = "[CLIENT_ID]"           # Replace with your actual client ID
    CLIENT_SECRET = "[CLIENT_SECRET]"   # Replace with your actual client secret

    api = DigiKeyAPI(CLIENT_ID, CLIENT_SECRET)

    action = input("Do you want to search by (1) Product Number or (2) Keyword? ")

    if action == "1":
        product_number = input("Enter the product number to search: ")
        results = api.search_digikey_product_details(product_number)
        if results:
            print("Product details found:")
            print(results)

    elif action == "2":
        keyword = input("Enter the keyword to search: ")
        results = api.search_by_keyword(keyword)
        if results:
            print("Search results found:")
            # print(results)
            extractHST = api.extractHST()
            print(extractHST)

    else:
        print("Invalid option selected.")