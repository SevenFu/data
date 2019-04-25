# Copyright (c) 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import json
import os
import sys
import time

from telemetry import benchmark
from telemetry import page as page_mod
from telemetry import story
from telemetry.page import legacy_page_test

import profiler as pro
import bench_settings

VMSRate = '1'
PARate = '1'


#class StreamingVP94K60IntelMeasurement(page_mod.page_test.PageTest):
class StreamingVP94K60IntelMeasurement(legacy_page_test.LegacyPageTest):
  def ValidateAndMeasurePage(self, page, tab, results):
    for arg in sys.argv:
      if 'remote' in arg:
        pro.VMSCommand[3] = 'root@' + arg.split('=')[1]

    pro.VMSCommand[5] = VMSRate
    pro.PACommand[2] = PARate
    vms = pro.profiler(pro.VMSCommand)
    pa = pro.profiler(pro.PACommand)
    pa.start('streamingVP94K60Intel.ex')
    vms.start('streamingVP94K60Intel.vms')

    time.sleep(120)
    js_get_results = """
var results = {};
results['FPS'] = document.getElementById('fps').innerHTML;
results['droppedFrameCount'] = document.getElementById('droppedFrameCount').innerHTML;
JSON.stringify(results);
"""
    js_results_dict = json.loads(tab.EvaluateJavaScript(js_get_results))
    vms.stop()
    pa.stop()

    for key, value in js_results_dict.iteritems():
      print '{0}, {1},'.format(key, value)


class StreamingVP94K60Intel(benchmark.Benchmark):
  test = StreamingVP94K60IntelMeasurement

  def CreateStorySet(self, options):
    try:
      mbm = __main__.bm
    except NameError:
      mbm = bench_settings.bench_mapping()
    _URL = mbm.get_bench_URL('streamingVP9Intel')
    _URL = _URL + '?id=lt1540'
    ps = story.StorySet(base_dir=os.path.dirname(__file__))
    ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name="VP9-4K-60FPS"))
    return ps
