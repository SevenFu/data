# Copyright (c) 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import collections
import json
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


#class AngryBirdsIntelMeasurement(page_mod.page_test.PageTest):
class AngryBirdsIntelMeasurement(legacy_page_test.LegacyPageTest):
  def ValidateAndMeasurePage(self, page, tab, results):
    js_start_workload = ("document.getElementById('runButton').click()")
    js_is_done = ("document.getElementById('alertDiv').innerHTML "
                  "== 'Please reload page if run more test'")
    for arg in sys.argv:
        if 'remote' in arg:
            pro.VMSCommand[3] = 'root@' + arg.split('=')[1]

    pro.VMSCommand[5] = VMSRate
    pro.PACommand[2] = PARate
    vms = pro.profiler(pro.VMSCommand)
    pa = pro.profiler(pro.PACommand)
    pa.start('angrybirdsIntel.ex')
    vms.start('angrybirdsIntel.vms')

    tab.EvaluateJavaScript(js_start_workload)
    tab.WaitForJavaScriptCondition(js_is_done, timeout=1200)
    #tab.WaitForJavaScriptExpression(js_is_done, 1200)
    vms.stop()
    pa.stop()

    js_get_results = """
result = {};
function abParse(target)
{
    var res = target.replace(/\s+/g, '');
    return res.replace(/^.*-/, '');
}
result['ejectFPS'] = abParse(document.getElementById('ejectFPSResult').innerText);
JSON.stringify(result);
"""
    js_results_dict = json.loads(tab.EvaluateJavaScript(js_get_results))
    print '{0}, {1},'.format('ejectFPS', js_results_dict['ejectFPS'])
    del js_results_dict['ejectFPS']
    for key, value in js_results_dict.iteritems():
        print '{0}, {1},'.format(key, value)

class AngryBirdsIntel(benchmark.Benchmark):
  test = AngryBirdsIntelMeasurement

  def CreateStorySet(self, options):
    try:
       mbm = __main__.bm
    except NameError:
       mbm = bench_settings.bench_mapping()
    _URL = mbm.get_bench_URL('angrybirdsIntel')
    ps = story.StorySet(base_dir=os.path.dirname(__file__))
    ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name='angrybirdsIntel'))
    return ps

