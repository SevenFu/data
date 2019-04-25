#!/usr/bin/env python
"""
NAME
    pnp_util.py - module with utility functions for the PnP framework

SYNOPSIS
    import pnp_util

DESCRIPTION
    Module contains a series of commonly used utility functions for the
    Power and Performance automated framework.

AUTHOR
    Nathan Ciobanu (nathan.d.ciobanu@intel.com)

COPYRIGHT
    2014 Intel Corporation. All Rights Reserved.
"""

import os
import sys
import pickle
import re
import time
import socket
import numpy
from collections import namedtuple
from glob import glob
import cPickle
import shutil
from ConfigParser import SafeConfigParser
import subprocess as sp
from subprocess import PIPE
import psutil
import result_libs as resl
import datetime
from datetime import date
import histograms
import sendTo

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             os.path.pardir,
                                             os.path.pardir,
                                             "third_party",
                                             "catapult",
                                             "telemetry")))

from telemetry.core import cros_interface


Measurement = resl.Measurement
Result = namedtuple('Result', ['measurement', 'result', 'results_list'])

PAGE_CYCLER_NAME = "page_cycler_v2.typical_25"

class Benchmark():
    def __init__(self, alias, name, description, perf_measurements,
                 power_measurements, framework_type, has_subtests = False,
                 use_live_sites = True, in_unified = False):
        """
        Args:
            name: Benchmark name
            description: Short summary of the benchmark
            perf_measurements: List of performance measurements
            power_measurements: List of power measurements
            framework_type: telemetry or autotest
            use_live_sites: WPR should be able to scrape most simple static
                            websites. Streaming videos and certain workloads
                            such as BrowsingBench require livesites.
        """
        self.alias = alias
        self.name = name
        self.description = description
        self.perf_measurements = perf_measurements
        self.power_measurements = power_measurements
        self.framework_type = framework_type
        self.has_subtests = has_subtests
        self.use_live_sites = use_live_sites
        self.in_unified = in_unified

    def _extract_max(self, measurement, telemetry_text):
        """Extract the max from the telemetry output

        Args:
            measurement: Measurement to search the text for
            telemetry_text: Text to search through
        """
        results = []
        result = ""
        # Populate the list with any results
        for i in re.findall(measurement.perf_pattern, telemetry_text):
            perf_value = i.split(measurement.perf_spl)[1].split(',')[0]
            try:
                results.append(float(perf_value))
            except ValueError:
                print "Warning: Could not get perf value!"

        # Calculate the max if there are results
        if results:
            result = numpy.max(results)
            result = round(result, 2)

        return result;

    def _extract_median(self, measurement, telemetry_text):
        """Extract the median from the telemetry output

        Args:
            measurement: Measurement to search the text for
            telemetry_text: Text to search through
        """
        results = []
        result = ""
        # Populate the list with any results
        for i in re.findall(measurement.perf_pattern, telemetry_text):
            perf_value = i.split(measurement.perf_spl)[1].split(',')[0]
            try:
                results.append(float(perf_value))
            except ValueError:
                print "Warning: Could not get perf value!"

        # Calculate the median if there are results
        if results:
            result = numpy.median(results)
            result = round(result, 2)

        return result;

    def _extract_series(self, measurement, telemetry_text):
        """Extract score0~score2 for unityIntel benchmark

        Args:
            measurement: Measurement to search the text for
            telemetry_text: Text to search through
        """
        results = []
        result = ""
        loop_num = 4
        for num in range(0, loop_num):
            unity_perf_spl     = "score%d, " % num
            unity_perf_pattern = "score%d, .*?," % num
            # Populate the list with any results
            for i in re.findall(unity_perf_pattern, telemetry_text):
                perf_value = i.split(unity_perf_spl)[1].split(',')[0]
                if num > 0:
                    try:
                        results.append(float(perf_value))
                    except ValueError:
                        print "Warning: Could not get perf value!"

        # Calculate the maxium if there are results
        if results:
            result = numpy.nanmax(results)
            result = round(result, 2)

        return result;

    def _extract_unity_results_list(self, measurement, telemetry_text):
        """Extract the list of score1~score3 for unityIntel benchmark

        Args:
            measurement: Measurement to search the text for
            telemetry_text: Text to search through
        """
        results = []
        loop_num = 4
        for num in range(0, loop_num):
            unity_perf_spl     = "score%d, " % num
            unity_perf_pattern = "score%d, .*?," % num
            # Populate the list with any results
            for i in re.findall(unity_perf_pattern, telemetry_text):
                perf_value = i.split(unity_perf_spl)[1].split(',')[0]
                if num > 0:
                    try:
                        results.append(float(perf_value))
                    except ValueError:
                        print "Warning: Could not get perf value!"
        return results

    def _extract_results_list(self, measurement, telemetry_text):
        """Extract the list from the telemetry output

        Args:
            measurement: Measurement to search the text for
            telemetry_text: Text to search through
        """
        results = []
        # Populate the list with any results
        if ('unityIntel' is self.name) and ('score' is measurement.units):
            results = self._extract_unity_results_list(measurement, telemetry_text)
        else:
            for i in re.findall(measurement.perf_pattern, telemetry_text):
                perf_value = i.split(measurement.perf_spl)[1].split(',')[0]
                try:
                    results.append(float(perf_value))
                except ValueError:
                    print "Warning: Could not get perf value!"
        return results;

    def _extract_results(self, measurements, telemetry_text):
        """Extract any measurements from input text

        Args:
            measurements: List of measurements
            telemtry_text: Text to search through

        Returns:
            A list of Results
        """
        results = []
        for measurement in measurements:
            if ('octaneV2New' is self.name) and ('watts' is not measurement.units):
                result = self._extract_max(measurement, telemetry_text)
            elif ('unityIntel' is self.name) and ('score' is measurement.units):
                result = self._extract_series(measurement, telemetry_text)
            else:
                result = self._extract_median(measurement, telemetry_text)
            results_list = self._extract_results_list(measurement,
                                                      telemetry_text)
            results.append(Result(measurement, result, results_list))

        return results

    def get_perf_results(self, telemetry_text):
        """Extract any performance results from the input text

        Args:
            telemtry_text: Text to search through

        Returns:
            A list of Results
        """
        return self._extract_results(self.perf_measurements, telemetry_text)

    def get_power_results(self, telemetry_text):
        """Extract any power results from the input text

        Args:
            telemtry_text: Text to search through

        Returns:
            A list of Results
        """
        return self._extract_results(self.power_measurements, telemetry_text)

    def get_name(self):
        """Getter for the benchmark name"""
        return self.name

    def get_alias(self):
        '''Getter for the test alias'''
        return self.alias

    def get_description(self):
        """Getter for the benchmark description"""
        return self.description


