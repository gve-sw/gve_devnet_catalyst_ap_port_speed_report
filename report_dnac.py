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
from dnacentersdk import api
import pandas as pd
from dotenv import load_dotenv
import os
import sys
import json
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from pprint import pprint

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
    # get DNAC credentials from .env file
    load_dotenv()
    IP_ADDR = os.getenv("DNAC_IP")
    USER = os.getenv("USERNAME")
    PASSWORD = os.getenv("PASSWORD")

    console = Console()
    console.print(Panel.fit(f"AP Port Speed Report via DNA Center"))

    console.print(Panel.fit(f"Retrieve WLCs from DNA Center", title="Step 1"))

    # retrieve WLCs from DNA Center
    dnac = api.DNACenterAPI(username=USER,
                            password=PASSWORD,
                            base_url=IP_ADDR,
                            verify=False)
    wlcs = dnac.devices.get_device_list(family="Wireless Controller")

    console.print(Panel.fit(f"Run show ap ethernet statistics on all WLCs", title="Step 2"))

    # run show command on all WLCs
    wlc_ids = []
    wlc_id_to_name = {}

    for wlc in wlcs["response"]:
        if wlc["reachabilityStatus"] == "Reachable":
            wlc_ids.append(wlc["id"])
            wlc_id_to_name[wlc["id"]] = wlc["hostname"]

    try:
        show_command = dnac.command_runner.run_read_only_commands_on_devices(commands=["show ap ethernet statistics"],
                                                                             deviceUuids=wlc_ids,
                                                                             timeout=0)
    except Exception as e:
        console.print(f"[red]Error:[/] {e}. Failed to run show ap ethernet statistics on the WLCs")
    time.sleep(5)
    show_output_task = dnac.task.get_task_by_id(task_id=show_command.response.taskId)
    while "fileId" not in show_output_task.response.progress:
        show_output_task = dnac.task.get_task_by_id(task_id=show_command.response.taskId)

    progress = json.loads(show_output_task.response.progress)
    file_id = progress["fileId"]
    file = dnac.file.download_a_file_by_fileid(file_id)

    console.print(Panel.fit(f"Parse the output from the show commands", title="Step 3"))

    # parse the output from the show command
    parsed_stats = []
    with Progress() as progress:
        overall_progress = progress.add_task("Overall Progress", total=len(file.json()))

        for response in file.json():
            wlc_id = response["deviceUuid"]
            hostname = wlc_id_to_name[wlc_id]
            progress.console.print(f"Parsing the show ap ethernet statistics output from {hostname}")
            if "show ap ethernet statistics" in response["commandResponses"]["FAILURE"].keys():
                progress.console.print(f"[red]Error[/]: {response['commandResponses']['FAILURE']['show ap ethernet statistics']}")
                progress.update(overall_progress, advance=1)
                continue
            show_output = response["commandResponses"]["SUCCESS"]["show ap ethernet statistics"]
            parsed_stats.extend(parse_ap_ethernet_stats(show_output, hostname))
            progress.update(overall_progress, advance=1)

    console.print(Panel.fit(f"Write Excel report named [green]ap_ethernet_statistics.xlsx[/] from the parsed output", title="Step 4"))

    # create Excel report
    with pd.ExcelWriter("ap_ethernet_statistics.xlsx") as writer:
        stats_df = pd.DataFrame.from_dict(parsed_stats)
        stats_df.to_excel(writer, index=False)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
