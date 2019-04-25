# Copyright 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys

from telemetry import benchmark
from telemetry import page as page_mod
from telemetry import story
from telemetry.page import legacy_page_test

import profiler as pro
import bench_settings

VMSRate = '1'
PARate = '1'

#class KrakenIntelMeasurement(page_mod.page_test.PageTest):
class KrakenIntelMeasurement(legacy_page_test.LegacyPageTest):

    def ValidateAndMeasurePage(self, page, tab, results):
        for arg in sys.argv:
            if 'remote' in arg:
                pro.VMSCommand[3] = 'root@' + arg.split('=')[1]

        pro.VMSCommand[5] = VMSRate
        pro.PACommand[2] = PARate
        vms = pro.profiler(pro.VMSCommand)
        pa = pro.profiler(pro.PACommand)
        pa.start('krakenIntel.ex')
        vms.start('krakenIntel.vms')

        tab.WaitForJavaScriptCondition('document.title.indexOf("Results") != -1', timeout=700)
        #tab.WaitForJavaScriptExpression('document.title.indexOf("Results") != -1', 700)
        tab.WaitForDocumentReadyStateToBeComplete()

        vms.stop()
        pa.stop()

        js_get_results = """
var results = {};
function krakenparse(target)
{
    var res=target.replace(/\s+/g, '');
    res = res.replace(/^.*:/,'');
    return res.replace(/ms.*/,'');
}

var raw = document.getElementById('console').innerHTML;
var rawSplit = raw.split("<br>");
results['total'] = krakenparse(rawSplit[4]);
results['ai'] = krakenparse(rawSplit[7]);
results['astar'] = krakenparse(rawSplit[8]);
results['audio'] = krakenparse(rawSplit[10]);
results['beat-detection'] = krakenparse(rawSplit[11]);
results['dft'] = krakenparse(rawSplit[12]);
results['fft'] = krakenparse(rawSplit[13]);
results['oscillator'] = krakenparse(rawSplit[14]);
results['imaging'] = krakenparse(rawSplit[16]);
results['gaussian-blur'] = krakenparse(rawSplit[17]);
results['darkroom'] = krakenparse(rawSplit[18]);
results['desaturate'] = krakenparse(rawSplit[19]);
results['json'] = krakenparse(rawSplit[21]);
results['parse-financial'] = krakenparse(rawSplit[22]);
results['stringify-tinderbox'] = krakenparse(rawSplit[23]);
results['stanford'] = krakenparse(rawSplit[25]);
results['crypto-aes'] = krakenparse(rawSplit[26]);
results['crypto-ccm'] = krakenparse(rawSplit[27]);
results['crypto-pbkdf2'] = krakenparse(rawSplit[28]);
results['crypto-sha256-iterative']=krakenparse(rawSplit[29]);
JSON.stringify(results)
"""
        result_dict = eval(tab.EvaluateJavaScript(js_get_results))
        print '{0}, {1},'.format('total', result_dict['total'])
        del result_dict['total']
        for key, value in result_dict.iteritems():
            print "{0}, {1},".format(key, value)

class KrakenIntel(benchmark.Benchmark):
    """Mozilla's Kraken JavaScript benchmark."""
    test = KrakenIntelMeasurement

    def CreateStorySet(self, options):
        try:
           mbm = __main__.bm
        except NameError:
           mbm = bench_settings.bench_mapping()
        _URL = mbm.get_bench_URL('krakenIntel')
        ps = story.StorySet(base_dir=os.path.dirname(__file__))
        ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name='krakenIntel'))
        return ps
