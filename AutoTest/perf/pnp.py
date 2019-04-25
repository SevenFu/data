#!/usr/bin/env python

"""
NAME
    pnp.py - main executable for the PnP framework

SYNOPSIS
    sudo ./pnp.py --ip <DUT IP address> [--menu]

DESCRIPTION
    Main script that sets up, runs, collects and emails results for the PnP
    automated test. Running it without the --menu option will run the test
    with all benchmarks, will parse, collect and email results.
    Running the script with the --menu option, will display a menu allowing
    more control over each step of the process, including the ability to
    select the benchmarks to be run.

COPYRIGHT
    2014 Intel Corporation. All Rights Reserved.
"""

import os, stat
import sys
from time import sleep
import fnmatch, subprocess, signal
import pnp_util
import time
import pickle
from email.Utils import COMMASPACE
import urlparse
import argparse
import parse_results
import shutil
import tarfile
import glob
import socket
import sendTo
import re
import autotest_runner as au

from benchmarks import bench_settings
sys.path.append(os.path.normpath(os.path.join(os.path.realpath(__file__),
                                             os.path.pardir,
                                             os.path.pardir,
                                             os.path.pardir,
                                             "third_party",
                                             "catapult",
                                             "telemetry")))
sys.path.append(os.path.normpath(os.path.join(os.path.realpath(__file__),
                                             os.path.pardir,
                                             os.path.pardir,
                                             os.path.pardir,
                                             os.path.pardir,
                                            os.path.pardir,
                                             "scripts"
                                             )))
import Globals
ip = ""
use_macaddr = False

WARN_COUNT = 3
ERROR_COUNT = 4

VALID_RUNS = 3
UPLOAD_RESULTS = False
ARCHIVE_SERVER = "cros-share.ostc.intel.com"
BASE_DIR = os.path.dirname(__file__)

PAGE_CYCLER_NAME = "page_cycler_v2.typical_25"
PAGE_CYCLER_RUNS = 3
# TODO: break down VALID_RUNS PAGE_CYCLER_RUNS

def get_email_address(saved_vars={}, from_to=""):
    valid_from = False
    valid_to = False
    result = False

    if from_to == "from":
        while not valid_from:
            u = raw_input("Email from [" + saved_vars["from"] + "]:")
            valid_from = pnp_util.validate_email(u, [])
            if valid_from:
                saved_vars["from"] = u
                result = True
                pnp_util.write_vars_to_file(saved_vars)
            else:
                print "Invalid email address %s" %u
                if raw_input("Do you want to try again? (y/n):") == 'n':
                    break
    elif from_to == "to":
        while not valid_to:
            u = raw_input("Email to (comma separate multiple addresses)[" + \
                           COMMASPACE.join(saved_vars["to"]) + "]:")
            valid_to = pnp_util.validate_email("", u.split(","))
            if valid_to:
                saved_vars["to"] = u.split(",")
                result = True
                pnp_util.write_vars_to_file(saved_vars)
            else:
                print "Invalid email address"
                if raw_input("Do you want to try again? (y/n)") == 'n':
                    break

    return result


def send_alert(reason, bmark, saved_vars={}):

    subject = reason.split(' ')[0] + " " + bmark

    if "WARNING" in reason:
        body = "<p>%s: PnP test has run %s %d times and has failed to" \
               " collect complete data!</p><p>This workload will be postponed"\
               " and rerun before user intervention is required!</p>" \
                 %(reason.split(' ')[0], bmark, WARN_COUNT)
    elif "ERROR" in reason:
        body = "<p>%s: PnP test has run %s %d times and has failed to" \
               " collect complete data!</p><p>User intervention is" \
               " required!</p>" %(reason.split(' ')[0], bmark, ERROR_COUNT)

    body += "<p>List of delayed workloads:</p>"
    body += "<p>"+str(reason.split(' ')[1:])+"</p>"

    sendTo.send_mail(saved_vars["from"], saved_vars["to"], subject, body, [])


