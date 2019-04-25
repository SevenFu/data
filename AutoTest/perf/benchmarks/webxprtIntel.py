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

#class webxprtIntelMeasurement(page_mod.page_test.PageTest):
class webxprtIntelMeasurement(legacy_page_test.LegacyPageTest):
    def ValidateAndMeasurePage(self, page, tab, results):
        for arg in sys.argv:
            if 'remote' in arg:
                pro.VMSCommand[3] = 'root@' + arg.split('=')[1]

        pro.VMSCommand[5] = VMSRate
        pro.PACommand[2] = PARate
        vms = pro.profiler(pro.VMSCommand)
        pa = pro.profiler(pro.PACommand)
        pa.start('webxprtIntel.ex')
        vms.start('webxprtIntel.vms')

        tab.EvaluateJavaScript("document.getElementById('username').value='chronos'")
        tab.EvaluateJavaScript("document.getElementById('pwd').value='test0000'")
        tab.EvaluateJavaScript("onLogin();document.forms[0].submit();")
        #tab.WaitForJavaScriptExpression('window.location.pathname.indexOf("index.php") >= 0', 1200)
        tab.WaitForJavaScriptCondition('window.location.pathname.indexOf("index.php") >= 0', 
             timeout=1200)

        time.sleep(5)

        tab.EvaluateJavaScript("onClickstart()")
        #tab.WaitForJavaScriptExpression('window.location.pathname.indexOf("results.php") >= 0', 1200)
        tab.WaitForJavaScriptCondition('window.location.pathname.indexOf("results.php") >= 0', 
             timeout=1200)

        vms.stop()
        pa.stop()

        js_get_results = """

var results = {};
var result_divs = document.querySelectorAll('.ui-bar.ui-bar-c');
for (var i = 2; i<6; i++) {
    var txt = result_divs[i].textContent.trim();
    var n = txt.indexOf(":");
    if(n > 0) {
        var key = txt.slice(0,n);
        results[key] = txt.slice(n+1).trim().split(' +')[0];
    }
}
var webxprt_score = document.getElementsByClassName("scoreDiv")[0].innerHTML;
results['score'] = webxprt_score.split(' +')[0];
JSON.stringify(results);
"""
        result_dict = eval(tab.EvaluateJavaScript(js_get_results))
        print "{0}, {1},".format('score', result_dict['score'])
        del result_dict['score']
        for key, value in result_dict.iteritems():
            print "{0}, {1},".format(key, value)

class webxprtIntel(benchmark.Benchmark):
    """Principle Technology's WebXPRT v1.01 benchmark."""
    test = webxprtIntelMeasurement

    def CreateStorySet(self, options):
        try:
           mbm = __main__.bm
        except NameError:
           mbm = bench_settings.bench_mapping()
        _URL = mbm.get_bench_URL('webxprtIntel')
        ps = story.StorySet(base_dir=os.path.dirname(__file__))
        ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name='webxprtIntel'))
        return ps