# Setup common performance measurements.
total_time_measurement = Measurement('ms', 'total, .*?,', 'total, ')
score_measurement = Measurement('score', 'score, .*?,', 'score, ')
fps_measurement = Measurement('fps', 'FPS, .*?,', 'FPS, ')

# Unique measurement for angrybirdsIntel.
eject_fps_measurement = Measurement('fps', 'ejectFPS, .*?,', 'ejectFPS, ')

# Unique measurement for localVideo*Intel
dropped_frames_measurement = Measurement('dropped frames',
                                         'dropped_frame_count.media_0, .*?,',
                                         'dropped_frame_count.media_0, ')

# Unique measurement for streamingVP*Intel
dropped_frame_count_measurement = Measurement('dropped frames',
                                              'droppedFrameCount, .*?,',
                                              'droppedFrameCount, ')

# Setup power measurement.
power_measurement = Measurement('watts',
                                "power\n{'max': .*?, 'mean': .*?,",
                                "'mean': ")

# Unique measurement for hardware_CoremarkIntel
coremark_iterations_measurement = Measurement('iterations', 'iterations, .*?,',
                                              'iterations, ')


# Unique measurement for hardware_SpecIntel
spec_overall_measurement_val = Measurement('Overall', 'Overall Value, .*?,',
                                           'Overall Value, ')
spec_overall_measurement_time = Measurement('Overall', 'Overall Time, .*?,',
                                            'Overall Time, ')



# Setup benchmarks. Update this when adding new benchmarks.
TELEMETRY = 'telemetry'
AUTOTEST = 'autotest'

benchmarks = []
benchmarks.append(Benchmark('sunspiderV1Intel.SunspiderV1Intel',
                            'sunspiderV1Intel',
                            'JavaScript - Sunspider v1.0.2',
                            [total_time_measurement],
                            [power_measurement],
                            TELEMETRY))
benchmarks.append(Benchmark('krakenIntel.KrakenIntel',
                            'krakenIntel',
                            'JavaScript - Kraken',
                            [total_time_measurement],
                            [power_measurement],
                            TELEMETRY))
benchmarks.append(Benchmark('octaneV2New.OctaneV2New',
                            'octaneV2New',
                            'JavaScript - Octane v2',
                            [score_measurement],
                            [power_measurement],
                            TELEMETRY,
                            in_unified = True))
benchmarks.append(Benchmark('angrybirdsIntel.AngryBirdsIntel',
                            'angrybirdsIntel',
                            'HTML5 Games - AngryBirds',
                            [eject_fps_measurement],
                            [power_measurement],
                            TELEMETRY))
benchmarks.append(Benchmark('canvasearthIntel.CanvasEarthIntel',
                            'canvasearthIntel',
                            'Canvas 2D - CanvasEarth',
                            [fps_measurement],
                            [power_measurement],
                            TELEMETRY,
                            in_unified = True))
benchmarks.append(Benchmark('fishietankIntel.FishIETankIntel',
                            'fishietankIntel',
                            'Canvas2D - FishTank 250 fish',
                            [fps_measurement],
                            [power_measurement],
                            TELEMETRY))
benchmarks.append(Benchmark('robohornetIntel.RobohornetIntel',
                            'robohornetIntel',
                            'Browser Performance - RoboHornet',
                            [score_measurement],
                            [power_measurement],
                            TELEMETRY))
benchmarks.append(Benchmark('browsingbenchIntel.BrowsingBenchIntel',
                            'browsingbenchIntel',
                            'Browser Performance - BrowsingBenchIntel',
                            [score_measurement],
                            [power_measurement],
                            TELEMETRY))
