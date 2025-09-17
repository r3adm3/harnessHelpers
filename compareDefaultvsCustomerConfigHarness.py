import requests
import os
import json
from typing import Dict, Any, Set, Tuple

def get_harness_config(endpoint_type: str) -> Dict[str, Any]:
    """
    Fetch configuration from Harness API
    
    Args:
        endpoint_type: Either 'default' or 'customer'
    
    Returns:
        Dict containing the API response
    """
    account_id = os.getenv('HARNESS_ACCT_ID')
    api_key = os.getenv('HARNESS_API_TOKEN')
    
    if not account_id or not api_key:
        raise ValueError("Environment variables YOUR_HARNESS_ACCOUNT_ID and API_KEY must be set")
    
    base_url = "https://app.harness.io/gateway/ci/execution-config"
    
    if endpoint_type == 'default':
        url = f"{base_url}/get-default-config"
        params = {
            'accountIdentifier': account_id,
            'infra': 'K8'
        }
    elif endpoint_type == 'customer':
        url = f"{base_url}/get-customer-config"
        params = {
            'accountIdentifier': account_id,
            'infra': 'K8',
            'overridesOnly': 'true'
        }
    else:
        raise ValueError("endpoint_type must be 'default' or 'customer'")
    
    headers = {'X-API-KEY': api_key}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {endpoint_type} config: {e}")
        return {}

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten nested dictionary for easier comparison
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for recursion
        sep: Separator for nested keys
    
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                else:
                    items.append((f"{new_key}[{i}]", item))
        else:
            items.append((new_key, v))
    return dict(items)

def compare_configs(default_config: Dict[str, Any], customer_config: Dict[str, Any]) -> None:
    """
    Compare default and customer configurations and display differences
    
    Args:
        default_config: Default configuration response
        customer_config: Customer configuration response
    """
    print("=" * 80)
    print("HARNESS CONFIGURATION COMPARISON")
    print("=" * 80)
    
    # Check if customer config has data
    customer_data = customer_config.get('data', {})
    default_data = default_config.get('data', {})
    
    if not customer_data or customer_data is None:
        print("📋 RESULT: Customer config is using DEFAULT configuration (no overrides)")
        print("\nDefault configuration:")
        print(json.dumps(default_data, indent=2, sort_keys=True))
        return
    
    print("🔍 COMPARISON RESULTS:")
    print("Customer config has overrides. Analyzing differences...\n")
    
    # Flatten both configurations for easier comparison
    flat_default = flatten_dict(default_data)
    flat_customer = flatten_dict(customer_data)
    
    # Find all keys
    all_keys = set(flat_default.keys()) | set(flat_customer.keys())
    
    # Categorize differences
    only_in_default = []
    only_in_customer = []
    different_values = []
    same_values = []
    
    for key in sorted(all_keys):
        default_val = flat_default.get(key, '<NOT_SET>')
        customer_val = flat_customer.get(key, '<NOT_SET>')
        
        if key not in flat_customer:
            only_in_default.append((key, default_val))
        elif key not in flat_default:
            only_in_customer.append((key, customer_val))
        elif default_val != customer_val:
            different_values.append((key, default_val, customer_val))
        else:
            same_values.append((key, default_val))
    
    # Display results
    if different_values:
        print("🔄 OVERRIDDEN VALUES:")
        print("-" * 50)
        for key, default_val, customer_val in different_values:
            print(f"Key: {key}")
            print(f"  Default:  {default_val}")
            print(f"  Customer: {customer_val}")
            print()
    
    if only_in_customer:
        print("➕ CUSTOMER-ONLY SETTINGS:")
        print("-" * 50)
        for key, val in only_in_customer:
            print(f"Key: {key}")
            print(f"  Value: {val}")
            print()
    
    if only_in_default:
        print("➖ DEFAULT-ONLY SETTINGS (not overridden):")
        print("-" * 50)
        for key, val in only_in_default:
            print(f"Key: {key}")
            print(f"  Value: {val}")
            print()
    
    if same_values:
        print(f"✅ UNCHANGED VALUES: {len(same_values)} settings match between default and customer config")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"  🔄 Overridden values: {len(different_values)}")
    print(f"  ➕ Customer-only settings: {len(only_in_customer)}")
    print(f"  ➖ Default-only settings: {len(only_in_default)}")
    print(f"  ✅ Unchanged values: {len(same_values)}")

def main():
    """Main function to orchestrate the comparison"""
    print("Fetching Harness configurations...")
    
    # Fetch both configurations
    print("📥 Fetching default config...")
    default_config = get_harness_config('default')
    
    print("📥 Fetching customer config...")
    customer_config = get_harness_config('customer')
    
    if not default_config or not customer_config:
        print("❌ Failed to fetch one or both configurations. Please check your credentials and network connection.")
        return
    
    # Compare configurations
    compare_configs(default_config, customer_config)

if __name__ == "__main__":
    main()