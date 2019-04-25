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

#class EarthScreenIntelMeasurement(page_mod.page_test.PageTest):
class EarthScreenIntelMeasurement(legacy_page_test.LegacyPageTest):
  def ValidateAndMeasurePage(self, page, tab, results):
    for arg in sys.argv:
        if 'remote' in arg:
            pro.VMSCommand[3] = 'root@' + arg.split('=')[1]

    pro.VMSCommand[5] = VMSRate
    pro.PACommand[2] = PARate
    vms = pro.profiler(pro.VMSCommand)
    pa = pro.profiler(pro.PACommand)
    pa.start('earthscreenIntel.ex')
    vms.start('earthscreenIntel.vms')

    time.sleep(300)
    js_get_results = """
var results = {};
results['FPS'] = document.getElementById('FPS').innerHTML;
JSON.stringify(results);
"""
    js_results_dict = json.loads(tab.EvaluateJavaScript(js_get_results))
    vms.stop()
    pa.stop()

    print '{0}, {1},'.format('FPS', js_results_dict['FPS'].split(':')[1])
    del js_results_dict['FPS']
    for key, value in js_results_dict.iteritems():
        print '{0}, {1},'.format(key, value)

class EarthScreenIntel(benchmark.Benchmark):
  test = EarthScreenIntelMeasurement

  def CreateStorySet(self, options):
    try:
       mbm = __main__.bm
    except NameError:
       mbm = bench_settings.bench_mapping()
    _URL = mbm.get_bench_URL('earthscreenIntel')
    ps = story.StorySet(base_dir=os.path.dirname(__file__))
    ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name='earthscreenIntel'))
    return ps