def check_data(bmark):
    b_count=0

    if bmark != "":
        for f in os.listdir(os.curdir):
            if re.search(r'\w+-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}.pkl$', f) and \
               bmark in f:
                b_count += 1
    else:
        for f in os.listdir(os.curdir):
            if re.search(r'\w+-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}.pkl$', f):
                b_count += 1

    return b_count

def saveTelemetryResultHtml(run_count, saved_vars, benchmark_name):
    ver = pnp_util.get_dut_version()

    board_name = ""
    try:
        board_name = saved_vars["board"]
    except KeyError:
        pass
    if board_name == "":
        board_name = ver["board"]
    cmd = "cp results.html %s_%s_%d_results.html" % (benchmark_name,
                board_name, run_count)
    print cmd
    os.system(cmd)
    print "deleting trace file"
    current_path = os.getcwd()
    del_files(current_path)


def del_files(path):
    for root, dirs, files in os.walk(path, topdown=True):
        for name in files:
            # print(os.path.join(root, name))
            if name.endswith(".html"):
                if name.startswith("http__") or name.startswith("https__") or name.startswith("ESPN_") \
                        or name.startswith("Blogger_") or name.startswith("Docs__") \
                        or name.startswith("LinkedIn_") or name.startswith("Facebook_") \
                        or name.startswith("Twitter_") or name.startswith("Weather_") \
                        or name.startswith("Wordpress_") or name.startswith("Wikipedia_") \
                        or name.startswith("Pinterest_"):
                    os.remove(os.path.join(root, name))
                    print ("Delete File: " + os.path.join(root, name))
                pass