benchmarks.append(Benchmark('webxprtIntel.webxprtIntel',
                            'webxprtIntel',
                            'Browser Performance - WebXPert',
                            [score_measurement],
                            [power_measurement],
                            TELEMETRY))
benchmarks.append(Benchmark('webxprt2015Intel.webxprt2015Intel',
                            'webxprt2015Intel',
                            'Browser Performance - WebXPRT 2015',
                            [score_measurement],
                            [power_measurement],
                            TELEMETRY))
benchmarks.append(Benchmark('earthscreenIntel.EarthScreenIntel',
                            'earthscreenIntel',
                            'WebGL - EarthScreen',
                            [fps_measurement],
                            [power_measurement],
                            TELEMETRY))
benchmarks.append(Benchmark('webglaquariumV3Intel.WebGLAquariumV3Intel',
                            'webglaquariumV3Intel',
                            'WebGL - Aquarium 1000 fish',
                            [fps_measurement],
                            [power_measurement],
                            TELEMETRY,
                            in_unified = True))
benchmarks.append(Benchmark('streamingVP9Intel.StreamingVP9Intel',
                            'streamingVP9Intel',
                            'VP9 1080p60 - Streaming',
                            [fps_measurement, dropped_frame_count_measurement],
                            [power_measurement],
                            TELEMETRY,
                            in_unified = True))
benchmarks.append(Benchmark('streamingVP94KIntel.StreamingVP94KIntel',
                            'streamingVP94KIntel',
                            'VP9 4K30 - Streaming',
                            [fps_measurement, dropped_frame_count_measurement],
                            [power_measurement],
                            TELEMETRY,
                            in_unified = True))
benchmarks.append(Benchmark('streamingVP91080P30Intel.StreamingVP91080P30Intel',
                            'streamingVP91080P30Intel',
                            'VP9 1080P30 - Streaming',
                            [fps_measurement, dropped_frame_count_measurement],
                            [power_measurement],
                            TELEMETRY,
                            in_unified = True))
benchmarks.append(Benchmark('streamingVP94K60Intel.StreamingVP94K60Intel',
                            'streamingVP94K60Intel',
                            'VP9 4K60 - Streaming',
                            [fps_measurement, dropped_frame_count_measurement],
                            [power_measurement],
                            TELEMETRY))
benchmarks.append(Benchmark('webrtcIntel',
                            'webrtcIntel',
                            '720p30 video chat using WebRTC',
                            resl.WebRtcResults().measurements,
                            [power_measurement],
                            TELEMETRY,
                            use_live_sites=False))
benchmarks.append(Benchmark('localVideo30Intel.localVideo30Intel',
                            'localVideo30Intel',
                            'H264 30FPS - Local',
                            [fps_measurement, dropped_frames_measurement],
                            [power_measurement],
                            TELEMETRY))
benchmarks.append(Benchmark('localVideo60Intel.localVideo60Intel',
                            'localVideo60Intel',
                            'H264 60FPS - Local',
                            [fps_measurement, dropped_frames_measurement],
                            [power_measurement],
                            TELEMETRY))
benchmarks.append(Benchmark('speedometer', 'speedometer', 'Speedometer',
                            resl.SpeedometerResults().measurements,
                            [power_measurement],
                            TELEMETRY, resl.SpeedometerResults().has_subtests,
                            use_live_sites=False))
benchmarks.append(Benchmark('smoothness.top_25_smooth',
                            'smoothness.top_25_smooth',
                            'Smoothness',
                            resl.SmoothnessTop25SmoothResults().measurements,
                            [power_measurement],
                            TELEMETRY,
                            resl.SmoothnessTop25SmoothResults().has_subtests,
                            use_live_sites=False,
                            in_unified = True))
benchmarks.append(Benchmark('page_cycler_v2.typical_25',
                            'page_cycler_v2.typical_25',
                            'Pagecycler.V2',
                            resl.PageCyclerV2Typical25Results().measurements,
                            [power_measurement],
                            TELEMETRY,
                            resl.PageCyclerV2Typical25Results().has_subtests,
                            use_live_sites=False,
                            in_unified = True))
benchmarks.append(Benchmark('unityIntel.unity2015Intel',
                            'unityIntel',
                            'Unity2015',
                            [score_measurement],
                            [power_measurement],
                            TELEMETRY,
                            in_unified = True))
benchmarks.append(Benchmark('', 'hardware_CoremarkIntel',
                            'Coremark',
                            [coremark_iterations_measurement],
                            [power_measurement],
                            AUTOTEST))
benchmarks.append(Benchmark('', 'hardware_StreamIntel',
                            'Stream',
                             resl.StreamIntelResults().measurements,
                             [power_measurement],
                             AUTOTEST,
                             in_unified = True))
benchmarks.append(Benchmark('', 'hardware_SpecIntel',
                            'Spec',
                            [spec_overall_measurement_val,
                             spec_overall_measurement_time],
                            [power_measurement],
                            AUTOTEST))
benchmarks.append(Benchmark('', 'platform_BootPerf',
                            'BootPerf',
                            resl.BootPerfResults().measurements,
                            [power_measurement],
                            AUTOTEST,
                            in_unified = True))
