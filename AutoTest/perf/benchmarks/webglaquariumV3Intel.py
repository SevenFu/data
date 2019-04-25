# Copyright (c) 2012 The Chromium Authors. All rights reserved.
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

#class WebGLAquariumIntelV3Measurement(page_mod.page_test.PageTest):
class WebGLAquariumIntelV3Measurement(legacy_page_test.LegacyPageTest):
  def ValidateAndMeasurePage(self, page, tab, results):
    for arg in sys.argv:
        if 'remote' in arg:
          pro.VMSCommand[3] = 'root@' + arg.split('=')[1]

    pro.VMSCommand[5] = VMSRate
    pro.PACommand[2] = PARate
    vms = pro.profiler(pro.VMSCommand)
    pa = pro.profiler(pro.PACommand)
    pa.start('webglaquariumV3Intel.ex')
    vms.start('webglaquariumV3Intel.vms')

    #tab.WaitForJavaScriptExpression(
    tab.WaitForJavaScriptCondition(
      'document.getElementById("benchMessage").innerHTML == "Benchmark Finished"',
      timeout=1200)

    vms.stop()
    pa.stop()

    js_get_fps = """
var result = {};
result['fps'] = document.getElementById('avgFps').innerHTML;
JSON.stringify(result);
"""

    result_dict = eval(tab.EvaluateJavaScript(js_get_fps))
    avg = int(result_dict['fps'])

    print "{0}, {1},".format('FPS', avg)

class WebGLAquariumV3Intel(benchmark.Benchmark):
  test = WebGLAquariumIntelV3Measurement

  def CreateStorySet(self, options):
    try:
       mbm = __main__.bm
    except NameError:
       mbm = bench_settings.bench_mapping()
    _URL = mbm.get_bench_URL('webglaquariumV3Intel')
    _URL = _URL + '?numFish=1000&startWait=300&runFor=1200'
    ps = story.StorySet(base_dir=os.path.dirname(__file__))
    ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name='webglaquariumV3Intel'))
    return ps
