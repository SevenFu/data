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

#class SunspiderIntelMeasurement(page_mod.page_test.PageTest):
class SunspiderIntelMeasurement(legacy_page_test.LegacyPageTest):
  def ValidateAndMeasurePage(self, page, tab, results):
    for arg in sys.argv:
        if 'remote' in arg:
            pro.VMSCommand[3] = 'root@' + arg.split('=')[1]

    pro.VMSCommand[5] = VMSRate
    pro.PACommand[2] = PARate
    vms = pro.profiler(pro.VMSCommand)
    pa = pro.profiler(pro.PACommand)
    pa.start('sunspiderV1Intel.ex')
    vms.start('sunspiderV1Intel.vms')

    #tab.WaitForJavaScriptExpression(
    tab.WaitForJavaScriptCondition(
        'window.location.pathname.indexOf("results.html") >= 0'+
        '&& typeof(output) != undefined', timeout=1200)

    vms.stop()
    pa.stop()

    js_get_results = """
var results = {};
function sunspiderParse(target)
{
    var res = target.replace(/\s+/g, '');
    res = res.replace(/^.*:/, '');
    return res.replace(/ms.*/, '');;
}
var raw = document.getElementById('console').innerHTML;
var rawSplit = raw.split("<br>")
results['total'] = sunspiderParse(rawSplit[4]);
results['3d'] = sunspiderParse(rawSplit[7]);
results['cube'] = sunspiderParse(rawSplit[8]);
results['morph'] = sunspiderParse(rawSplit[9]);
results['ray'] = sunspiderParse(rawSplit[10]);
results['access'] = sunspiderParse(rawSplit[12]);
results['btree'] = sunspiderParse(rawSplit[13]);
results['fann'] = sunspiderParse(rawSplit[14]);
results['nbody'] = sunspiderParse(rawSplit[15]);
results['nsieve'] = sunspiderParse(rawSplit[16]);
results['bitops'] = sunspiderParse(rawSplit[18]);
results['bit'] = sunspiderParse(rawSplit[19]);
results['bits'] = sunspiderParse(rawSplit[20]);
results['bitwise'] = sunspiderParse(rawSplit[21]);
results['nsievebits'] = sunspiderParse(rawSplit[22]);
results['control'] = sunspiderParse(rawSplit[24]);
results['recursive'] = sunspiderParse(rawSplit[25]);
results['crypto'] = sunspiderParse(rawSplit[27]);
results['aes'] = sunspiderParse(rawSplit[28]);
results['md5'] = sunspiderParse(rawSplit[29]);
results['sha1'] = sunspiderParse(rawSplit[30]);
results['date'] = sunspiderParse(rawSplit[32]);
results['tofte'] = sunspiderParse(rawSplit[33]);
results['xparb'] = sunspiderParse(rawSplit[34]);
results['math'] = sunspiderParse(rawSplit[36]);
results['cordic'] = sunspiderParse(rawSplit[37]);
results['partial'] = sunspiderParse(rawSplit[38]);
results['spectral'] = sunspiderParse(rawSplit[39]);
results['reg'] = sunspiderParse(rawSplit[41]);
results['dna'] = sunspiderParse(rawSplit[42]);
results['string'] = sunspiderParse(rawSplit[44]);
results['base64'] = sunspiderParse(rawSplit[45]);
results['fasta'] = sunspiderParse(rawSplit[46]);
results['tagcloud'] = sunspiderParse(rawSplit[47]);
results['unpack'] = sunspiderParse(rawSplit[48]);
results['validate'] = sunspiderParse(rawSplit[49]);
JSON.stringify(results);

"""
    js_results_dict = json.loads(tab.EvaluateJavaScript(js_get_results))
    print '{0}, {1},'.format('total', js_results_dict['total'])
    del js_results_dict['total']
    for key, value in js_results_dict.iteritems():
        print '{0}, {1},'.format(key, value)

class SunspiderV1Intel(benchmark.Benchmark):
  """Apple's SunSpider JavaScript benchmark."""
  test = SunspiderIntelMeasurement

  def CreateStorySet(self, options):
    try:
       mbm = __main__.bm
    except NameError:
       mbm = bench_settings.bench_mapping()
    _URL = mbm.get_bench_URL('sunspiderV1Intel')
    ps = story.StorySet(base_dir=os.path.dirname(__file__))
    ps.AddStory(page_mod.Page(_URL, ps, ps.base_dir, name='sunspiderV1Intel'))

    return ps

