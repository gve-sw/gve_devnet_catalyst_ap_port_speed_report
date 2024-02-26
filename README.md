# GVE DevNet Catalyst AP Port Speed Report
This repository contains the source code of a Python script that can create a report regarding the AP ethernet statistics of a Catalyst WLC. The script connects to the WLC with the Netmiko library, executes the show command 'show ap ethernet statistics', parses the output, and then writes the results to an Excel spreadsheet.

## Contacts
* Danielle Stacy

## Solution Components
* Python 3.11
* Netmiko
* Catalyst WLC
* Catalyst AP
* Excel

## Prerequisites
Configure the environmental variables in the .env file with the appropriate credentials for your network
```python
IP_ADDRESS = "provide IP address here"
USERNAME = "provide ssh username here"
PASSWORD = "provide ssh password here"
```

## Installation/Configuration
1. Clone this repository with the comman: `git clone https://github.com/gve-sw/gve_devnet_catalyst_ap_port_speed_report.git`.
2. Set up a Python virtual environment. Make sure Python 3 is installed in your environment, and if not, you may download Python [here](https://www.python.org/downloads/). Once Python 3 is installed in your environment, you can activate the virtual environment with the instructions found [here](https://docs.python.org/3/tutorial/venv.html).
3. Install the requirements with `pip3 install -r requirements.txt`.

## Usage
To run the script, enter the following command:
```
python report.py
```
Once the code is complete, it will have created a spreadsheet entitled ap_ethernet_statistics.xlsx in the same directory as the code. This will contain the information parsed from the show command.

# Screenshots

![/IMAGES/0image.png](/IMAGES/0image.png)

![/IMAGES/catalyst_ap_speed_report.png](/IMAGES/catalyst_ap_speed_report.png)

### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.