#TODO: Break-up this ugly method
def runTest(skey, bmarks=[], saved_vars={}):
    offenders = {}
    mac = ""
    global ip
    b = None

    # ignore power analzer useless for wto test
    # try:
    #     os.stat("/dev/ttyUSB0")
    # except OSError, e:
    #     print e
    #     print "ERROR: Power Meter Not Found! Power Analyzer is not connected?"


    if not bmarks:
        benchmarks = pnp_util.get_benchmarks()
    else:
        benchmarks = bmarks
    global send_benchmarks 
    send_benchmarks = benchmarks
    # If the user specified '--use_macaddr', get MAC for IP address 'ip',
    # trying up to 5 times and pausing 10 seconds between attempts.
    # MAC is helpful if the IP address changes after a reboot between tests.
    if use_macaddr:
        print "Getting MAC address for %s..." %ip
        mac = pnp_util.get_mac_for_ip(ip, 10, 5)
        if mac == "":
            print "ERROR: Cannot get MAC address for %s" %ip
            print "ERROR: MAC address helps recover from IP address" \
                  + " changes between reboots"
            ans = ""
            while ans != 'y' and ans != 'n':
                ans = raw_input("Continue without it? (y/n): ").lower().rstrip()
            if ans == 'n':
                print "Exiting"
                exit()

    for test_name in benchmarks:
        run_count=0
        for i in pnp_util.benchmarks:
            if test_name in i.name:
                b = i

        if len(offenders) > 0:
            print "Workloads that couldn't execute:"
            print str(offenders.keys())

        print ("*"*30)
        try:
            print 'Testing ' + b.name
        except AttributeError:
            print test_name + " is not a valid workload"
            print "Valid workloads: "
            print pnp_util.get_benchmarks()
            break

        print ("*"*30)

        while (check_data(b.name) < VALID_RUNS and \
                not ("unityIntel" is b.name and run_count > 0)) \
                   or (PAGE_CYCLER_NAME == b.name and \
                   run_count < PAGE_CYCLER_RUNS):

            if use_macaddr and mac != "" and not pnp_util.pingDut(ip, 4, 20):
                print "Checking for IP address change for MAC %s..." %mac
                # Get IP address for 'mac', trying up to 5 times and pausing 15
                # seconds between attempts.
                new_ip = pnp_util.get_ip_for_mac(mac, ip, 15, 5)
                if new_ip == "":
                    print "ERROR: Cannot get IP address for MAC %s" %mac
                elif new_ip != ip:
                    print "IP address changed for MAC %s" %mac
                ip = new_ip

            # Now that we know the ip address, make sure we can connect to it.
            # If we can't, ask user to enter new address manually.
            while not pnp_util.pingDut(ip, 4, 20):
                if ip:
                    print "ERROR: Could not connect to DUT at %s" %ip
                print "If the address has changed and you know the new address,"
                print "please enter it now or press Enter to stop test"
                new_ip = raw_input("New IP address of the DUT: ")
                if new_ip == "":
                    print "No IP address given"
                    return
                ip = new_ip

            # Make sure we have the ssh key for the ip address.
            if not pnp_util.check_ip_key(ip):
                print "WARNING: Cannot get ssh key for IP address ", ip

            print 'System is ready...'
            sleep(1)
            print 'Running Iteration ' + str(run_count+1)
            print ("*"*100)
            pnp_util.cros_ssh(remote=ip, args=["stop", "powerd"])

            if b.framework_type is pnp_util.TELEMETRY:
                use_live_sites = "--use-live-sites" if b.use_live_sites else ""
                browser_flag = "--browser=cros-chrome --output-format=html "

                if "page_cycler_v2" in b.name:
                    browser_flag = "--browser=cros-chrome --reset-results --pageset-repeat=1 --output-format=html --output-dir=%s" %Globals.LOG.path

                if "smoothness" in b.name:
                    browser_flag = "--browser=cros-chrome --reset-results --output-format=html --output-dir=%s" %Globals.LOG.path

                if "tab_switching" in b.name or "webrtcIntel" in b.name:
                    browser_flag = "--browser=cros-chrome --reset-results --output-format=html --also-run-disabled-tests --output-dir=%s" %Globals.LOG.path

                runcmd = "%s/intel_run_benchmark --remote=%s --identity=%s "\
                          %(BASE_DIR, ip, skey) \
                          + browser_flag + use_live_sites +" %s"\
                          %b.alias
                print runcmd
                os.system(runcmd)
                if "page_cycler_v2" in b.name \
                    or "smoothness" in b.name \
                    or "tab_switching" in b.name \
                    or "webrtcIntel" in b.name:
                    saveTelemetryResultHtml(run_count, saved_vars, b.name)
            elif b.framework_type is pnp_util.AUTOTEST:
                auto_runner = au.AutotestWorkload(b.name, ip)
                print "Running " + b.name
                try:
                    auto_runner.start()
                except au.AutotestError as e:
                    print e
                    break

            pnp_util.cleanup("ssh")
            # In some cases, this function call is not enough to kill
            # the poweranaylzer, thus error values (-14.0) will be read
            # from the power anaylzer script. IT sometimes could also
            # lead to a stack dump.
            #pnp_util.cleanup("poweranalyzer")

            pnp_util.cleanupPower("poweranalyzer")

            print ("*"*100)
            print ("*"*30)
            if b.name == "webglaquariumV3Intel":
               time.sleep(600)
            print 'Rebooting the device...'
            pnp_util.cros_ssh(remote=ip, args=["reboot"])
            print ("*"*30)
            sleep(10)

            """ Another run has executed and need to take action
                if we still don't have good data
            """
            if check_data(b.name) < VALID_RUNS:
                # Ask for user intervention
                if run_count == ERROR_COUNT:
                    send_alert("ERROR "+str(offenders.keys()), b.name,
                               saved_vars)
                    print "Data collection for %s has failed %d times!" \
                          %(b.name, ERROR_COUNT)
                    print "Email alert has been sent to %s" %saved_vars["to"]
                    pnp_util.cleanup("ssh")
                    pnp_util.cleanup("poweranalyzer")
                    sys.exit()
                elif run_count == WARN_COUNT:
                    print "Data collection for %s has failed %d times!" \
                          %(b.name, WARN_COUNT)
                    print "Email alert has been send to %s" %saved_vars["to"]

                    # continue with other benchmarks if this one has problems
                    # and add it at the end of the list to be retried
                    if not offenders.get(b.name, False):
                        offenders[b.name] = True
                        benchmarks.append(b.name)
                        send_alert("WARNING "+str(offenders.keys()), b.name,
                                   saved_vars)
                        break
                    else:
                        send_alert("WARNING "+str(offenders.keys()), b.name,
                                   saved_vars)

            elif offenders.get(b.name, False):
                del offenders[b.name]
            run_count += 1


