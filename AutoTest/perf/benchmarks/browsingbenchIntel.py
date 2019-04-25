# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys
import time

from telemetry import benchmark
from telemetry.core import util
from telemetry import page as page_mod
from telemetry import story
from telemetry.page import legacy_page_test

import profiler as pro
import bench_settings

VMSRate = '1'
PARate = '1'

#class BrowsingBenchIntelMeasurement(page_mod.page_test.PageTest):
class BrowsingBenchIntelMeasurement(legacy_page_test.LegacyPageTest):

    def ValidateAndMeasurePage(self, page, tab, results):
        for arg in sys.argv:
            if 'remote' in arg:
                pro.VMSCommand[3] = 'root@' + arg.split('=')[1]

        pro.VMSCommand[5] = VMSRate
        pro.PACommand[2] = PARate
        vms = pro.profiler(pro.VMSCommand)
        pa = pro.profiler(pro.PACommand)
        pa.start('browsingbenchIntel.ex')
        vms.start('browsingbenchIntel.vms')

        tab.EvaluateJavaScript("go('user')")
        time.sleep(2)
        tab.EvaluateJavaScript("document.forms['complianceTest'][0].value='Yes'")
        tab.EvaluateJavaScript("document.forms['complianceTest'][1].value='Red'")

        tab.EvaluateJavaScript("verify_form()")
        tab.WaitForJavaScriptCondition('window.location.search.indexOf("phase=results") >= 0', timeout=2400)
        #tab.WaitForJavaScriptExpression('window.location.search.indexOf("phase=results") >= 0', 2400)

        vms.stop()
        pa.stop()

        js_get_results = """

var results = {};
var bb_scoretxt = document.getElementById("score-std").innerHTML;
var bb_score = bb_scoretxt.substring(bb_scoretxt.indexOf(":") + 1);
bb_score = bb_score.replace(/\s+/g,'');
results['score'] = bb_score.split("/")[0];
JSON.stringify(results);
"""
        result_dict = eval(tab.EvaluateJavaScript(js_get_results))
        print "{0}, {1},".format('score', result_dict['score'])
        del result_dict['score']
        for key, value in result_dict.iteritems():
            print "{0}, {1},".format(key, value)

class BrowsingBenchIntel(benchmark.Benchmark):
    """Browsing bench"""
    test = BrowsingBenchIntelMeasurement

    def CreateStorySet(self, options):
        try:
           mbm = __main__.bm
        except NameError:
           mbm = bench_settings.bench_mapping()
        _URL = mbm.get_bench_URL('browsingbenchIntel')
        ps = story.StorySet(base_dir=os.path.dirname(__file__))
        ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name='browsingbenchIntel'))
        return ps
