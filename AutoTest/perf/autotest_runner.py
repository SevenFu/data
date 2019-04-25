import os
import sys
import time
from benchmarks import profiler as pro
from benchmarks import bench_settings
import subprocess as sp
import re
import cPickle
from time import gmtime, strftime
import perfstats as ps
import pnp_util as pu
import psutil
import ip_finder
from time import sleep
from collections import namedtuple
import result_libs

PARate = '1'

ResultLabel = namedtuple('ResultLabel', ['names', 'patterns'])

workloads = {}

cm_res = result_libs.CoremarkIntelResults()
cx_res = result_libs.CrXprtIntelResults()
st_res = result_libs.StreamIntelResults()
sp_res = result_libs.SpecIntelResults()
pb_res = result_libs.BootPerfResults()
glm_res = result_libs.Glmark2Results()
glb_res = result_libs.GlbenchResults()

workloads['hardware_CoremarkIntel'] = ResultLabel(cm_res.labels, cm_res.pattern)
workloads['hardware_StreamIntel'] = ResultLabel(st_res.labels, st_res.pattern)
workloads['hardware_SpecIntel'] = ResultLabel(sp_res.labels, sp_res.pattern)
workloads['platform_BootPerf'] = ResultLabel(pb_res.labels, pb_res.pattern)
workloads['graphics_CrXprtIntel'] = ResultLabel(cx_res.labels, cx_res.pattern)
workloads['graphics_GLMark2'] = ResultLabel(glm_res.labels, glm_res.pattern)
workloads['graphics_GLBench'] = ResultLabel(glb_res.labels, glb_res.pattern)

class AutotestError(Exception):
    def __init__(self, val):
        self.val = val

    def __str__(self):
        return repr(self.val)