def collect_results(saved_vars={}):

    if check_data("") == 0:
        print "WARNING: No data .pkl files found!"
        return

    ver = pnp_util.get_dut_version()

    board_name = ""
    fw_version = ""

    try:
        board_name = saved_vars["board"]
    except KeyError:
        pass

    try:
        fw_version = saved_vars["firmware"]
    except KeyError:
        pass

    if board_name == "":
        board_name = ver["board"]
    if fw_version == "":
        fw_version = ver["firmware"]

    title = "Power and Performance Test Results"
    saved_vars["subject"] = title + " Chrome Version: " + ver["chrome"] \
                            + " Firmware: " + fw_version + " Build: " \
                            + ver["build"] + " Board: " + board_name

    pnp_util.write_vars_to_file(saved_vars)

    res_dir = "".join([board_name, "-", pnp_util.get_time()])

    # convert pkl files to text
    pnp_util.totext(os.curdir)

    # convert html to csv
    pnp_util.htmltocsv(send_benchmarks,os.curdir, saved_vars)

    # Parse and collect results
    parse_results.parse_results(ver)

    try:
        os.mkdir(res_dir)
    except OSError, e:
        print e
        return

    for filename in glob.glob(os.path.join(os.curdir, '*.pkl')):
        shutil.copy(filename, os.path.join(os.curdir, res_dir))
    for filename in glob.glob(os.path.join(os.curdir, '*.txt')):
        shutil.copy(filename, os.path.join(os.curdir, res_dir))
    for filename in glob.glob(os.path.join(os.curdir, '*_results.html')):
        shutil.copy(filename, os.path.join(os.curdir, res_dir))

    with tarfile.open(res_dir + ".tar.bz2", "w:bz2") as tar:
        tar.add(res_dir, arcname=os.path.basename(res_dir))

    # cache the name of the archive file
    saved_vars["attachment"] = []
    saved_vars["attachment"].insert(0, res_dir + ".tar.bz2")
    i = 1
    if parse_results.long_result:
        for filename in glob.glob(os.path.join(os.curdir, '*_results.csv')):
            saved_vars["attachment"].insert(i, filename)
            i += 1
    benchmarks = pnp_util.get_benchmarks()
    if "page_cycler_v2.typical_25" in benchmarks \
       or "smoothness.top_25_smooth" in benchmarks \
       or "tab_switching.typical_25" in benchmarks \
       or "webrtcIntel" in benchmarks:
        for filename in glob.glob(os.path.join(os.curdir, '*_values.csv')):
            saved_vars["attachment"].insert(i, filename)
            i += 1

    shutil.rmtree(res_dir)

    pnp_util.write_vars_to_file(saved_vars)

    # Uploade files to ARCHIVE_SERVER
    if UPLOAD_RESULTS:
        pnp_util.copy_archive_to_server(ARCHIVE_SERVER,
                                    saved_vars['attachment'][0],
                                    ssh_user=args.ssh_user)


def email_results(ipaddr):
    if check_data("") == 0:
        print "WARNING: No data was found! Will not send email!"
        return

    cmd = os.path.join(BASE_DIR, "sendTo.py")
    if ipaddr:
        cmd += " -ip " + ipaddr

    os.system(cmd)