benchmarks.append(Benchmark('', 'graphics_CrXprtIntel',
                            'CrXPRT',
                            resl.CrXprtIntelResults().measurements,
                            [power_measurement],
                            AUTOTEST))
benchmarks.append(Benchmark('', 'graphics_GLMark2',
                            'GLMark2',
                            resl.Glmark2Results().measurements,
                            [power_measurement],
                            AUTOTEST, resl.Glmark2Results().has_subtests))
benchmarks.append(Benchmark('', 'graphics_GLBench',
                            'GLBench',
                            resl.GlbenchResults().measurements,
                            [power_measurement],
                            AUTOTEST, resl.GlbenchResults().has_subtests))
benchmarks.append(Benchmark('tab_switching.typical_25',
                            'tab_switching.typical_25',
                            'TabSwitching',
                            resl.TabSwitchingTypical25Results().measurements,
                            [power_measurement],
                            TELEMETRY,
                            resl.TabSwitchingTypical25Results().has_subtests,
                            use_live_sites=False))
benchmarks.append(Benchmark('speedometerIntelV1.speedometerIntelV1',
                            'speedometerIntelV1',
                            'SpeedometerIntelV1',
                            [score_measurement],
                            [power_measurement],
                            TELEMETRY,
                            in_unified = True))
benchmarks.append(Benchmark('speedometerIntelV2.speedometerIntelV2',
                            'speedometerIntelV2',
                            'SpeedometerIntelV2',
                            [score_measurement],
                            [power_measurement],
                            TELEMETRY,
                            in_unified = True))


def validate_email(email_from="", email_to=[]):
    valid = False

    if email_from != "":
        if re.search(r'[\w.-]+@[\w.-]+.\w+', email_from):
            valid = True

    if len(email_to) > 0:
        for addr in email_to:
            if re.search(r'[\w.-]+@[\w.-]+.\w+', addr):
                valid = True
            else: # needed because we have to check each email in the list
                valid = False

    return valid

def get_unified_benchmark_list():
    """
        Return the BSW KPI/Benchmark list
    """
    bmarks = []
    for benchmark in benchmarks:
        if benchmark.in_unified:
            bmarks.append(benchmark.name)
    return bmarks

def get_benchmarks():
    """Returns a list of available benchmark names"""
    bmarks = []
    for benchmark in benchmarks:
        bmarks.append(benchmark.name)
    return bmarks


def get_time():
    tmd = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime())
    return tmd


def clean_up():
    for f in os.listdir(os.curdir):
        if '.pyc' in f or '.res' in f or \
           '.vms' in f or '.ex' in f or '.txt' in f:
            os.remove(f)

def delete_pkl(pkl_path):
    pkl_found=[]
    for f in os.listdir(pkl_path):
        if re.search(r'\w+-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}.pkl$', f):
            pkl_found.append(f)

    if pkl_found != []:
        for item in pkl_found:
            os.remove(item)

def delete_csv_html(csv_path):
    csv_html_found = []
    for f in os.listdir(csv_path):
        if re.search(r'\w+_\w+_\d{1}_results.html', f):
           csv_html_found.append(f)
        elif re.search(r'\w+_\w+_\d{1}_values.csv', f):
           csv_html_found.append(f)
    if csv_html_found != []:
        for item in csv_html_found:
            os.remove(item)

def archive_pkl(pkl_path):
    pkl_found=[]
    for f in os.listdir(pkl_path):
        if re.search(r'\w+-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}.pkl$', f):
            pkl_found.append(f)

    if pkl_found != []:
        archive_dir = "pkl_archive"+"-"+get_time()
        os.mkdir(archive_dir)
        for item in pkl_found:
            print "Archiving %s to %s..." %(item, archive_dir)
            shutil.copy2(item, os.path.join(pkl_path, archive_dir))
            # check if file got copied and remove original
            if os.path.isfile(os.path.join(pkl_path, archive_dir, item)):
                os.remove(item)


def get_ssh_key():
    return os.path.join(os.path.dirname(__file__),
                        os.path.pardir,
                        os.path.pardir,
                        "third_party",
                        "chromite",
                        "ssh_keys",
                        "testing_rsa")

class GracefulExit(Exception):
     pass

def graceful_exit(signum, frame):
    raise GracefulExit

def reboot_device(cri=None):
    import signal
    signal.signal(signal.SIGTERM, graceful_exit)
    try:
        cri.RunCmdOnDevice(["reboot"], quiet=False)
    except GracefulExit:
        print "GracefulExit exception is raised"
    finally:
        print "Exit from 'reboot' sub-process"

def cros_ssh(remote=None, port=None, identity=None, args=None):
    good_ip = False
    cri = None
    output_strs = []

    if not remote:
        raise ValueError
    else:
        good_ip = check_ip(remote)

    if not identity:
        identity = get_ssh_key()
    if not port:
        port = 22

    if good_ip:
        cri = cros_interface.CrOSInterface(remote,  port, identity)
    else:
        raise socket.error

    if cri:
       cri.TryLogin()
       if "reboot" is ("".join(args)):
           from multiprocessing import Process
           t = Process(target=reboot_device, args=(cri,))
           t.start()
           t.join(timeout=2)
           if t.is_alive():
               t.terminate()
               t.join(timeout=0.1)
           output_strs = [""]
       else:
           output_strs = cri.RunCmdOnDevice(args, quiet=False)
       cri.CloseConnection()

    # output_strs[0] is stdout, output_strs[1] is stderr
    # so we want to return only stdout
    return output_strs[0]


