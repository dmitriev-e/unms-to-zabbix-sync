from datetime import datetime

import pandas as pd
from pyzabbix import ZabbixAPI
import os
import logging
from urllib.parse import urlparse
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("zabbix_ip_check.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()


def validate_zabbix_url(url):
    """Validate the Zabbix URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def check_ips_in_zabbix(excel_file, zabbix_url, zabbix_api_key):
    try:
        # Check if file exists
        if not os.path.exists(excel_file):
            logger.error(f"File {excel_file} does not exist.")
            return False

        # Create output filename with timestamp
        filename, ext = os.path.splitext(excel_file)
        timestamp = datetime.now().strftime("%Y%m%d")
        output_file = f"{filename}_result_{timestamp}{ext}"

        # Read Excel file
        logger.info(f"Reading data from {excel_file}")
        df = pd.read_excel(excel_file)

        # Check if ip_address column exists
        if 'ip_address' not in df.columns:
            logger.error("Column 'ip_address' not found in the Excel file.")
            return False

        # Create zabbix column if it doesn't exist
        if 'zabbix' not in df.columns:
            df['zabbix'] = ""

        # Validate Zabbix URL
        if not validate_zabbix_url(zabbix_url):
            logger.error(f"Invalid Zabbix URL: {zabbix_url}")
            return False

        # Connect to Zabbix API
        logger.info(f"Connecting to Zabbix API at {zabbix_url}")
        zapi = ZabbixAPI(zabbix_url)
        zapi.login(api_token=zabbix_api_key)
        logger.info(f"Connected to Zabbix API version {zapi.api_version()}")

        # Get all hosts from Zabbix with selectInterfaces parameter to include interface data
        logger.info("Retrieving hosts from Zabbix")
        hosts = zapi.host.get(
            output=["hostid", "host"],
            selectInterfaces=["interfaceid", "ip"]
        )

        # Create a dictionary of IP addresses for faster lookup
        ip_dict = {}
        for host in hosts:
            print(host)
            if 'interfaces' in host and host['interfaces']:
                for interface in host['interfaces']:
                    if 'ip' in interface and interface['ip']:
                        ip_dict[interface['ip']] = host['host']

        logger.info(f"Retrieved {len(ip_dict)} unique IP addresses from Zabbix")

        # Check each IP in the Excel file
        update_count = 0
        for index, row in df.iterrows():
            ip = str(row['ip_address']).strip()
            if ip:
                if ip in ip_dict:
                    df.at[index, 'zabbix'] = "exist"
                    logger.debug(f"IP {ip} found in Zabbix as host {ip_dict[ip]}")
                    update_count += 1
                else:
                    df.at[index, 'zabbix'] = "not exist"
                    logger.debug(f"IP {ip} not found in Zabbix")

        # Save to a new Excel file
        logger.info(f"Saving results to new file: {output_file}")
        df.to_excel(output_file, index=False)
        logger.info(f"Results saved successfully with {update_count} matched IPs")
        return True

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return False


if __name__ == "__main__":
    # Configuration
    load_dotenv()
    EXCEL_FILE = "device_data_export.xlsx"
    ZABBIX_URL = os.getenv("ZABBIX_SERVER")
    ZABBIX_KEY = os.getenv("ZABBIX_API_KEY")

    logger.info("Starting Zabbix IP check script")
    success = check_ips_in_zabbix(EXCEL_FILE, ZABBIX_URL, ZABBIX_KEY)
    if success:
        logger.info("Script completed successfully")
    else:
        logger.error("Script encountered errors")