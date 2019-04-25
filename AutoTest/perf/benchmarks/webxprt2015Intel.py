# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys

from telemetry import benchmark
from telemetry import page as page_mod
from telemetry.value import scalar
from telemetry import story
from telemetry.page import legacy_page_test

import profiler as pro
import bench_settings

VMSRate = '1'
PARate = '1'
DESCRIPTIONS = {
    'photo_enhancement':
        'Apply three effects to two photos each using Canvas',
    'organize_album':
        'Detect faces in a set of five photos using Canvas',
    'stock_option_pricing':
        'Calculate and display graphic views of a stock portfolio using '
        'Canvas and SVG',
    'local_notes':
        'Encrypt, store, and display notes from local storage using AES '
        'encryption and ASM.js',
    'sales_graphs':
        'Calculate and display multiple views of sales',
    'explore_dna_sequencing':
        'Use Web Workers to filter 8 DNA sequences for ORFs and amino acids',
    'overall_score':
        'Combined score',
}


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
        pa.start('webxprt2015Intel.ex')
        vms.start('webxprt2015Intel.vms')

        tab.EvaluateJavaScript("onClickstart()")
        tab.WaitForJavaScriptCondition('window.location.pathname.indexOf("results.php") >= 0', 
             timeout=1200)
        #tab.WaitForJavaScriptExpression('window.location.pathname.indexOf("results.php") >= 0', 1200)

        vms.stop()
        pa.stop()

        js_get_results = """
var results = {};

// Main score
var overall_score = document.getElementsByClassName("scoreText")[0].innerHTML
results['overall_score'] = {value: overall_score,
                            units: 'score'};

// Subtest results
var result_divs = document.querySelectorAll('.resultsworkload-text');
for (var i = 0; i < result_divs.length; i++) {
    var result_name;
    var result_units;
    var result_value;
    // Ex: Photo Enhancement (ms) :
    var result_name_div = $(result_divs[i]).children(".resultsworkload-name").text();
    // Ex: 248 +/- 7.69%
    var result_duration_div = $(result_divs[i]).children(".resultsworkload-duration").text();

    // Convert 'Photo Enhancement (ms) :' to 'photo_enhancement'
    result_name = result_name_div.split('(')[0];
    result_name = result_name.trim();
    result_name = result_name.replace(/ /g,"_").toLowerCase();

    result_units = result_name_div.split(')')[0];
    result_units = result_units.split('(')[1];

    result_value = result_duration_div.split('+')[0];
    result_value = result_value.trim();

    results[result_name] = {value: result_value, units: result_units};
}

JSON.stringify(results);
"""
        js_results = eval(tab.EvaluateJavaScript(js_get_results))
        for key in js_results:
            results.AddValue(scalar.ScalarValue(
                results.current_page,
                key,
                js_results[key]['units'],
                int(js_results[key]['value']),
                important=True if key == 'overall_score' else False,
                description=DESCRIPTIONS.get(key)))

        # Print score for Intel infrastructure
        print "the score to write down is:"
        # print('score, %s,' % (js_results['overall_score']['value']))
        print (js_results['overall_score']['value'])
        print (js_results['photo_enhancement']['value'])
        print (js_results['organize_album']['value'])
        print (js_results['stock_option_pricing']['value'])
        print (js_results['local_notes']['value'])
        print (js_results['sales_graphs']['value'])
        print (js_results['explore_dna_sequencing']['value'])
        print "*"*10
        # for v, k in js_results.items():
        #     print('{v}:{k}'.format(v=v, k=k))

class webxprt2015Intel(benchmark.Benchmark):
    """Principle Technology's WebXPRT v1.995 benchmark."""
    test = webxprtIntelMeasurement

    def CreateStorySet(self, options):
        try:
            mbm = __main__.bm
        except NameError:
            mbm = bench_settings.bench_mapping()
            _URL = mbm.get_bench_URL('webxprt2015Intel')
        ps = story.StorySet(base_dir=os.path.dirname(__file__))
        ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name='webxprt2015Intel'))
        return ps