class ChromebookVersion():
    def __init__(self, remote):
        self._remote = remote
        self._cert = get_ssh_key()
        self._output = []
        self._cri = cros_interface.CrOSInterface(self._remote, 22, self._cert)
        self._cri.TryLogin()


    def _run_cmds(self, cmds):
        return self._cri.RunCmdOnDevice(cmds, quiet=False)


    def _get_version(self, cmds, ptrn):
        ver = ''
        ver = self._run_cmds(cmds)
        ver = ver[0] #keep only stdout, disregard stderr
        return re.findall(ptrn, ver)


    def get_firmware_version(self):
        cmds = ["grep", "^version", "/var/log/bios_info.txt"]
        ptrn = "(?<=\|\s)[A-Za-z0-9\._]+"
        res = self._get_version(cmds, ptrn)
        return res[0] if res else None


    def get_build_version(self):
        cmds = ["grep", "^CHROMEOS_RELEASE_VERSION", "/etc/lsb-release"]
        ptrn = "(?<==)[0-9\._]+"
        res = self._get_version(cmds, ptrn)
        return res[0] if res else None


    def get_board_name(self):
        cmds = ["grep", "^CHROMEOS_RELEASE_BOARD", "/etc/lsb-release"]
        ptrn = "(?<==)[a-zA-Z0-9\._]+"
        res = self._get_version(cmds, ptrn)
        return res[0] if res else None


    def get_chrome_version(self):
        cmds = ["/opt/google/chrome/chrome", "-version"]
        ptrn = "(?<=\s)[0-9\.]+"
        res = self._get_version(cmds, ptrn)
        return res[0] if res else None


    def get_cpu_model(self):
        cmds = ["grep", "model\ name", "/proc/cpuinfo", "|", "head", "-1"]
        ptrn = "(?<=:\s).*"
        res = self._get_version(cmds, ptrn)
        return res[0] if res else None


    def get_cpu_max_frequency(self):
        freq_float = None
        cmds = ["cat", "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq"]
        ptrn = "\d+"
        res = self._get_version(cmds, ptrn)

        if res:
            try:
                freq_float = float(res[0])
                freq_float = freq_float / 1000000
                freq_float = round(freq_float, 2)
            except ValueError:
                pass

            return freq_float

        return None


    def get_cpu_cur_frequency(self):
        freq = None
        cmds = ["cat", "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq"]
        ptrn = "\d+"
        res = self._get_version(cmds, ptrn)

        if res:
            try:
                freq = float(res[0])
                freq = freq / 1000000
                freq = round(freq, 2)
            except ValueError:
                pass

            return freq

        return None


    def get_gpu_max_frequency(self):
        freq_float = None
        cmds = ["cat", "/sys/class/drm/card0/gt_max_freq_mhz"]
        ptrn = "\d+"
        res = self._get_version(cmds, ptrn)

        if res:
            try:
                freq_float = float(res[0])
            except ValueError:
                pass

            return freq_float

        return None


    def get_gpu_cur_frequency(self):
        freq = None
        cmds = ["cat", "/sys/devices/pci0000\:00/0000"\
                       "\:00\:02.0/drm/card0/gt_max_freq_mhz"]
        ptrn = "\d+"
        res = self._get_version(cmds, ptrn)

        if res:
            try:
                freq = float(res[0])
            except ValueError:
                pass

            return freq

        return None


    def get_kernel_version(self):
        cmds = ["uname", "-r"]
        ptrn = "[0-9a-zA-Z\.]+"
        res = self._get_version(cmds, ptrn)
        return res[0] if res else None


    def get_firmware_type(self):
        cmds = ["crossystem"]
        ptrn = "backup_nvram_request\s+=\s+\(error\)"
        res = self._get_version(cmds, ptrn)
        # error found means DUT is uEFI
        return "uEFI" if res else "Coreboot"


    def get_screen_resolution(self):
        cmds = ["modetest", "-p"]
        ptrn = "(?<=\()[0-9x]{4,}"
        res = self._get_version(cmds, ptrn)
        return res[0] if res else None


    def get_memory_size(self):
        cmds = ["cat", "/proc/meminfo"]
        ptrn = "(?<=MemTotal:\s)\s+\d+"
        mem_float = None
        res = self._get_version(cmds, ptrn)
        if res:
            try:
                mem_float = float(res[0]) / 1000000
                mem_float = round(mem_float, 2)
            except ValueError:
                pass
            return mem_float

        return None


    def get_memory_channels(self):
        cmds = ["dmidecode", "-t", "memory"]
        ptrn = "Locator: Channel-\d+"
        res = self._get_version(cmds, ptrn)
        if res:
            return len(res)
        elif self.get_memory_size() > 2:
            return 2
        else:
            return 1


    def get_mesa_version(self):
        cmds = ["wflinfo", "-p", "null", "-a", "gles2"]
        ptrn = "(?<=OpenGL\sversion\sstring:\s).*"
        res = self._get_version(cmds, ptrn)
        return res[0] if res else None



