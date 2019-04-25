# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys
import time
import json
from core import path_util
from core import perf_benchmark

from telemetry import benchmark
from telemetry import page as page_mod
from telemetry.value import scalar
from telemetry import story
from telemetry.page import shared_page_state
from telemetry.page import legacy_page_test

import profiler as pro
import bench_settings

VMSRate = '1'
PARate = '1'

_SPEEDOMETER_DIR = os.path.join(path_util.GetChromiumSrcDir(),
    'third_party', 'WebKit', 'PerformanceTests', 'Speedometer')

class speedometerIntelV1Measurement(legacy_page_test.LegacyPageTest):
    def ValidateAndMeasurePage(self, page, tab, results):
        for arg in sys.argv:
            if 'remote' in arg:
                pro.VMSCommand[3] = 'root@' + arg.split('=')[1]

        pro.VMSCommand[5] = VMSRate
        pro.PACommand[2] = PARate
        vms = pro.profiler(pro.VMSCommand)
        pa = pro.profiler(pro.PACommand)
        pa.start('speedometerIntelV1.ex')
        vms.start('speedometerIntelV1.vms')

        start_js = "startTest();"
        tab.EvaluateJavaScript(start_js)
        tab.WaitForJavaScriptCondition("document.getElementById('result-number').innerHTML.length > 0",timeout=1500)

        js_get_results = """
var results = {};
results['score'] = document.getElementById('result-number').innerHTML;
JSON.stringify(results);
"""
        js_results_dict = json.loads(tab.EvaluateJavaScript(js_get_results))
        vms.stop()
        pa.stop()

        for key, value in js_results_dict.iteritems():
            print '{0}, {1},'.format(key, value)
        time.sleep(5)

class speedometerIntelV1(benchmark.Benchmark):
    """Speedometer benchmark V1"""
    test = speedometerIntelV1Measurement

    #speedometer 1.0
    def CreateSpeedometerV1StorySet(self, options):
        try:
            mbm = __main__.bm
        except NameError:
            mbm = bench_settings.bench_mapping()
        _URL = "http://user-awfy.sh.intel.com/awfy/ARCworkloads/Speedometer-Old-Version/Speedometer/Speedometer/Full.html"
        ps = story.StorySet(base_dir=os.path.dirname(__file__))
        ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name='speedometerIntelV1'))
        return ps

    def CreateSpeedometerStorySet(self, options):
        ps = story.StorySet(base_dir=_SPEEDOMETER_DIR,
                 serving_dirs=[_SPEEDOMETER_DIR])
        ps.AddStory(page_mod.Page(
                 'file://index.html', ps, ps.base_dir, name='Speedometer'))
        return ps

    def GetExpectations(self):
        class StoryExpectations(story.expectations.StoryExpectations):
            def SetExpectations(self):
                pass # Speedometer1.0 not disabled.
        return StoryExpectations()

    def CreateStorySet(self, options):
        ps = self.CreateSpeedometerV1StorySet(options)
        return ps
