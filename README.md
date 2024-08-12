# IP Lens CLI Tool

A  lightweight CLI tool designed for fetching and displaying detailed IP address information. **No API keys are required**, making it accessible and easy to use for various use cases.

![IP Lens CLI Tool Screenshot](https://i.ibb.co/0DdXPtt/ksnip-20240812-020344.png)


## Installation

```bash
git clone https://github.com/aiomorphic/iplens.git
cd iplens
pip install -e .
```

## Usage

### CLI Tool

Basic usage:

```bash
iplens 8.8.8.8 1.1.1.1
```

Using an input file:

```bash
iplens --input-file ips.txt
```

The input **file** can be in one of the following formats:

- Plain text file with one IP address per line
- Text file containing a Python list of IP addresses
- JSON file with a list of IP addresses or a dictionary containing a list of IP addresses in any field
- CSV file with a column containing IP addresses (the column name should include "ip", case-insensitive)
- Log file containing IP addresses (the tool will extract unique IP addresses from the log)

Using an Input **Folder** to Parse Files for IP Addresses:

You can also specify a directory, and the tool will parse all non-binary files within that folder to extract IP addresses:

```bash
iplens --input-folder /path/to/logs/
```

Use Cases:

Scan system logs: For example, to scan the UFW log for IP addresses, you can run:

```bash
iplens --input-folder /var/log/ufw.log
```

or for e.g. analyze web server logs: Parse your web server logs to gather and analyze IP addresses.

Save output to a file:

```bash
iplens 8.8.8.8 1.1.1.1 --output results --format json
```

Available options:

- `--input-file` or `-i`: Specify an input file containing IP addresses
- `--input-folder` or `-d`: Specify an input folder containing files to parse for IP addresses
- `--output` or `-o`: Specify output file (without extension)
- `--format` or `-f`: Specify output format (csv or json)

Note: The tool will automatically detect the input file format and extract valid IP addresses. Invalid IP addresses will be ignored.

#### Exports Examples

```json
[
  {
    "ip": "8.8.8.8",
    "rir": "ARIN",
    "is_bogon": "False",
    "is_datacenter": "True",
    "is_tor": "False",
    "is_proxy": "False",
    "is_vpn": "True",
    "is_abuser": "True",
    "company_name": "Google LLC",
    "company_abuser_score": "0.0039 (Low)",
    "company_type": "business",
    "company_domain": "google.com",
    "company_network": "8.8.8.0 - 8.8.8.255",
    "company_whois": "https://api.incolumitas.com/?whois=8.8.8.0",
    "abuse_email": "network-abuse@google.com",
    "asn_asn": "AS15169",
    "asn_abuser_score": "0 (Very Low)",
    "asn_route": "8.8.8.0/24",
    "asn_descr": "GOOGLE, US",
    "asn_country": "us",
    "asn_active": "True",
    "asn_org": "Google LLC",
    "asn_domain": "google.com",
    "asn_abuse": "network-abuse@google.com",
    "asn_type": "business",
    "asn_created": "2000-03-30",
    "asn_updated": "2012-02-24",
    "asn_rir": "ARIN",
    "asn_whois": "https://api.incolumitas.com/?whois=AS15169",
    "location_country": "United States",
    "location_country_code": "US",
    "location_state": "California",
    "location_city": "Sunnyvale",
    "location_latitude": "37.36883",
    "location_longitude": "-122.03635",
    "location_zip": "95196",
    "location_timezone": "America/Los_Angeles"
  }
]
```

```csv
ip,rir,is_bogon,is_datacenter,is_tor,is_proxy,is_vpn,is_abuser,company_name,company_abuser_score,company_type,company_domain,company_network,company_whois,abuse_email,asn_asn,asn_abuser_score,asn_route,asn_descr,asn_country,asn_active,asn_org,asn_domain,asn_abuse,asn_type,asn_created,asn_updated,asn_rir,asn_whois,location_country,location_country_code,location_state,location_city,location_latitude,location_longitude,location_zip,location_timezone
8.8.8.8,ARIN,False,True,False,False,True,True,Google LLC,0.0039 (Low),business,google.com,8.8.8.0 - 8.8.8.255,https://api.incolumitas.com/?whois=8.8.8.0,network-abuse@google.com,AS15169,0 (Very Low),8.8.8.0/24,"GOOGLE, US",us,True,Google LLC,google.com,network-abuse@google.com,business,2000-03-30,2012-02-24,ARIN,https://api.incolumitas.com/?whois=AS15169,United States,US,California,Sunnyvale,37.36883,-122.03635,95196,America/Los_Angeles

```

### As a Python Library

IP Lens can also be utilized as a Python library for direct integration into your Python projects.

```python
from iplens.api import IPInfoAPI

api = IPInfoAPI()
results = api.process(['8.8.8.8', '1.1.1.1'])
```

This will fetch and process the IP information for the given IP addresses. The results will include detailed information such as ASN, location, company details, and more, extracted and formatted for easy access

### Configuration

The API URL, logging level, and other constants can be configured in the config.cfg file. You can modify the configuration file to suit your specific requirements. The available fields and their purposes are defined in the src/config_loader.py.
API Limits

Note that the API has rate limits in its free, unregistered mode. If you encounter a rate limit, simply wait for 20 minutes and then continue using the tool.
Caching

IP Lens includes a caching mechanism to store fetched IP information locally. This helps reduce the number of API calls, especially when processing large lists of IPs. The cache is automatically cleared after a configurable expiration period, which can be set in the config.cfg file.
Ignoring Fields

If there are specific fields you wish to exclude from the output, you can configure this in the src/utils.py file, where the list of field names is defined. This allows you to customize the output based on your needs.

## Development

### Setup

1. Clone the repository
   ```bash
   git clone https://github.com/aiomorphic/iplens.git
   cd iplens
   ```
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
    - Windows: `venv\Scripts\activate`
    - Unix or MacOS: `source venv/bin/activate`
4. Install development dependencies: `pip install -r requirements.txt`

### Pre commit checks

```bash
make pre-commit
```

### Adding New Features

Implement new functionality in the appropriate module under iplens/.
Add tests for the new functionality in tests/.
Update iplens_cli.py if the new feature should be accessible via CLI.
