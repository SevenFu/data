# This file contains the definitions for ports, servers, and URI options to
# execute power test benchmarks
# To improve automation and reduce network lag and errors, most of these
# benchmarks have been rehosted to one or more servers inside Intel.
# Therefore, both the benchmark server and invocation information can vary.
# A 'metaset' is a group of servers

# bpxxx is the dictionary of port-and-options by metaset and
# bsxxx is the dictionary of server-names for a given server definition
# Currently, server metasets are {'a':'standard', 'b':'legacy', 'c':'custom'}
# Currently, server base URLs are hard-coded as serv['standard'] and serv['legacy']

import os
import pickle

class bench_mapping(object):
    def __init__(self):
        self.metasets = {'a': 'standard', 'b': 'legacy', 'c': 'custom'}
        self.bpstd = {'streamingVP9Intel': ':7000/',
                     'unityIntel': ':7022',
                     'canvasearthIntel': ':7001/Canvas2D-earth/canvas_earth.html',
                     'earthscreenIntel': ':7001/WebGL-EarthScreen/index.html',
                     'angrybirdsIntel': ':7002/ab.html',
                     'fishietankIntel': ':7006/',
                     'krakenIntel': ':7008/kraken-1.1/driver.html',
                     'octaneV2New': ':7039/?auto=1',
                     'sunspiderV1Intel': ':7011/sunspider-1.0.2/driver.html',
                     'webglaquariumV3Intel': ':7013/aquarium/aquarium.html',
                     'robohornetIntel': ':7016/',
                     'pageloaderIntel': ':7017/iterations_rev11.html',
                     'webxprtIntel': ':7018/login.php',
                     'webxprt2015Intel': ':7020/',
                     'browsingbenchIntel': ':7019/bench/website_bench.php',
                     'graphics_CrXprtIntel': ':7021/zip'}
        self.bpleg = {'angrybirdsIntel': '/html5-workloads/angryBirds/ab.html',
                     'unityIntel': '/unity3d-release/index.html',
                     'browsingbenchIntel': '/bench/website_bench.php',
                     'canvasearthIntel': '/benchmarks/WRTBench_Packages' +
                                         '/WRTBench_latest_project/' +
                                         'Canvas2D-earth/canvas_earth.html',
                     'earthscreenIntel': '/earthscreen/index.html',
                     'fishietankIntel': '/fishietank/',
                     'krakenIntel': '/kraken/kraken-1.1/driver.html',
                     'octaneV2New': '/octane-v2/index.html?auto=1',
                     'pageloaderIntel': '/umgpageload/iterations_rev11.html',
                     'robohornetIntel': ':9000/',
                     'streamingVP9Intel': '/yahvp/',
                     'sunspiderV1Intel': '/sunspider/sunspider-1.0.2/driver.html',
                     'webglaquariumV3Intel': '/webglsamples/aquarium/aquarium.html',
                     'webxprtIntel': '/webxprt/v1dot01/login.php'}
        self.bsleg = {'angrybirdsIntel': 'http://html5soc.jf.intel.com',
                     'browsingbenchIntel': 'http://stocsocros-bb.jf.intel.com',
                     'canvasearthIntel': 'http://pnp.sh.intel.com'}
        self.bsstd = {}
        self.serv = {}
        self.serv['standard'] = 'http://otc-chromeos-media.jf.intel.com'
        self.serv['legacy'] = 'http://stocsocros.jf.intel.com'
        self.serv['custom'] = ''

    def get_serv_URL(self, name):
        if name == 'custom':
            my_vars = {}
            if os.path.isfile("saved_test_vars"):
                f = open("saved_test_vars", "r")
                my_vars = pickle.load(f)
                f.close()
                try:
                    self.serv['custom'] = my_vars['url']
                except KeyError:
                    self.serv['custom'] = self.serv['standard']
            else:
                self.serv['custom'] = "ERROR: Missing file saved_test_vars"
        try:
          ul = self.serv[name]
        except KeyError:
          print "WARNING: SERVER [" + name + "] has no URL defined."
          ul = self.serv['standard']
        return ul

    def get_metasets(self):
        return self.metasets

    def get_bench_URL(self, bnch):
        my_vars = {}

        if os.path.isfile("saved_test_vars"):
            f = open("saved_test_vars", "r")
            my_vars = pickle.load(f)
            f.close()
            try:
                self.serv['custom'] = my_vars['url']
            except KeyError:
                self.serv['custom'] = self.serv['standard']
        else:
            # hard code the default testserver to the first in the list
            # AND DO NOT make the first one in the list be 'custom'.
            my_vars["ts"] = self.metasets['a']

        try:
            ts = my_vars["ts"]
        except KeyError:
            ts = self.metasets['a']

        if ts == 'legacy':
           try:
              lh = self.bpleg[bnch]
           except KeyError:
              print "ERROR: UNKNOWN BENCHMARK [" + bnch + "]"
              return ""
           try:
              uh = self.bsleg[bnch]
           except KeyError:
              uh = self.serv['legacy']
        elif ts == 'custom':
           try:
               lh = self.bpstd[bnch]
           except KeyError:
              print "ERROR: UNKNOWN BENCHMARK [" + bnch + "]"
              return ""
           try:
              uh = self.serv['custom']
           except KeyError:
              uh = self.serv['standard']
        else:
           try:
              lh = self.bpstd[bnch]
           except KeyError:
              print "ERROR: UNKNOWN BENCHMARK [" + bnch + "]"
              return ""
           try:
              uh = self.bsstd[bnch]
           except KeyError:
              uh = self.serv['standard']

        rv = uh + lh

        return rv


# otc-chromeoslab1 original port definitions, no additional options.
#
# bport['yahvp'] = '7000'           # streamingVP9
# bport['wrtbench'] = '7001'       # earthscreen and canvasearth
# bport['angrybirds'] = '7002'
# bport['browser_i'] = '7003'       # NO MATCHING BENCHMARK
# bport['cuttherope'] = '7004'      # NO MATCHING BENCHMARK
# bport['fishietank'] = '7006'
# bport['kraken'] = '7008'
# bport['octane'] = '7009'
# bport['octane-v1'] = '7010'
# bport['sunspider'] = '7011'
# bport['testdrive'] = '7012'
# bport['webglsamples'] = '7013'         # for the webglaquarium calls
# bport['octanertc'] = '7015'  # this is appRTC + Octane 2.0 -- no specific benchmark for this. //
# bport['robohornet'] = '7016'
# bport['umgpageload'] = '7017'
# bport['webxprt'] = '7017'
# bport['BrowsingBench.v1447'] = '7019'
