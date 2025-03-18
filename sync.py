import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import json
import pandas as pd


def get_unms_devices(base_url, api_key, verify_ssl=False):
    """
    Retrieve all devices from a UNMS/UISP system

    Args:
        base_url (str): The base URL of your UNMS/UISP instance (e.g., 'https://unms.example.com')
        api_key (str): Your UNMS/UISP API key
        verify_ssl (bool): Whether to verify SSL certificates (default: True)

    Returns:
        list: List of devices with their information
    """
    # Ensure base_url doesn't end with a slash
    if base_url.endswith('/'):
        base_url = base_url[:-1]

    # Endpoint for retrieving devices
    endpoint = f"{base_url}/api/v2.1/devices"

    # Set up headers with authentication
    headers = {
        'x-auth-token': api_key,
        'Content-Type': 'application/json'
    }

    try:
        # Make the API request
        response = requests.get(endpoint, headers=headers, verify=verify_ssl)

        # Check if the request was successful
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: Received status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def save_devices_to_file(devices, output_file=None):
    """
    Save the list of devices to a JSON file

    Args:
        devices (list): List of device data
        output_file (str): Path to output file (default: generates a timestamped filename)

    Returns:
        str: Path to the saved file
    """
    if devices is None:
        print("No devices to save")
        return None

    # Generate default filename if none provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"unms_devices_{timestamp}.json"

    # Save devices to file
    with open(output_file, 'w') as f:
        json.dump(devices, f, indent=2)

    print(f"Successfully saved {len(devices)} devices to {output_file}")
    return output_file


def display_device_summary(devices):
    """
    Display a summary of the devices retrieved

    Args:
        devices (list): List of device data
    """
    if devices is None or len(devices) == 0:
        print("No devices found")
        return

    print(f"\nFound {len(devices)} devices:")
    print("-" * 80)
    print(f"{'Name':<30} {'Model':<20} {'IP Address':<15} {'Status':<10}")
    print("-" * 80)

    for device in devices:
        name = device.get('identification', {}).get('name', 'Unknown')
        model = device.get('identification', {}).get('model', 'Unknown')
        ip = device.get('ipAddress', 'N/A')
        status = device.get('status', {}).get('status', 'Unknown')

        print(f"{name[:30]:<30} {model[:20]:<20} {ip:<15} {status:<10}")


def extract_device_data(json_data):
    """Extract specific fields from the JSON data and return as a dictionary."""

    # Extract the requested fields
    extracted_data = {
        "site_name": json_data.get("identification", {}).get("site", {}).get("name"),
        "site_type": json_data.get("identification", {}).get("site", {}).get("type"),
        "mac": json_data.get("identification", {}).get("mac"),
        "name": json_data.get("identification", {}).get("name"),
        "model_name": json_data.get("identification", {}).get("modelName"),
        "role": json_data.get("identification", {}).get("role"),
        "status": json_data.get("overview", {}).get("status"),
        "ip_address": json_data.get("ipAddress", "").split("/")[0] if json_data.get("ipAddress") else None
    }

    return extracted_data


def save_device_data_to_excel():
    # Load the JSON data from a file
    try:
        with open('unms_devices_20250318_192916.json', 'r') as file:
            json_data = json.load(file)
    except FileNotFoundError:
        print("Please save your JSON data to a file named 'device_data.json' in the same directory as this script.")
        return

    # Check if the data is a list or a single object
    if isinstance(json_data, list):
        # Process each item in the list
        extracted_items = [extract_device_data(item) for item in json_data]
    else:
        # Process the single object
        extracted_items = [extract_device_data(json_data)]

    # Create a DataFrame from the extracted data
    df = pd.DataFrame(extracted_items)

    # Save to Excel
    excel_file = 'device_data_export.xlsx'
    df.to_excel(excel_file, index=False)
    print(f"Data successfully exported to {excel_file}")


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Get configuration from .env or command line arguments
    base_url = os.getenv("UNMS_SERVER")
    api_key = os.getenv("UNMS_API_KEY")
    verify_ssl = True

    # Retrieve devices
    print(f"Connecting to UNMS/UISP at {base_url}...")
    # devices = get_unms_devices(base_url, api_key, verify_ssl=verify_ssl)

    # if devices:
        # Display summary
        # display_device_summary(devices)

        # Save to file
        # save_devices_to_file(devices)

    save_device_data_to_excel()
    # else:
    #     print("Failed to retrieve devices.")
