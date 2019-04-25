# Copyright (c) 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys
import time
from benchmarks import profiler as pro
from metrics import cpu
from metrics import media
from metrics import system_memory
from telemetry.page import legacy_page_test

#class LocalVideoIntel(page_test.PageTest):
class LocalVideoIntel(legacy_page_test.LegacyPageTest):
  """ Heavily based on measurements/media.py """
  def __init__(self):
    super(LocalVideoIntel, self).__init__('RunMediaMetrics')
    self._media_metric = None
    self._cpu_metric = None
    self._memory_metric = None
    # Intel specific collections
    self._VMSRate = '1'
    self._PARate = '1'
    self._pa = None
    self._vms = None
    # Save the interface for pushing files to the DUT
    self.cri = None
    # Snapshot start and stop times for calculating FPS from decoded frames
    self.startTime = None
    self.stopTime = None

  def WillStartBrowser(self, browser):
    # Setup Intel metrics
    for arg in sys.argv:
        if 'remote' in arg:
            pro.VMSCommand[3] = 'root@' + arg.split('=')[1]
    pro.VMSCommand[5] = self._VMSRate
    pro.PACommand[2] = self._PARate
    self._vms = pro.profiler(pro.VMSCommand)
    self._pa = pro.profiler(pro.PACommand)

    # Rip the CrOSInterface out of the browser class
    self.cri = browser._platform_backend._cri

  def CustomizeBrowserOptions(self, options):
    # Needed to run media actions in JS on touch-based devices as on Android.
    options.AppendExtraBrowserArgs(
        '--disable-gesture-requirement-for-media-playback')

  def WillNavigateToPage(self, page, tab):
    # Now that we have access to the page, push the video
    self._pushVideo(page)

  def DidNavigateToPage(self, page, tab):
    """Override to do operations right after the page is navigated."""
    tab.Navigate("file://" + page.remoteFilePath)
    self._media_metric = media.MediaMetric(tab)
    self._media_metric.Start(page, tab)
    self.startTime = time.time()
    self._cpu_metric = cpu.CpuMetric(tab.browser)
    self._cpu_metric.Start(page, tab)
    self._memory_metric = system_memory.SystemMemoryMetric(tab.browser)
    self._memory_metric.Start(page, tab)
    self._pa.start(page.paVmsName + '.ex')
    self._vms.start(page.paVmsName + '.vms')

  def ValidateAndMeasurePage(self, page, tab, results):
    """Measure the page's performance."""
    self._media_metric.Stop(page, tab)
    self.stopTime = time.time()
    trace_name = self._media_metric.AddResults(tab, results)
    self._cpu_metric.Stop(page, tab)
    self._memory_metric.Stop(page, tab)
    self._cpu_metric.AddResults(tab, results, trace_name=trace_name)
    exclude_metrics = ['WorkingSetSizePeak', 'SystemCommitCharge', 'VMPeak',
                       'VM']
    self._memory_metric.AddResults(tab, results,
                                   trace_name=trace_name,
                                   exclude_metrics=exclude_metrics)
    self._vms.stop()
    self._pa.stop()
    self._printIntelCSVMetrics(page, results)

  def _printIntelCSVMetrics(self, page, results):
    """ Print CSV results for pnp parsing """
    # FPS
    name = 'decoded_frame_count.media_0'
    for value in results.FindPageSpecificValuesForPage(page, name):
      fps = value.GetRepresentativeNumber() / (self.stopTime - self.startTime)
      print ('FPS, {}'.format(round(fps, 0)))

    # Dropped frames
    name = 'dropped_frame_count.media_0'
    for value in results.FindPageSpecificValuesForPage(page, name):
      print (name + ", " + value.GetRepresentativeString())

  def _pushVideo(self, page):
    """ Push files to the DUT for local video playback """
    if not self.cri.FileExistsOnDevice(page.remoteFilePath):
      self.cri.PushFile(page.localFilePath, page.remoteFilePath)
