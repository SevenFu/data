# Copyright (c) 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import collections
import json
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

#class RobohornetIntelMeasurement(page_mod.page_test.PageTest):
class RobohornetIntelMeasurement(legacy_page_test.LegacyPageTest):
  def ValidateAndMeasurePage(self, page, tab, results):
    js_is_done = ("document.getElementById('runButton').innerHTML "
                  "!= 'Running...'")
    for arg in sys.argv:
        if 'remote' in arg:
            pro.VMSCommand[3] = 'root@' + arg.split('=')[1]

    pro.VMSCommand[5] = VMSRate
    pro.PACommand[2] = PARate
    vms = pro.profiler(pro.VMSCommand)
    pa = pro.profiler(pro.PACommand)
    pa.start('robohornetIntel.ex')
    vms.start('robohornetIntel.vms')

    tab.EvaluateJavaScript("document.getElementById('runButton').click()")
    #tab.WaitForJavaScriptExpression(
    tab.WaitForJavaScriptCondition(
        "document.getElementById('runButton').innerHTML != 'Running...'", timeout=1200)

    vms.stop()
    pa.stop()

    js_get_results = """
var result = {};
result['score'] = document.getElementById('index').innerHTML;
var table = document.getElementById('tests').rows;
for(var i = 1; i < table.length - 2 ; i = i + 2)
{
    result[table[i].cells[0].getElementsByTagName('span')[0].innerHTML] =
        table[i].cells[5].innerHTML;
}
JSON.stringify(result);
"""
### table.length - 2 to strip out trailing details/summary from table
    js_results_dict = json.loads(tab.EvaluateJavaScript(js_get_results))
    print '{0}, {1},'.format('score', js_results_dict['score'])
    del js_results_dict['score']
    for key, value in js_results_dict.iteritems():
        print '{0}, {1},'.format(key, value)

class RobohornetIntel(benchmark.Benchmark):
  test = RobohornetIntelMeasurement

  def CreateStorySet(self, options):
    try:
       mbm = __main__.bm
    except NameError:
       mbm = bench_settings.bench_mapping()
    _URL = mbm.get_bench_URL('robohornetIntel')
    ps = story.StorySet(base_dir=os.path.dirname(__file__))
    ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name='robohornetIntel'))
    return ps
