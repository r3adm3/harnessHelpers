import requests
import os
import json

# Get credentials from environment variables
account_id = os.getenv('HARNESS_ACCT_ID')
api_key = os.getenv('HARNESS_API_TOKEN')

# API endpoint and parameters
url = "https://app.harness.io/gateway/ci/execution-config/get-customer-config"
params = {
    'accountIdentifier': account_id,
    'infra': 'K8',
    'overridesOnly': 'true'
}

# Headers
headers = {
    'X-API-KEY': api_key
}

# Make the GET request
try:
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()  # Raises an HTTPError for bad responses
    
    # Print response with pretty formatting
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2, sort_keys=True))
    
except requests.exceptions.RequestException as e:
    print(f"Error making request: {e}")
except ValueError as e:
    print(f"Error parsing JSON response: {e}")
    print(f"Raw response: {response.text}")