def _get_cached_dut_version():
    ver = {}
    if os.path.isfile("dut_version"):
        f = open("dut_version", "r")
        ver = pickle.load(f)
        f.close()
        return ver
    else:
        return None


def write_vars_to_file(my_vars={}):
    f = open("saved_test_vars", "w")
    pickle.dump(my_vars, f)
    f.close()


def get_vars_from_file():
    my_vars = {}

    if os.path.isfile("saved_test_vars"):
        f = open("saved_test_vars", "r")
        my_vars = pickle.load(f)
        f.close()
    else:
        my_vars["ip"] = "0.0.0.0"
        my_vars["from"] = ""
        my_vars["to"] = []

    return my_vars


# checks IP address format
def check_ip(ip):
    retval = False
    s = None

    try:
        s = socket.create_connection((ip, 22), 5)
        retval = True
    except socket.error as e:
        retval = False
        print e

    if s:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
    return retval


def overwrite_dut_info(dut_info={}):
    parser = SafeConfigParser()
    pnp_ini_file = "./pnp.ini"
    if os.path.isfile(pnp_ini_file):
        parser.read(pnp_ini_file)
        has_option_board_name = parser.has_option("board", "board_name")
        has_option_firmware = parser.has_option("board", "firmware")
        if has_option_board_name:
            dut_info['board'] = parser.get('board', 'board_name')
        if has_option_firmware:
            dut_info['firmware'] = parser.get('board', 'firmware')

def replace_none_with_error(dict_dut_info):
    for k in dict_dut_info:
        if dict_dut_info[k] is None:
            dict_dut_info[k] = "No Value Found"

def get_dut_version(ip=''):
    ver = {}
    ssh_cmds = {}

    if not ip:
        ver = _get_cached_dut_version()
        return ver

    if check_ip(ip) == False:
        ver = _get_cached_dut_version()
        return ver

    cv = ChromebookVersion(ip)
    ver = {}
    ver["ip"] = ip
    ver["firmware"] = cv.get_firmware_version()
    ver["build"] = cv.get_build_version()
    ver["board"] = cv.get_board_name()
    ver["basename"] = ver["board"]
    ver["chrome"] = cv.get_chrome_version()
    ver["cpu"] = cv.get_cpu_model()
    ver["cpu_max_freq"] = cv.get_cpu_max_frequency()
    ver["cpu_cur_freq"] = cv.get_cpu_cur_frequency()
    ver["gpu_max_freq"] = cv.get_gpu_max_frequency()
    ver["gpu_cur_freq"] = cv.get_gpu_cur_frequency()
    ver["kernel"] = cv.get_kernel_version()
    ver["firmware_type"] = cv.get_firmware_type()
    ver["screen_resolution"] = cv.get_screen_resolution()
    ver["memory"] = cv.get_memory_size()
    ver["memory_channels"] = cv.get_memory_channels()
    ver["mesa"] = cv.get_mesa_version()

    # overwrite none values while grabbing dut information
    replace_none_with_error(ver)

    # overwrite any DUT info if available via pnp.ini config file
    overwrite_dut_info(ver)

    # cache the version information
    with open("dut_version", "w") as f:
        pickle.dump(ver, f)

    return ver


def perfprint(src, dst, file_mode):
    t = open(dst, file_mode)
    with open(src, 'r') as f:
        pickle = cPickle.load(f)
        t.write("scores\n")
        t.write(str(pickle.result.generateCSVRows()) + '\n')
        t.write("power\n")
        t.write(str(pickle.profiles['extech'].getStats()) + '\n')
        t.write("cpu profiler\n")
        t.write(str(pickle.profiles['vmstat'].getStats()) + '\n')
        f.close()
    t.close()


def totext(perf_dir):
    for b in benchmarks:
        bench_file = b.name
        txt_file = bench_file+".txt"
        file_mode = 'w'
        for filename in glob(os.path.join(os.curdir, bench_file+'*.pkl')):
            perfprint(filename, txt_file, file_mode)
            file_mode = 'a'

def send_pagecycler_alert(valid_files, saved_vars={}):

    subject = "WARNNING: No 3 valid roundis from 10 rounds of Page_Cycler.V2 testing results."

    body = "<p>Only %d valid rounds are found in Page_Cycler.V2 results, \
           fail to find 3 valid rounds from 10 round results.</p>\
           <p>Please check the result from csv manually</p>" \
                       % len(valid_files)
    body += "<p>Below are the valid results:</p>"
    for file_name in valid_files:
        body += "<p>%s</p>" % file_name

    sendTo.send_mail(saved_vars["from"], saved_vars["to"], subject, body, [])

