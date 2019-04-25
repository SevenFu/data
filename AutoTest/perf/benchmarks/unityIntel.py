# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys

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

#class unityIntelMeasurement(page_mod.page_test.PageTest):
class unityIntelMeasurement(legacy_page_test.LegacyPageTest):
    def ValidateAndMeasurePage(self, page, tab, results):
        for arg in sys.argv:
            if 'remote' in arg:
                pro.VMSCommand[3] = 'root@' + arg.split('=')[1]

        pro.VMSCommand[5] = VMSRate
        pro.PACommand[2] = PARate
        vms = pro.profiler(pro.VMSCommand)
        pa = pro.profiler(pro.PACommand)
        pa.start('unity2015Intel.ex')
        vms.start('unity2015Intel.vms')
        loop_num = 4

        for num in range(0, loop_num):
            #tab.WaitForJavaScriptExpression('document.readyState == "complete"', 180)
            tab.WaitForJavaScriptCondition('document.readyState == "complete"', timeout=180)
            tab.ExecuteJavaScript('var a=""; console.log = function(text){a+=text+"||"}')
            #tab.WaitForJavaScriptExpression('a.indexOf("Mandelbrot Script:")!=-1',1000)
            tab.WaitForJavaScriptCondition('a.indexOf("Mandelbrot Script:")!=-1',timeout=1000)

            js_get_results = """
var results = {};
var b = a.substring(a.indexOf('Mandelbrot Script:'));
b = b.split('||');
for (var i = 0; i < b.length-1; i++) {
    var result_name;
    var result_value;
    result_name = b[i].split(":")[0];
    result_value = b[i].split(":")[1].trim();
    results[result_name] = {value: result_value};
}

JSON.stringify(results);
"""
            js_results = eval(tab.EvaluateJavaScript(js_get_results))
            for key in js_results:
                results.AddValue(scalar.ScalarValue(
                    results.current_page,
                    key,
                    '',
                    int(int(js_results[key]['value'])),
                    important=True if key == 'Overall' else False))
            # Print score for Intel infrastructure
            print 'score%d, %s,' % (num, js_results['Overall']['value'])
            # reload the page
            if num < loop_num - 1:
                #tab.ExecuteJavaScript('window.location.reload()')
                restart_js = """
var restart = function() {
    var canvas = document.getElementById("canvas");
    var canvas_width = canvas.width;
    var canvas_height = canvas.height;
    var restart_button_offset_x = canvas_width/2 - 50;
    var restart_button_offset_y = canvas_height/2 + 220;
    var rect = canvas.getBoundingClientRect();
    var restart_button_position_x = rect.left + restart_button_offset_x;
    var restart_button_position_y = rect.top + restart_button_offset_y;

    var event = {
        bubbles: true,
        cancelable: true,
        clientX: restart_button_position_x,
        clientY: restart_button_position_y,
    };
    canvas.dispatchEvent(new MouseEvent("mousemove", event));
    canvas.dispatchEvent(new MouseEvent("mousedown", event));
    canvas.dispatchEvent(new MouseEvent("mouseup", event));
}

restart();
"""
                tab.ExecuteJavaScript(restart_js)

        vms.stop()
        pa.stop()

class UnityPage(page_mod.Page):
    def __init__(self, url, page_set, name=''):
        super(UnityPage, self).__init__(
                                    url=url, page_set=page_set, name=name,
                                    shared_page_state_class=shared_page_state.SharedDesktopPageState
                                    )
        self.archive_data_file='data/unity.json'

    def RunNavigateSteps(self, action_runner):
      action_runner.Navigate(self.url)
      action_runner.WaitForJavaScriptCondition("document.readyState == 'complete'")
      action_runner.Wait(5)

class unity2015Intel(benchmark.Benchmark):
    """Unity3d benchmark - webgl """
    test = unityIntelMeasurement

    def CreateStorySet(self, options):
        try:
            mbm = __main__.bm
        except NameError:
            mbm = bench_settings.bench_mapping()
        # _URL = mbm.get_bench_URL('unityIntel')
        _URL = "http://user-awfy.sh.intel.com/awfy/ARCworkloads/unity3d-release/"
        ps = story.StorySet(base_dir=os.path.dirname(__file__))
        ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name='unityIntel'))
        return ps
