# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import logging
import re

import page_sets
from core import perf_benchmark
from metrics import cpu
from metrics import power
from py_utils import camel_case
from telemetry import benchmark
from telemetry.page import legacy_page_test
from telemetry.timeline import chrome_trace_category_filter
from telemetry.web_perf import timeline_based_measurement
from telemetry.value import list_of_scalar_values


INTERESTING_METRICS = {
    'packetsReceived': {
        'units': 'packets',
        'description': 'Packets received by the peer connection',
    },
    'packetsSent': {
        'units': 'packets',
        'description': 'Packets sent by the peer connection',
    },
    'googDecodeMs': {
        'units': 'ms',
        'description': 'Time spent decoding.',
    },
    'googMaxDecodeMs': {
        'units': 'ms',
        'description': 'Maximum time spent decoding one frame.',
    },
    'googRtt': {
        'units': 'ms',
        'description': 'Measured round-trip time.',
    },
    'googJitterReceived': {
        'units': 'ms',
        'description': 'Receive-side jitter in milliseconds.',
    },
    'googCaptureJitterMs': {
        'units': 'ms',
        'description': 'Capture device (audio/video) jitter.',
    },
    'googTargetDelayMs': {
        'units': 'ms',
        'description': 'The delay we are targeting.',
    },
    'googExpandRate': {
        'units': '%',
        'description': 'How much we have NetEQ-expanded the audio (0-100%)',
    },
    'googFrameRateReceived': {
        'units': 'fps',
        'description': 'Receive-side frames per second (video)',
    },
    'googFrameRateSent': {
        'units': 'fps',
        'description': 'Send-side frames per second (video)',
    },
    'googAvailableSendBandwidth': {
        'units': 'bit/s',
        'description': 'How much send bandwidth we estimate we have.'
    },
    'googAvailableReceiveBandwidth': {
        'units': 'bit/s',
        'description': 'How much receive bandwidth we estimate we have.'
    },
    'googTargetEncBitrate': {
        'units': 'bit/s',
        'description': ('The target encoding bitrate we estimate is good to '
                        'aim for given our bandwidth estimates.')
    },
    'googTransmitBitrate': {
        'units': 'bit/s',
        'description': 'The actual transmit bitrate.'
    },
}


def GetReportKind(report):
  if 'audioInputLevel' in report or 'audioOutputLevel' in report:
    return 'audio'
  if 'googFrameRateSent' in report or 'googFrameRateReceived' in report:
    return 'video'
  if 'googAvailableSendBandwidth' in report:
    return 'bwe'

  logging.debug('Did not recognize report batch: %s.', report.keys())

  # There are other kinds of reports, such as transport types, which we don't
  # care about here. For these cases just return 'unknown' which will ignore the
  # report.
  return 'unknown'


def DistinguishAudioVideoOrBwe(report, stat_name):
  return GetReportKind(report) + '_' + stat_name


def StripAudioVideoBweDistinction(stat_name):
  return re.sub('^(audio|video|bwe)_', '', stat_name)


def SortStatsIntoTimeSeries(report_batches):
  time_series = {}
  for report_batch in report_batches:
    for report in report_batch:
      for stat_name, value in report.iteritems():
        if stat_name not in INTERESTING_METRICS:
          continue
        if GetReportKind(report) == 'unknown':
          continue
        full_stat_name = DistinguishAudioVideoOrBwe(report, stat_name)
        time_series.setdefault(full_stat_name, []).append(float(value))

  return time_series


class WebrtcIntelMeasurement(legacy_page_test.LegacyPageTest):
  """Gathers WebRTC-related metrics on a page set."""

  def __init__(self):
    super(WebrtcIntelMeasurement, self).__init__()
    self._all_reports = None

    self._cpu_metric = None
    self._power_metric = None

  def WillStartBrowser(self, platform):
    self._power_metric = power.PowerMetric(platform)

  def DidStartBrowser(self, browser):
    pass
    self._cpu_metric = cpu.CpuMetric(browser)

  def DidNavigateToPage(self, page, tab):
    self._cpu_metric.Start(page, tab)
    self._power_metric.Start(page, tab)

  def CustomizeBrowserOptions(self, options):
    power.PowerMetric.CustomizeBrowserOptions(options)

  def ValidateAndMeasurePage(self, page, tab, results):
    """Measure the page's performance."""
    self._cpu_metric.Stop(page, tab)
    self._cpu_metric.AddResults(tab, results)

    self._power_metric.Stop(page, tab)
    self._power_metric.AddResults(tab, results)

    # Digs out stats from data populated by the javascript in webrtc_cases.
    self._all_reports = tab.EvaluateJavaScript(
        'JSON.stringify(window.peerConnectionReports)')

    if not self._all_reports:
      return

    reports = json.loads(self._all_reports)
    for i, report in enumerate(reports):
      time_series = SortStatsIntoTimeSeries(report)

      for stat_name, values in time_series.iteritems():
        stat_name_underscored = camel_case.ToUnderscore(stat_name)
        trace_name = 'peer_connection_%d_%s' % (i, stat_name_underscored)
        general_name = StripAudioVideoBweDistinction(stat_name)
        results.AddValue(list_of_scalar_values.ListOfScalarValues(
            results.current_page, trace_name,
            INTERESTING_METRICS[general_name]['units'], values,
            description=INTERESTING_METRICS[general_name]['description'],
            important=False))

  def DidRunPage(self, platform):
    self._power_metric.Close()


@benchmark.Owner(emails=['chunbo.hua@intel.com'])
class WebrtcIntelPerfBenchmark(perf_benchmark.PerfBenchmark):
  """Intel implementation for WebRTC metrics for real-time communications tests."""
  page_set = page_sets.WebrtcIntelPageSet
  test = WebrtcIntelMeasurement

  @classmethod
  def Name(cls):
    return 'webrtcIntel'

  def SetExtraBrowserOptions(self, options):
    options.AppendExtraBrowserArgs('--use-fake-device-for-media-stream=fps=30')
    options.AppendExtraBrowserArgs('--use-fake-ui-for-media-stream')