def htmltocsv(executed_benchmarks,perf_dir, saved_vars={}):
    for b in executed_benchmarks:
        bench_file = b
        bench_text = b + ".txt" 
        if b is PAGE_CYCLER_NAME:
            pc_valid_items_dict = {}
            pc_empty_items_dict = {}
            for filename in sorted(glob(os.path.join(os.curdir, bench_file+'*results.html'))):
                histogram_items = histograms.parse_result_file(b, filename)
                csv_file  = filename.replace("_results.html", "_values.csv")
                histograms.savetocsv(csv_file, histogram_items)
                is_valid = True
                for item in histogram_items:
                    value = item.get_digital_value()
                    if value < 0.0001:
                        is_valid = False
                        break
                if is_valid :
                    pc_valid_items_dict[filename] = histogram_items
                else:
                    pc_empty_items_dict[filename] = histogram_items
            if len(pc_valid_items_dict.keys()) >= 3:
                result_index = 0
                for valid_round in sorted(pc_valid_items_dict.keys()):
                    print "Pick result from %s" % valid_round
                    histograms.updatetext(result_index, bench_text, \
                          pc_valid_items_dict[valid_round], b)
                    if result_index == 2:
                        break
                    result_index += 1
            else:
                #Send warnning email
                send_pagecycler_alert(pc_valid_items_dict.keys(), saved_vars)
                print "Only %d valid rounds are found in Page_Cycler.V2 results, \
                       fail to find 3 valid rounds from 10 round results.\
                       Please check the result from csv manually" \
                       % len(pc_valid_items_dict.keys())
                for valid_round in pc_valid_items_dict.keys():
                    print "%s is valid." % valid_round
        else:
            i = 0
            for filename in glob(os.path.join(os.curdir, bench_file+'*results.html')):
                csv_file  = filename.replace("_results.html", "_values.csv")
                histogram_items = histograms.parse_result_file(b, filename)
                histograms.savetocsv(csv_file, histogram_items)
                histograms.updatetext(i, bench_text, histogram_items, b)
                i += 1

def _find_fping():
    fping_path = ""

    # Is fping installed?
    try:
        fping_path = sp.check_output("which fping", shell=True).rstrip()
    except sp.CalledProcessError as e:
        print "ERROR: fping not found"
        print "ERROR: fping required to get new DUT IP address after reboot"
        print "Install fping using your distro's preferred method"
        print "On Ubuntu: sudo apt-get install fping"
        print "On Fedora: sudo yum install fping"
        return ""

    return fping_path


def _update_arp_cache(ip):
    # Make sure fping is installed.
    fping_cmd = _find_fping()
    if fping_cmd == "":
        return False

    subnet = '.'.join(ip.split(".")[0:3]) + ".0/24"
    cmd = fping_cmd + " -q -c 1 -g " + subnet

    try:
        # Run fping to fill the arp cache, ignore output
        with open(os.devnull, 'w') as fp:
            sp.check_call(cmd, stdout=fp, stderr=fp, shell=True)
    except sp.CalledProcessError as e:
        # returncodes 1 and 2 are not true failures.
        if e.returncode > 2:
            return False

    return True


# Update the arp cache, then search the cache for the given
# IP address, returning the corresponding MAC address.
def get_mac_for_ip(ip, sleep_secs, retries):

    while retries:
        if not _update_arp_cache(ip):
            return ""

        try:
            f = open("/proc/net/arp", "r")
        except:
            return ""

        for line in f.readlines():
            addrline = line.rstrip().split()
            if addrline[0] == ip:
                return addrline[3]

        f.close()
        time.sleep(sleep_secs)
        retries -= 1

    return ""


# Update the arp cache, then search the cache for the given
# MAC address, returning the corresponding IP address.
def get_ip_for_mac(mac, ip, sleep_secs, retries):

    while retries:
        # Update the arp cache
        if not _update_arp_cache(ip):
            return ""

        try:
            f = open("/proc/net/arp", "r")
        except:
            return ""

        for line in f.readlines():
            addrline = line.rstrip().split()
            if addrline[3] == mac:
                return addrline[0]

        f.close()
        time.sleep(sleep_secs)
        retries -= 1

    return ""


