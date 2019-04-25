#!/usr/bin/env python
#
"""
NAME
    parse_results.py - parses benchmark txt files and gathers results in
                       pnp_results.html
SYNOPSIS
    parse_results.py <DUT IP address>

DESCRIPTION
    Parses the <benchmark>.txt results files and generates the pnp_results.html
    file which will be used by "sendTo" as the body of the email message.
    It can be called as stand-alone, but it is normally called by pnp.py
    when results are being collected.

COPYRIGHT
    2014 Intel Corporation. All Rights Reserved.
"""

import os
from time import gmtime, strftime
import pnp_util
import argparse
import glob
import csv

long_result = None

def parse_results(dut_version=None):
    result_file = "pnp_results.html"
    csv_result_file = "pnp_results.csv"
    time = strftime('%Y-%m-%d', gmtime())

    if dut_version:
        ver = dut_version
    else:
        ver = pnp_util.get_dut_version()

    global long_result

    if not ver:
        print "ERROR: No version information found, did you run a test?"
        return None

    os.remove(result_file) if os.path.exists(result_file) else None
    for csv_file in glob.glob(os.path.join(os.curdir, '*_results.csv')):
        os.remove(csv_file)

    cached_vars = pnp_util.get_vars_from_file()

    board_name = ""
    fw_version = ""
    memory_channels = ""

    try:
        board_name = cached_vars["board"]
    except KeyError:
        pass

    try:
        fw_version = cached_vars["firmware"]
    except KeyError:
        pass

    if board_name == "":
        board_name = ver["board"]
    if fw_version == "":
        fw_version = ver["firmware"]

    try:
        memory_channels = cached_vars["memory_channels"]
    except KeyError:
        memory_channels = ver["memory_channels"]


    # Print the header and system information
    html = """Power and Performance results as of (dd-mm-yyyy) %s:
              <br /><br />
              Board: %s <br />
              Board base name: %s <br />
              Chrome Version: %s <br />
              Active firmware ID: %s <br />
              Firmware type: %s <br />
              Platform Build Version: %s <br />
              CPU model name: %s <br />
              CPU Turbo: %s <br />
              CPU Max Frequency: %sGHz <br />
              GPU Turbo: %s <br />
              GPU Max Frequency: %sMHz <br />
              Kernel version: %s <br />
              Mesa version: %s <br />
              Screen Resolution: %s <br />
              Memory: %sGB <br />
              Memory channels no: %s <br />
              <br />""" % (time, board_name, ver["basename"], ver["chrome"],
                           fw_version, ver["firmware_type"], ver["build"],
                           ver["cpu"], pnp_util.check_cpu_turbo(ver["ip"]),
                           ver["cpu_max_freq"], pnp_util.check_gpu_turbo(ver["ip"]),
                           ver["gpu_max_freq"], ver["kernel"], ver["mesa"],
                           ver["screen_resolution"], ver["memory"],
                           memory_channels)

    # Setup the table and header row
    html += """<table cellpadding="4" style="border: 1px solid #000000;
                border-collapse: collapse;" border="1">
                   <tr>
                       <th>Workload</th>
                       <th>Description</th>
                       <th>Units</th>
                       <th>Performance</th>
                       <th>Power</th>
                   </tr>"""

    pnp_csv_file = open(csv_result_file, 'w')
    pnp_csv_file_writer = csv.writer(pnp_csv_file)
    pnp_csv_file_writer.writerow(["*Note ( DO NOT REMOVE THIS LINE ) : TBD"])
    pnp_csv_file_writer.writerow(["Project*", "Distro*", "Device*", "Build Full Name*",
                                  "Build Number", "Build Date", "Test Freq*", "Tester*",
                                  "Note", "TestEnv_ENVs"])
    pnp_csv_header = ["ChromeOS"]
    pnp_csv_header.append("Chrome OS")
    pnp_csv_header.append("_".join(["TBD", "TBD"]))
    pnp_csv_header.append("_".join(["TBD", "TBD"]))
    pnp_csv_header.append("_".join(["TBD", "TBD"]))
    pnp_csv_header.append(time)
    pnp_csv_header.append("TBD")
    pnp_csv_header.append("tbd@intel.com")
    pnp_csv_header.append("TBD")
    pnp_csv_header.append("Board: %s\nBoard base name: %s\nChrome Version: %s\n\
Active firmware ID: %s\nFirmware type: %s\nPlatform \
Build Version: %s\nCPU model name: %s\nCPU Turbo: \
%s\nCPU Max Frequency: %sGHz\nGPU Turbo: %s\nGPU \
Max Frequency: %sMHz\nKernel version: %s\nMesa \
version: %s\nScreen Resolution: %s\nMemory: %sGB\n\
Memory channels no: %s\n" %
                           (board_name, ver["basename"], ver["chrome"],
                           fw_version, ver["firmware_type"], ver["build"],
                           ver["cpu"], pnp_util.check_cpu_turbo(ver["ip"]),
                           ver["cpu_max_freq"],
                           pnp_util.check_gpu_turbo(ver["ip"]),
                           ver["gpu_max_freq"], ver["kernel"], ver["mesa"],
                           ver["screen_resolution"], ver["memory"],
                           memory_channels))
    pnp_csv_file_writer.writerow(pnp_csv_header)
    pnp_csv_indicator_header = ["Indicator*", "D1*", "D2", "D3", "D4", "D5", "Comment"]
    pnp_csv_file_writer.writerow(pnp_csv_indicator_header)

    with open(result_file, 'w') as pnp_file:
        for benchmark in pnp_util.benchmarks:
            # Read the result data, skipping if the file does not exist.
            result_path = os.path.join(os.curdir, benchmark.name + '.txt')
            if not os.path.isfile(result_path):
                continue

            if benchmark.has_subtests:
                long_result = True
            else:
                long_result= False

            benchmark_sd_list = ["speedometer",
                                 "page_cycler.typical_25",
                                 "smoothness.top_25_smooth",
                                 "tab_switching.typical_25"]
            #get csv file
            if long_result:
                data = [['Workload', 'Description', 'Performance', 'Power']]
                csv_file = benchmark.get_name() + "_results.csv"
                if benchmark.name not in benchmark_sd_list:
                    html += "<tr>"
                    html += "<td>%s</td>" % (benchmark.name)
                    html += "<td>See attached file</td>"
                    html += "</tr>"
                else:
                    avg = 0.0
                    sd = 0.0

            result_file = open(result_path, 'r')
            ftext = result_file.read()

            # Extract the results
            perf_results = benchmark.get_perf_results(ftext)
            power_results = benchmark.get_power_results(ftext)

            # Formatting has the following layout
            # | description | units | performance results | power results |
            # Power data is duplicated for each performance result
            for perf_result in perf_results:
                #TODO debug print "PerfResult: %s" % perf_result.result
                if perf_result.result == "":
                    continue
                else:
                    perf_result_row = []
                    power_result_row = []
                    perf_indicator_name = "_".join(
                        ((benchmark.description + " " +
                          perf_result.measurement.
                          perf_pattern.split(',')[0]).
                          replace("-", " ").replace("_", " ")).split())
                    power_indicator_name = "Power_" + \
                        "_".join(((benchmark.description + " " +
                            perf_result.measurement.perf_pattern.split(
                            ',')[0]).replace("-", " ").replace("_", " ")).split())
                    perf_result_row.append(perf_indicator_name)
                    # Start the row
                    if not long_result:
                        html += "<tr>"

                        # Workload column
                        html += "<td>%s</td>" % (benchmark.name)

                        # Description column
                        html += "<td>%s - %s</td>" %(benchmark.description,
                              perf_result.measurement.perf_pattern.split(',')[0])

                        # Units column
                        html += "<td>%s" % (perf_result.measurement.units)
                        for result in power_results:
                            html += ", %s" % (result.measurement.units)
                            html += "</td>"

                        # Performance result column
                        html += "<td>%s</td>" % (perf_result.result)

                        # Power result column
                        html += "<td>"
                        for result in power_results:
                            html += "%s " % (result.result)
                        html += "</td>"

                        # Close the row for this benchmark
                        html += "</tr>"
                        for i_round in perf_result.results_list:
                            perf_result_row.append(i_round)

                        for power_result in power_results:
                            power_result_row = []
                            power_result_row.append(power_indicator_name)
                            for i_round in power_result.results_list:
                                if int(i_round) < 0:
                                    power_result_row = []
                                    break
                                power_result_row.append(i_round)

                    else:
                        row = []

                        # Workload column
                        row.append(benchmark.name)

                        # Description column
                        row.append(benchmark.description + " - " +
                                   perf_result.measurement.perf_pattern.split(',')[0])

                        # Performance result column
                        row.append(perf_result.result)
                        for i_round in perf_result.results_list:
                            perf_result_row.append(i_round)

                        # Power result column
                        for result in power_results:
                            row.append(result.result)

                        for power_result in power_results:
                            power_result_row = []
                            power_result_row.append(power_indicator_name)
                            for i_round in power_result.results_list:
                                if int(i_round) < 0:
                                    power_result_row = []
                                    continue
                                power_result_row.append(i_round)

                        data.append(row)
                        if (benchmark.name in benchmark_sd_list):
                            avg_list = []
                            sd_list = []

                            if benchmark.name == "speedometer":
                                avg_list = ["Avg Total"]
                                sd_list = ["Sd  Total"]
                            elif benchmark.name == "page_cycler_v2.typical_25":
                                avg_list = ["Avg timeToOnload"]
                                sd_list = ["Sd  timeToOnload"]
                            elif benchmark.name == "page_cycler.typical_25":
                                avg_list = ["Avg warm_times"]
                                sd_list = ["Sd  warm_times"]
                            elif benchmark.name == "smoothness.top_25_smooth":
                                avg_list = ["Avg percentage_smooth"]
                                sd_list = ["Sd  percentage_smooth"]
                            elif benchmark.name == "tab_switching.typical_25":
                                avg_list = ["Avg tab_switching_latency"]
                                sd_list = ["Sd tab_switching_latency"]

                            if perf_result.measurement.perf_pattern.split(',')[0] \
                                    in avg_list:
                                avg = perf_result.result
                            if perf_result.measurement.perf_pattern.split(',')[0] \
                                    in sd_list:
                                sd = perf_result.result

                            if avg != 0.0 and sd != 0.0:
                                html += "<tr>"

                                # Workload column
                                html += "<td>%s</td>" % (benchmark.name)

                                # Description column
                                html += "<td>%s - %s</td>" %(benchmark.description,
                                      perf_result.measurement.perf_pattern.split(',')[0])

                                # Units column
                                html += "<td>%s" % (perf_result.measurement.units)
                                for result in power_results:
                                    html += ", %s" % (result.measurement.units)
                                    html += "</td>"

                                # Performance result column
                                html += "<td>%s</td>" % (str(avg)+" +- " +
                                                         "{0:.2f}".format(sd / avg * 100) + "%")

                                # Power result column
                                html += "<td>"
                                for result in power_results:
                                    html += "%s " % (result.result)
                                html += "</td>"

                                # Close the row for this benchmark
                                html += "</tr>"

                                avg = 0.0
                                sd = 0.0

                # Verify the result data length and save to a CSV row
                if perf_result_row:
                    if len(perf_result_row) \
                       > len(pnp_csv_indicator_header) - 1:
                      print ("WARNING: %s result data number is bigger than %d\
, only keep first %d data"
                              % (perf_result_row[0],
                              len(pnp_csv_indicator_header) - 2,
                              len(pnp_csv_indicator_header) - 2))
                      perf_result_row = perf_result_row \
                                        [:len(pnp_csv_indicator_header) - 1]

                    if len(perf_result_row) < len(pnp_csv_indicator_header):
                      miss_data_len = len(pnp_csv_indicator_header) \
                                      - len(perf_result_row)
                      while miss_data_len > 0:
                        perf_result_row.append("")
                        miss_data_len = miss_data_len - 1
                    pnp_csv_file_writer.writerow(perf_result_row)

                if power_result_row:
                    if len(power_result_row) \
                       > len(pnp_csv_indicator_header) - 1:
                      print ("WARNING: %s result data number is bigger than %d\
, only keep first %d data"
                              % (power_result_row[0],
                              len(pnp_csv_indicator_header) - 2,
                              len(pnp_csv_indicator_header) - 2))
                      power_result_row = power_result_row \
                                         [:len(pnp_csv_indicator_header) - 1]

                    if len(power_result_row) < len(pnp_csv_indicator_header):
                      miss_data_len = len(pnp_csv_indicator_header) \
                                      - len(power_result_row)
                      while miss_data_len > 0:
                        power_result_row.append("")
                        miss_data_len = miss_data_len - 1
                    pnp_csv_file_writer.writerow(power_result_row)

            # Close the row for this benchmark
            if long_result:
                with open(csv_file, 'w') as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter=',')
                    csv_writer.writerows(data)
                    csvfile.close()
        html += "</table>"
        pnp_file.write(html)
    pnp_file.close()
    pnp_csv_file.close()

if __name__ == "__main__":
    parse_results()