def set_up_and_run(saved_vars={}, bmarks=[]):
    # Make sure we have the ssh key for the ip address.
    if not pnp_util.check_ip_key(ip):
        print "WARNING: Cannot get ssh key for IP address ", ip

    title = "Power and Performance Test Results"
    ver = pnp_util.get_dut_version(ip)
    if ver:
        saved_vars["subject"] = title + " Chrome Version: " + ver["chrome"]\
                             + " Firmware: " + ver["firmware"] + " Build: "\
                             + ver["build"] + " Board: " + ver["board"]
    else:
        print "ERROR: Unable to obtain DUT version information"
        exit(1)

    pnp_util.write_vars_to_file(saved_vars)

    s_key = pnp_util.get_ssh_key()
    if os.path.isfile(s_key) == False:
        print "ERROR: " + s_key + " not found!"

    runTest(s_key, bmarks, saved_vars)


def select_benchmarks(selected_benchmarks=[]):
    os.system("clear")
    print "Current Benchmarks:\n"
    all_benchmarks = pnp_util.get_benchmarks()
    print "\nSelected benchmarks:\n"
    print selected_benchmarks
    print '\n'
    ans = ""
    while ans != "r":
        i = 0
        print "Possible benchmarks:"
        for bm in all_benchmarks:
            print `i` + ") " + bm
            i += 1
        print "\na) Select all benchmarks"
        print "c) Clear all selected benchmarks"
        print "r) Return to main menu\n"
        ans = raw_input("Select benchmark or r to go back: ")
        maxB = i - 1
        os.system("clear")
        if ans == 'a':
            for bm in all_benchmarks:
               if bm not in selected_benchmarks:
                   selected_benchmarks.append(bm)
        elif ans == 'c':
            selected_benchmarks = []
        else:
            try:
                idx = int(ans)
                if all_benchmarks[idx] not in selected_benchmarks:
                    selected_benchmarks.append(all_benchmarks[idx])
                else:
                    selected_benchmarks.remove(all_benchmarks[idx])
            except ValueError:
                print "Please enter an integer between 0 and %d (a for all)" \
                      % maxB
            except IndexError:
                print "Value %d is greater than max index %d" %  ( idx, maxB )

        print "Selected benchmarks: "
        print '\n'
        print selected_benchmarks
        print "\n\n"

    return selected_benchmarks


def enforce_email(saved_vars={}):
    if not pnp_util.validate_email(saved_vars["from"], []):
        if not get_email_address(saved_vars, "from"):
            return False
    if not pnp_util.validate_email("", saved_vars["to"]):
        if not get_email_address(saved_vars, "to"):
            return False

    return True

def check_valid_url(hurl):
    # Can send URL by --server command line, or by menu entry if 'custom'.
    # not "strong" validation, just see if it's an URL. It can be http or https.
    # It must not have a port.
    valUrl = urlparse.urlparse(hurl)
    if valUrl.scheme != 'http' and valUrl.scheme != 'https':
       print "Server URL must begin with 'http://' or 'https://'"
    elif valUrl.port != None:
       print "May not specify port in server URL."
    elif valUrl.netloc == '':
       print "Badly formed server URL."
    elif ' ' in hurl:
       print "Badly formed server URL."
    else:
       return True

    return False


def select_server(preset={}, saved_vars={}):
    valid = False
    while not valid:
        print "Select server by letter:"
        print preset
        ans = raw_input("Server: ")
        try:
            test_server = preset[ans]
            valid = True
        except KeyError:
            print "%s is not a known server set." %ans
            print "Please enter one of the defined server keys."

    saved_vars['ts'] = test_server
    if test_server == 'custom':
       ans = enter_server_URL()
       if ans:
          saved_vars['url'] = ans
       else:
          print "URL unchanged, using " + saved_vars['url']
    else:
       saved_vars['url'] = bm.get_serv_URL(test_server)
    pnp_util.write_vars_to_file(saved_vars)

    return test_server

def enter_server_URL():
    valid = False
    while not valid:
        ans = raw_input("Enter Custom Server URL: ")
        if ans == "": return False
        valid = check_valid_url(ans)
    return ans