# Check known_hosts file for DUT's ssh key.
# If not found, get it and update known_hosts.
def check_ip_key(ip):
    print "checking ip " + ip
    known_hosts = os.path.expanduser("~") + "/.ssh/known_hosts"
    keyscan = "ssh-keyscan -H " + ip
    keygen = "ssh-keygen -F " + ip

    # Check known_hosts for key.
    if os.path.isfile(known_hosts):
        try:
            p = sp.Popen(keygen, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
        except:
            pass

        if len(p.stdout.read()) > 1:
            # Found it
            return True

    # Didn't find key, so update known_hosts.
    try:
        p = sp.Popen(keyscan, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    except Exception as e:
        print "ERROR:", e
        return False

    stdout = p.stdout.read()

    if stdout == "":
        print "ERROR:", p.stderr.readline().rstrip()
        return False

    f = open(known_hosts, 'a')
    f.write(stdout)
    f.close()

    return True


# Check if devserver is running and if not start it
def is_devserver_running():
    result = False

    for p in psutil.process_iter():
        if "start_devserver" in str(p.name):
            result = True

    if result is False:
        try:
            mshell = "cros_sdk start_devserver &"
            os.system(mshell)
            result = True
        except OSError as o:
            print o
            result = False

    return result


def pingDut(ip, wait_secs, retries):
    dut_alive = False
    wait_max = wait_secs * retries
    wait_total = 0

    while not dut_alive and wait_total < wait_max:
        """ Wait up to 'retries' times 'wait_secs' seconds
            for DUT to become available. In normal situations,
            it should only take a few iterations.
            Note that create_connection can throw an exception
            for reasons other than a timeout, so we account for
            that by tracking total wait time and only giving
            up after total wait time exceeds max wait time. """
        wait_remaining = wait_max - wait_total
        if wait_remaining < wait_secs:
            wait_secs = wait_remaining
        t1 = time.time()
        try:
            socket.create_connection((ip, 22), wait_secs)
            dut_alive = True
        except socket.error:
            # Errors are expected while waiting for the DUT to boot,
            # so ignore them here.
            pass

        wait_total += time.time() - t1

    return dut_alive


def cleanupPower(pValue):
    import signal
    # Get the out of ps -A and break it down
    # into lines.
    p = sp.Popen(['ps', '-A'], stdout=sp.PIPE)
    out, error = p.communicate()

    # Loop through the broken down items in ps -A
    # to see if we find a match to kill.
    for line in out.splitlines():
        if pValue in line:
            pid = int(line.split(None, 1)[0])
            os.kill(pid, signal.SIGKILL)

def cleanup(pname):
    mypid = os.getpid()
    find_pname = "pgrep -aP %d" %mypid
    p = sp.Popen(find_pname, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True)
    for line in iter(p.stdout.readline, b''):
        if pname in line:
            try:
                ID = int(line.split(" ")[0])
            except ValueError as e:
                print e
                #invalud power values are caused by poweranaylzer not being killed properly
                if "poweranalyzer" in pname:
                    print "WARNING: This will cause invalid power values!"
                break
            if ( ID > 0):
                try:
                    sp.call("kill -9 %d"%ID, shell=True)
                except OSError:
                    pass
    return 0

def copy_archive_to_server(server, comp_file, ssh_user=None):
    # The user account pnp_automation has been disabled.
    # The upload path has been removed.
    # PNP archives were given to Shaofeng Tang <shaofeng.tang@intel.com>
    return False

    if not server:
        return False
    if not comp_file:
        return False

    board = comp_file.split('-')[0]

    gt = time.gmtime()
    year = str(gt[0])

    ww_int = date(gt[0], gt[1], gt[2]).isocalendar()[1]
    if ww_int < 10:
        ww = '0' + str(ww_int)
    else:
        ww = str(ww_int)

    # results dir name
    dir_name = ''.join([year, '.', ww, '.',
                        str(datetime.datetime.today().weekday() + 1)])

    if not ssh_user:
        ssh_user = "pnp_automation"
    connect = 'ssh %s@%s' %(ssh_user, server)

    # cmd to check if year exists
    check_year = 'if [ ! -d \"www/PnP/%s\" ];' %(year)\
                 +' then mkdir www/PnP/%s; fi' %year

    # cmd to check if board exists
    check_board = 'if [ ! -d \"www/PnP/%s/%s\" ];'%(year,board)\
                  +' then mkdir www/PnP/%s/%s; fi' %(year, board)

    # check if archive dir exists
    check_arch = 'if [ ! -d \"www/PnP/%s/%s/'%(year, board)\
                 +'%s\" ]; then mkdir www/PnP/%s' %(dir_name, year)\
                 +'/%s/%s; fi' %(board, dir_name)

    # copy archive
    scp_arch = 'scp %s pnp_results.html *.csv %s@%s:~/' %(comp_file, ssh_user, server)
    cp_arc_dest = 'mv ~/%s www/PnP/%s/%s/%s' %(comp_file, year, board,
                 dir_name)
    cp_pnp_dest = 'mv ~/pnp_results.html www/PnP/%s/%s/%s'%(year,
                  board, dir_name)
    cp_csv_dest = 'mv ~/*.csv www/PnP/%s/%s/%s'%(year, board, dir_name)

    # parse results for web
    prs = 'cd ~/www/PnP; ./pnp_res_parse.py --weekly_path=%s/%s/%s'\
           %(year, board, dir_name)

    # expand files
    ex_arc = 'tar -xjvf %s' %comp_file
    cd_ex_arc = 'cd www/PnP/%s/%s/%s; %s' %(year, board, dir_name, ex_arc)

    sp.call(connect + ' "%s; %s; %s"' %(check_year,
                                        check_board,
                                        check_arch),
                                        shell=True)

    sp.call(scp_arch, shell=True)

    sp.call(connect + ' "%s; %s; %s; %s; %s"' %(cp_arc_dest, cp_pnp_dest,
                                            cp_csv_dest, cd_ex_arc, prs), shell=True)


def check_cpu_turbo(ip):
    res = None
    ver = _get_cached_dut_version()

    if not ver:
        ver = get_dut_version(ip)

    if ver:
        try:
            if ver["cpu_cur_freq"] <= ver["cpu_max_freq"]:
                res = "Enabled"
            else:
                res = "Disabled"
        except KeyError:
            return None

    return res


def check_gpu_turbo(ip):
    res = None
    ver = _get_cached_dut_version()

    if not ver:
        ver = get_dut_version(ip)

    if ver:
        try:
            if ver["gpu_cur_freq"] <= ver["gpu_max_freq"]:
                res = "Enabled"
            else:
                res =  "Disabled"
        except KeyError:
            return None

    return res

