# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys

from telemetry import benchmark
from telemetry.core import util
from telemetry import page as page_mod
from telemetry import story
from telemetry.page import legacy_page_test

import profiler as pro
import bench_settings

VMSRate = '1'
PARate = '1'

#class OctaneV2IntelMeasurement(page_mod.page_test.PageTest):
class OctaneV2IntelMeasurement(legacy_page_test.LegacyPageTest):

    def ValidateAndMeasurePage(self, page, tab, results):
        for arg in sys.argv:
            if 'remote' in arg:
                pro.VMSCommand[3] = 'root@' + arg.split('=')[1]
        pro.VMSCommand[5] = VMSRate
        pro.PACommand[2] = PARate
        vms = pro.profiler(pro.VMSCommand)
        pa = pro.profiler(pro.PACommand)
        pa.start('octaneV2Intel.ex')
        vms.start('octaneV2Intel.vms')
        tab.WaitForJavaScriptCondition(
             'completed && !document.getElementById("progress-bar-container")',
             timeout=1200)
        #tab.WaitForJavaScriptExpression(
        #    'completed && !document.getElementById("progress-bar-container")',
        #    1200)
       
        vms.stop()
        pa.stop()
        js_get_results = """
var results = {};
var result_divs = document.querySelectorAll('.p-result');
for (var r in result_divs) {
    if (result_divs[r].id && result_divs[r].id.indexOf('Result-') == 0) {
        var key = result_divs[r].id.replace('Result-', '');
        results[key] = result_divs[r].innerHTML;
    }
}
var main_banner = document.getElementById("main-banner").innerHTML;
var octane_score = main_banner.substr(main_banner.lastIndexOf(':') + 2);
results['score'] = octane_score;
JSON.stringify(results);
"""
        result_dict = eval(tab.EvaluateJavaScript(js_get_results))
        print "{0}, {1},".format('score', result_dict['score'])
        del result_dict['score']
        for key, value in result_dict.iteritems():
            print "{0}, {1},".format(key, value)

class OctaneV2Intel(benchmark.Benchmark):
    """Google's Octane JavaScript benchmark."""
    test = OctaneV2IntelMeasurement

    def CreateStorySet(self, options):
        try:
           mbm = __main__.bm
        except NameError:
           mbm = bench_settings.bench_mapping()
        _URL = mbm.get_bench_URL('octaneV2Intel')
        ps = story.StorySet(base_dir=os.path.dirname(__file__))
        ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name='octaneV2Intel'))
        return ps