class AutotestWorkload:
    def __init__(self, workload, dut_ip):
        self.workload = workload
        self.ip = dut_ip
        self.test_output = ''
        self.time = strftime('%Y-%m-%d-%H-%M', gmtime())
        self.label = workload + '-' + self.time
        self.res = self.label + '.res'

        try:
            self.mbm = __main__.bm
        except NameError:
            self.mbm = bench_settings.bench_mapping()

    def _cleanup(self):
        for fileName in os.listdir(os.getcwd()):
            if self.label in fileName and '.pkl' not in fileName:
                os.remove(fileName)


    def _rename_tmp_files(self):
        for fileName in os.listdir(os.getcwd()):
            if self.workload+'-' not in fileName:
                if self.workload in fileName and '.pkl' not in fileName:
                    os.rename(fileName, self.label + '.'\
                              + fileName.split('.')[1])

    def _get_test_that_args(self):
        """Returns workload unique test_that arguments"""
        args = ''

        if self.workload is 'graphics_CrXprtIntel':
            args = 'extension_url=' + self.mbm.get_bench_URL(self.workload)

        return args

    # add autotest to the Chromebook
    def _install_autotest_workload(self):
        ip_obj = ip_finder.IPFinder()
        server_ips = ip_obj.get_ip()
        stat_file_cmd = ''

        if "hardware_CoremarkIntel" in self.workload:
            package = 'coremark'
        elif "hardware_StreamIntel" in self.workload:
            package = 'stream'
        elif "hardware_SpecIntel" in self.workload:
            package = 'spec'
        else:
            package = ''

        success_pattern = "dev-util/%s-\d{4}.\d+.\d+\smerged." %package
        file_not_found = "cannot\s+stat"


        if package == 'spec':
            stat_file_cmd = ["stat", "/opt/%s/execute_spec_cros.sh"&package,
                             "2>&1"]
        else:
            stat_file_cmd = ["stat", "/opt/%s/%s"%(package, package),
                             "2>&1"]

        non_rw_ptrn = "mount:\s+\w+\s+\w+\s+\w+\s+read-write,\s+\w+\s+write-protected"
        make_read_write = ["/usr/share/vboot/bin/make_dev_ssd.sh", "--force",
                           "--remove_rootfs_verification", "--partitions", "2"]
        test_rw_cmd = ["mount", "-o", "remount", "rw", "/", "2>&1"]

        p = pu.cros_ssh(remote=self.ip, args=test_rw_cmd)
        # remove the new line character
        p = p[:-1]
        if re.findall(non_rw_ptrn, p):
            pu.cros_ssh(remote=self.ip, args=make_read_write)
            sleep(10) # give it time to disable rootfs_verification
            pu.cros_ssh(remote=self.ip, args=["reboot"])
            sleep(10) # give it a chance to reboot before checking connection
            if pu.pingDut(self.ip, 8, 10) is False:
                return False

        # first check if autotest was already installed
        p = pu.cros_ssh(remote=self.ip, args=stat_file_cmd)
        # remove the new line character
        p = p[:-1]
        if re.findall(file_not_found, p):
            for ip_str in server_ips:
                # spec doesn't fit on the /dev/root partition so we need to
                # make room in /usr/local/tmp
                if package == "spec":
                    make_tmp_opt_dir = ["mkdir", "/usr/local/tmp/opt"]
                    make_tmp_spec_dir = ["mkdir", "/usr/local/tmp/opt/spec"]
                    make_sym_link = ["ln", "-s", "/usr/local/tmp/opt/spec",
                                     "/opt/spec"]

                    pu.cros_ssh(remote=self.ip, args=make_tmp_opt_dir)
                    pu.cros_ssh(remote=self.ip, args=make_tmp_spec_dir)
                    pu.cros_ssh(remote=self.ip, args=make_sym_link)

                gmerge = ["gmerge", "-d", "http://%s:8080"%ip_str,
                          "%s"%package, "2>&1", "--accept_stable"]
                p = pu.cros_ssh(remote=self.ip, args=gmerge)
                # remove the new line character
                p = p[:-1]
                if re.findall(success_pattern, p):
                    break

        return True


    def start(self):
        res = []

        if pu.is_devserver_running():
            if not self._install_autotest_workload():
                raise AutotestError("Error: Unable to install %s"%self.workload)

        pro.PACommand[2] = PARate
        pa = pro.profiler(pro.PACommand)
        # start measuring power
        pa.start(self.workload+'.ex')

        test_that_args = ["cros_sdk", "--no-ns-pid", "--", "test_that",
                          "--args='%s'" % (self._get_test_that_args()),
                          self.ip, self.workload]
        try:
            p = sp.Popen(test_that_args, shell=False, stdout=sp.PIPE)
            self.test_output = p.stdout.read()[:-1]
        except OSError as o:
            print o

        pa.stop() # stop measuring power

        # Race condition on some dev boxes cause the .pkl file to
        # get created before the .ex file is written. An ugly sleep delay
        # might help
        sleep(2)

        # Ensure poweranalyzer is not running anymore
        process_list = psutil.process_iter()
        for p in process_list:
            pname = ""
            if psutil.__version__ < "2.0.0":
                pname = p.name
            else:
                pname = p.name()
            if "poweranalyzer" in pname:
                pu.cleanup("poweranalyzer")

        self._rename_tmp_files()

        result_ptrn = ""
        for name in workloads[self.workload].names:
            result_ptrn = name + workloads[self.workload].patterns
            res = re.findall(result_ptrn, self.test_output)
            if res:
                if self.workload == "hardware_SpecIntel":
                    for item in res:
                        res_values = re.findall(workloads[self.workload]\
                                                .patterns, item)
                        res_val = res_values[0].split('\'')[1]
                        res_time = res_values[0].split('\'')[3]
                        res_str_val = name+' Value'+', ' + res_val+','
                        res_str_time = name+' Time'+', ' + res_time+','
                        with open(self.res, 'a') as r:
                            r.write(res_str_val+'\n')
                            r.write(res_str_time+'\n')
                else:
                    s = res[0]
                    res_str = s.split(' ')[0] + ', ' + s.split(' ')[-1] + ','
                    with open(self.res, 'a') as r:
                        r.write(res_str+'\n')
            else:
                print "="*100
                print "WARNING: No results found for label " + name
                print "="*100

            pl = ps.PayloadPickle(self.label)
            with open(self.label+'.pkl', 'wb') as fp:
                cPickle.dump(pl, fp)

        self._cleanup()
