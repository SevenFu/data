#   AUTHOR: Matthew S. Atwood <matthew.s.atwood@intel.com>
import os
import subprocess
import signal
import sys
try:
    from subprocess import DEVNULL # > python 3.x
except ImportError:
    DEVNULL = open(os.devnull, 'r')
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
import pnp_util

try:
    ### EXTECH environment variable specifies that Extech 308083 is prsent
    extech_present = os.environ['EXTECH']
except KeyError:
    extech_present = 0

platID = pnp_util.get_ssh_key()

VMSCommand = ['/usr/bin/ssh',
              '-i',
              platID,
              '',
              'vmstat',
              '']

PACommand = ['./poweranalyzer', '-r', '']

class profiler:
    def __init__(self, command):
        self.cmd = command
        self.pid = None
        self.op = 0
        ### profiler should only operate if its vms profiler, or if it is
        ### the PA profiler with the extech device

        if os.path.isfile(platID) == False:
            print "Error: " + platID + " not found!"
            sys.exit()

        if (self.cmd[0] == PACommand[0] and extech_present) or (self.cmd[0] == VMSCommand[0]):
            self.op = 1

    def start(self, fileName):
        if self.op:
            self.output = open(fileName, 'w')
            self.pid = subprocess.Popen(self.cmd, executable=self.cmd[0],
                                        stdout=self.output, stdin=DEVNULL)

    def stop(self):
        if self.op:
            self.output.flush()
            self.output.close()
            if self.pid == None:
                return
            else:
                self.pid.send_signal(signal.SIGINT)

