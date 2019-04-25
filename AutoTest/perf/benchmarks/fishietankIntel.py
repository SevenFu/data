# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys
import re
from telemetry import benchmark
from telemetry.core import util
from telemetry import page as page_mod
from telemetry import story
from telemetry.page import legacy_page_test

import profiler as pro
import bench_settings

VMSRate = '1'
PARate = '1'

#class FishIETankIntelMeasurement(page_mod.page_test.PageTest):
class FishIETankIntelMeasurement(legacy_page_test.LegacyPageTest):
  def ValidateAndMeasurePage(self, page, tab, results):
    for arg in sys.argv:
        if 'remote' in arg:
           pro.VMSCommand[3] = 'root@' + arg.split('=')[1]

    pro.VMSCommand[5] = VMSRate
    pro.PACommand[2] = PARate
    vms = pro.profiler(pro.VMSCommand)
    pa = pro.profiler(pro.PACommand)
    pa.start('fishietankIntel.ex')
    vms.start('fishietankIntel.vms')

    #tab.WaitForJavaScriptExpression(
    #    "document.getElementById('avg_fps_lable').innerHTML != ''", 1200)
    tab.WaitForJavaScriptCondition(
         'document.getElementById("avg_fps_lable").innerHTML != ""', timeout=1200)

    vms.stop()
    pa.stop()
    js_get_results = """
var results = {}
results['FPS'] = document.getElementById('avg_fps_lable').innerHTML;
JSON.stringify(results);
"""
    result_dict = eval(tab.EvaluateJavaScript(js_get_results))
    value = result_dict['FPS']
    value = re.sub(r'^.*Result: ', '', value)
    value = re.sub(r'fps.*$', '', value)
    print "{0}, {1},".format('FPS', value)
    del result_dict['FPS']
    for key, value in result_dict.iteritems():
      print "{0}, {1},".format(key, value)

class FishIETankIntel(benchmark.Benchmark):
  test = FishIETankIntelMeasurement

  def CreateStorySet(self, options):
    try:
       mbm = __main__.bm
    except NameError:
       mbm = bench_settings.bench_mapping()
    _URL = mbm.get_bench_URL('fishietankIntel')
    ps = story.StorySet(base_dir=os.path.dirname(__file__))
    _URL = _URL + '?fish=250'
    ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name='fishietankIntel'))
    return ps