def show_menu(saved_vars={}):
    ans = ""
    bmarks = []
    global ip

    try:
        test_server = saved_vars['ts']
    except KeyError:
        test_server = 'standard'
        saved_vars['ts'] = test_server
    metasets = bm.get_metasets()

    print("="*45)
    print "Power and Performance Test"
    print("="*45)
    while ans != "x":
        print "\n\n"
        print "Enter a menu option to set up your test environment: \n\n"

        try:
            print "1) Email from = [" + saved_vars["from"] + "]"
        except KeyError:
            print "1) Email from = []"
        try:
            print "2) Email to = [" + COMMASPACE.join(saved_vars["to"]) + "]"
        except KeyError:
            print "2) Email to = []"

        if ip:
            print "3) Select Benchmarks to run"
            print "4) Select Benchmarks Webserver = [ " + test_server + " at "\
                  + bm.get_serv_URL(test_server) + " ]"

        try:
            print "5) Board Name = [" + saved_vars["board"] + "]"
        except KeyError:
            print "5) Board Name = []"
        try:
            print "6) Firmware version = [" + saved_vars["firmware"] + "]"
        except KeyError:
            print "6) Firmware version = []"

        if ip:
            print "\n"
            print "r) Run the test"

        print "a) Archive existing pkl files"
        print "c) Collect Results"
        print "d) Delete Results"
        print "e) Email results now"
        print "x) Exit now"
        print "\n"

        ans = raw_input("Option: ")
        usrin = ""

        if ans == "1":
            get_email_address(saved_vars, "from")

        elif ans == "2":
            get_email_address(saved_vars, "to")

        elif ans == "3":
            if ip:
                bmarks = select_benchmarks(bmarks)

        elif ans == "4":
            if ip:
                # Note: this stores the changes in the saved_vars file.
                test_server = select_server(metasets, saved_vars)

        elif ans == "5":
            u = raw_input("Enter board name: ")
            saved_vars["board"] = u

        elif ans == "6":
            u = raw_input("Enter firmware version: ")
            saved_vars["firmware"] = u

        # Run the test
        elif ans == "r":
            if ip:
                if enforce_email(saved_vars):
                    set_up_and_run(saved_vars, bmarks)
                else:
                    # return to menu
                    print "Error: Invalid email address(es)"
            else:
                print "ERROR: No DUT IP was specified, rerun providing the"\
                      +" --ip=<DUT_IP> parameter!"

        # Collect results
        elif ans == "c":
            collect_results(saved_vars)

        # Email results
        elif ans == "e":
            if enforce_email(saved_vars):
                email_results("")
            else:
                # return to menu
                print "Error: Invalid email address(es)"

        # Remove results
        elif ans == "d":
            pnp_util.delete_pkl(os.curdir)
            pnp_util.delete_csv_html(os.curdir)
            os.system("find *.html \! -name 'pnp_results.html' -delete")

        # Handle existing pkl files
        elif ans == "a":
            pnp_util.archive_pkl(os.curdir)

    pnp_util.write_vars_to_file(saved_vars)

