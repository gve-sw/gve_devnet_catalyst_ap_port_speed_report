#!/usr/bin/env python3
"""
Copyright (c) 2024 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
from netmiko import ConnectHandler
import pandas as pd
from dotenv import load_dotenv
import os
import sys
import json
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from pprint import pprint


def connect_to_wlc(ip, user, password):
    """
    Connect to WLC with the user provided IP address, username, and password
    Then send the show command 'show ap ethernet statistics' and save the output
    in the variable ap_ethernet_stats
    :return: string containing the output from the show command
    """
    wlc = {
        "device_type": "cisco_ios",
        "host": ip,
        "username": user,
        "password": password
        }

    with ConnectHandler(**wlc) as wlc_connect:
        hostname = wlc_connect.find_prompt()[:-1]
        try:
            ap_ethernet_stats = wlc_connect.send_command("show ap ethernet statistics")
        except Exception as e:
            print(e)

            return None, hostname

    return ap_ethernet_stats, hostname


def parse_ap_ethernet_stats(output, hostname):
    """
    Iterate through the show ap ethernet statistics output, remove the empty
    lines, separate the ethernet statistics by ap, and then add the statistics
    to a dictionary. If that port's speed is 100 Mbps, then add it to a list
    :return: list of dictionaries containing the ap ethernet statistics
    """
    lines = output.splitlines()
    nonempty_lines = []
    for line in lines:
        #remove preceding and trail whitespace
        if line != " " and line != "":
            stripped_line = line.strip()
            nonempty_lines.append(stripped_line)

    #find where the separate ap statistics are listed in the list
    ap_indices = []
    for line in nonempty_lines:
        if line.startswith("AP Name"):
            ap_index = nonempty_lines.index(line)
            ap_indices.append(ap_index)

    lines_split_by_ap = []
    for i, index in enumerate(ap_indices):
        # if we are at the last item in the ap_indices list
        if i == len(ap_indices) - 1:
            lines_split_by_ap.append(nonempty_lines[index:])
        else:
            lines_split_by_ap.append(nonempty_lines[index:ap_indices[i+1]])

    parsed_stats = []
    for ap_stats in lines_split_by_ap:
        stat_by_ap = {}
        stat_by_ap["WLC"] = hostname
        ap_name_split = ap_stats[0].split(":")
        ap_name = ap_name_split[1].strip()
        stat_by_ap["AP"] = ap_name

        # only one interface listed under the AP
        if len(ap_stats) == 4:
            ap_stat_split = ap_stats[-1].split()
        # two interfaces listed under the AP
        else:
            ap_stat_split = ap_stats[-2].split()

        stat_by_ap["port"] = ap_stat_split[0]
        stat_by_ap["speed"] = ap_stat_split[2] +  " " + ap_stat_split[3]
        stat_by_ap["duplex"] = ap_stat_split[4]

        if stat_by_ap["speed"] == "100 Mbps":
            parsed_stats.append(stat_by_ap)

    return parsed_stats


def main(argv):
    # retrieve the credentials
    with open("credentials.json", "r") as credential_file:
        CREDENTIALS = json.loads(credential_file.read())

    console = Console()
    console.print(Panel.fit(f"AP Port Speed Report"))

    parsed_stats = []
    with Progress() as progress:
        overall_progress = progress.add_task("Overall Progress",
                                             total=len(CREDENTIALS),
                                             transient=True)
        for wlc in CREDENTIALS:
            IP = wlc["IP_ADDRESS"]
            USER = wlc["USERNAME"]
            PASSWORD = wlc["PASSWORD"]

            progress.console.print(f"Retrieving and parsing AP Ethernet stats of WLC with IP {IP}")

            # connect to the WLCs and run command
            ethernet_stats, wlc = connect_to_wlc(IP, USER, PASSWORD)
            # check to make sure the command was successfully run
            if ethernet_stats is None:
                # if not, move to next WLC in the list
                console.print(f"[red]Error[/]: failed to run show ap ethernet statistics on WLC with IP {IP}, see above message for why")
                progress.update(overall_progress, advance=1)
                continue

            # parse the output of the command
            parsed_stats.extend(parse_ap_ethernet_stats(ethernet_stats, wlc))

            progress.update(overall_progress, advance=1)

    with pd.ExcelWriter("ap_ethernet_statistics.xlsx") as writer:
        stats_df = pd.DataFrame.from_dict(parsed_stats)
        stats_df.to_excel(writer, index=False)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