if __name__== "__main__":

    aparser = argparse.ArgumentParser(prog='pnp.py')
    group = aparser.add_argument_group('required arguments')
    group.add_argument('--ip', dest="ipaddr",
                         help='IP address of the DUT')
    aparser.add_argument('--menu', action="store_true", default=False,
                         help='Displays the menu')
    aparser.add_argument('--new_run', action="store_true", default=False,
                         help='Archive existing pkl files')
    aparser.add_argument('--use_macaddr', action="store_true", default=False,
                         help="Use MAC address to recover from IP address "\
                         + "changes")
    aparser.add_argument('--to_email', required=True, help='Email address for'\
                         +' sending results', metavar='<tester>@intel.com')
    aparser.add_argument('--workloads', help='Comma-separated list of workload'\
                         +' file names', metavar='<workload> | {<workload>, }')
    aparser.add_argument('--server', dest="httpaddr", nargs=1,
                         help="set URL of web server for benchmarks")
    aparser.add_argument('--runs', dest="n", nargs=1,
                         help="number of valid runs per benchmark, default 3")
    aparser.add_argument('--delay', dest='delay', metavar='<s>', default=10,
                         type=int,
                         help='Number of seconds to sleep between workloads')
    aparser.add_argument('--board', metavar='<board>', help='Board name')
    aparser.add_argument('--firmware', metavar="BIOS|CoreBoot version",
                         help="Enter firmware version string with no spaces")
    aparser.add_argument('--memory_channels', metavar='<memory_channels>',
                         help='Number of memory channels')
    aparser.add_argument('--ssh_user', metavar='<user>', help='Username '\
                         +'for the results archive server', dest='ssh_user')
    aparser.add_argument('--upload_results', action="store_true", default=False,
                         help='Upload results to the results archive server')

    args = aparser.parse_args()

    use_macaddr = args.use_macaddr

    pnp_util.clean_up()

    # Ensuring that no zombie process of poweranalyzer is left behind
    pnp_util.cleanupPower("poweranalyzer")


    if args.httpaddr:
       if check_valid_url(args.httpaddr[0]):
           saved_vars=pnp_util.get_vars_from_file()
           saved_vars['ts'] = 'custom'
           saved_vars['url'] = args.httpaddr[0]
           pnp_util.write_vars_to_file(saved_vars)
       else:
           aparser.print_help()
           sys.exit(2)

    if args.n:
       if args.n[0].isdigit():
          try:
              VALID_RUNS = int(args.n[0])
          except ValueError as e:
              print "WARNING: unable to convert --runs=N to int"

          WARN_COUNT = VALID_RUNS
          ERROR_COUNT = VALID_RUNS + 1
       else:
           aparser.print_help()
           sys.exit(2)

    cached_vars = pnp_util.get_vars_from_file()

    ip = args.ipaddr


    if args.new_run:
        pnp_util.archive_pkl(os.curdir)
        pnp_util.delete_pkl(os.curdir)
        pnp_util.delete_csv_html(os.curdir)
        os.system("find *.html \! -name 'pnp_results.html' -delete")

    if args.to_email:
        if pnp_util.validate_email("", args.to_email.split(',')):
            cached_vars['to'] = args.to_email.split(',')
            pnp_util.write_vars_to_file(cached_vars)
        else:
            print "Invalid to email(s). Please enter a valid email address!"
            aparser.print_help()
            sys.exit()

    if args.board:
        cached_vars["board"] = args.board
        pnp_util.write_vars_to_file(cached_vars)

    if args.firmware:
        cached_vars["firmware"] = args.firmware
        pnp_util.write_vars_to_file(cached_vars)

    if args.memory_channels:
        cached_vars["memory_channels"] = args.memory_channels
        pnp_util.write_vars_to_file(cached_vars)

    if args.upload_results:
        UPLOAD_RESULTS = True

    # All the obstacles have been passed.
    # get a benchmark-mapping entity

    bm = bench_settings.bench_mapping()

    # Note: passing the get_vars_from_file() function,
    # ensures that it dynamically updates as things are
    # saved. Python-magic.
    if args.menu:
        show_menu(pnp_util.get_vars_from_file())
    else:
        s_key = pnp_util.get_ssh_key()
        if os.path.isfile(s_key) == False:
            print "ERROR: " + s_key + " not found!"
        else:
            s_key = pnp_util.get_ssh_key()
            if os.path.isfile(s_key) == False:
                print "ERROR: " + s_key + " not found!"
            else:
                benchmarks = []
                if args.workloads:
                    for w in args.workloads.split(","):
                        benchmarks.append(w)
                else:
                    benchmarks = pnp_util.get_unified_benchmark_list()

                if ip:
                    set_up_and_run(pnp_util.get_vars_from_file(), benchmarks)
                    pnp_util.pingDut(ip, 8, 10)
                collect_results(pnp_util.get_vars_from_file())
                email_results(ip)
