#!/usr/bin/env python

# Copyright (c) 2017 Intel corp. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
The set of hitogram-json tags
containing all histogram-json tags and maintain values and id

"""

import codecs
import json
import csv
import os.path
from HTMLParser import HTMLParser

#page_cycler_v2.typical_25
PAGE_CYCLER_NAME  = "page_cycler_v2"
HISTOGRAM_TAG     = "histogram-json"
TIMETOONLOAD_JSON = "timeToOnload"
PCV1_WARM         = "cache_temperature:warm"
KEY_0_WARM        = 'values'
DISPLAY_NAME      = 'storyDisplayName'
REF_ID_0_KEY      = 'diagnostics'
REF_ID_1_KEY      = 'storyTags'
SCORE_LINE        = "['metric, score,']"

#smoothness
SMOOTHNESS_NAME   = "smoothness"
PERCENTAGE_SMOOTH = "percentage_smooth"
SMOOTH_DISPLAYNAME= "storyDisplayName"
SMOOTH_STORYS     = "stories"

#tab_switching
TAB_SWITCHING_NAME = "tab_switching.typical_25"
TAB_SWITCH_RESULT  = "tab_switching_latency"

#webrtcIntel
WEBRTC_NAME        = "webrtcIntel"
WEBRTC_RESULTS     = ['peer_connection_0_video_goog_frame_rate_sent',
                      'peer_connection_0_bwe_goog_transmit_bitrate',
                      'peer_connection_1_video_goog_frame_rate_received',
                      'peer_connection_1_bwe_goog_transmit_bitrate']

class HistogramJsonTagParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.isHist = False
        self.list   = []

    def handle_starttag(self, tag, attrs):
        if tag == HISTOGRAM_TAG:
            self.isHist = True
        else:
            self.isHist = False

    def handle_data(self, data):
        if self.isHist and not data.isspace():
            self.list.append(data)

class Histogram():
    def __init__(self, gid):
        self.id = gid

class KeyHistogram(Histogram):
    def __init__(self, gid, name, benchmark_name):
        Histogram.__init__(self, gid)
        self.name  = name
        self.benchmark_name = benchmark_name
        self.value_obj = None
        self.value_float = None
        self.is_reduplicated = False

    def assign_value(self, value_maps):
        if self.id in value_maps and 0 < len(value_maps[self.id]):
            self.value_obj = value_maps[self.id][0]
            if self.name is None:
                self.name = value_maps[self.id][0].url_str

    def to_str(self):
        if self.value_obj is None:
            return "Item: %s\nID: %s\nValue: %s\n" % (self.name, self.id, "None")
        return "Item: %s\nID: %s\nValue: %s\n" % (self.name, self.id, self.value_obj.value)

    def get_digital_value(self):
        if self.value_float is None:
            self.value_float = float(0.0)
            if self.value_obj is not None and self.value_obj.value is not None:
                value_str = str(self.value_obj.value)
                if len(value_str) > 2:
                    data_str = value_str[1:-1]
                    if "," in value_str:
                        data_list = data_str.split(",")
                        if self.benchmark_name == PAGE_CYCLER_NAME:
                            max = 0.0
                            for data_s in data_list:
                                if float(data_s) - max > 0.0001:
                                    max = float(data_s)
                            self.value_float = max
                        else:
                            sum = 0.0
                            for data_s in data_list:
                                sum += float(data_s)
                            self.value_float = sum / len(data_list)
                    else:
                        self.value_float = float(data_str)
        return self.value_float

    #Name,pcv1-warm,value,
    def to_csv_line(self):
        return "%s, %s, %f, \n" % (self.name, PCV1_WARM, self.get_digital_value())

    def is_same_url(self, other):
        return (not self.id == other.id) and self.name == other.name

    def merge_value(self, other):
        self.value_obj.merge_value(other.value_obj)
        other.is_reduplicated = True

class ValueHistogram(Histogram):
    def __init__(self, gid, name, value, ref_id, url_str=None):
        Histogram.__init__(self, gid)
        self.name  = name
        self.value = value
        self.ref_id= ref_id
        self.url_str = url_str

    def to_str(self):
        return "name: %s\nvalue: %s" % (self.name, self.value)

    def get_all_data(self):
        if self.value is None or len(str(self.value)) <= 2:
            return ","
        else:
            return str(self.value)[1:-1]

    def merge_value(self, other):
        if other is None:
            return
        if self.value is None or len(str(self.value)) <= 2:
            self.value = other.value
        elif other.value is not None and len(str(other.value)) > 2:
            value_str = "[%s, %s]" % (str(self.value)[1:-1], str(other.value)[1:-1])
            self.value = value_str

class SmoothnessKeyHistogram(KeyHistogram):
    #Name,PERCENTAGE_SMOOTH,value,
    def to_csv_line(self):
        return "%s, %s, %f, \n" % (self.name, PERCENTAGE_SMOOTH, self.get_digital_value())

class TabSwitchHistogram(KeyHistogram):
    #Name, TAB_SWITCH_RESULT, value1, value2,..., value25
    def to_csv_line(self):
        return "%s, %s, %s, \n" % (self.name, TAB_SWITCH_RESULT, self.value_obj.get_all_data())

class WebRTCHistogram(KeyHistogram):
    #Name, Result_Name, value1, value2,..., value25
    def to_csv_line(self):
        return "%s, %s, \n" % (self.name, self.value_obj.get_all_data())

def parseHtml(str):
    parser = HistogramJsonTagParser()
    parser.feed(str)
    return parser.list

def parseJson(benchmark, str):
    hist_json = json.loads(str)
    hist_obj  = None
    if 'name' in hist_json and hist_json['name'] == TIMETOONLOAD_JSON:
        value_str = None
        ref_id    = None
        url_str   = None
        if 'sampleValues' in hist_json:
            value_str = hist_json['sampleValues']
        if REF_ID_0_KEY in hist_json:
            ref_id = hist_json[REF_ID_0_KEY][REF_ID_1_KEY]
            if 'allBins' in hist_json:
                url_all_bins = hist_json['allBins']
                for key in url_all_bins.keys():
                     value = url_all_bins[key]
                     url_str= value[1][0]['url']['values'][0]
        hist_obj = ValueHistogram(hist_json['guid'], hist_json['name'], value_str, ref_id, url_str)
    elif KEY_0_WARM in hist_json and hist_json[KEY_0_WARM][0] == PCV1_WARM :
        hist_obj = KeyHistogram(hist_json['guid'], None, PAGE_CYCLER_NAME)
    elif 'name' in hist_json and hist_json['name'] == PERCENTAGE_SMOOTH:
        value_str = None
        if 'sampleValues' in hist_json:
            value_str = hist_json['sampleValues']
        if REF_ID_0_KEY in hist_json:
            hist_obj = SmoothnessKeyHistogram(hist_json['guid'],
                hist_json[REF_ID_0_KEY][SMOOTH_STORYS][0], SMOOTHNESS_NAME)
            value_obj = ValueHistogram(hist_json['guid'], hist_json['name'], value_str, None)
            hist_obj.value_obj = value_obj
    if TAB_SWITCHING_NAME == benchmark:
        if 'name' in hist_json and TAB_SWITCH_RESULT in hist_json['name']:
            value_str = None
            if 'sampleValues' in hist_json:
                value_str = hist_json['sampleValues']
                value_obj = ValueHistogram(hist_json['guid'], hist_json['name'], value_str, None)
                hist_obj  = TabSwitchHistogram(hist_json['guid'], benchmark, TAB_SWITCHING_NAME)
                hist_obj.value_obj = value_obj
    if WEBRTC_NAME == benchmark:
        if 'name' in hist_json and hist_json['name'] in WEBRTC_RESULTS:
            value_str = None
            if 'sampleValues' in hist_json:
                value_str = hist_json['sampleValues']
                value_obj = ValueHistogram(hist_json['guid'], hist_json['name'], value_str, None)
                hist_obj  = WebRTCHistogram(hist_json['guid'], hist_json['name'], benchmark)
                hist_obj.value_obj = value_obj
    return hist_obj

def mergeSameUrl(items):
    merged = []
    for item in items:
        if not item.is_reduplicated:
            for other in items:
                if item.is_same_url(other):
                    item.merge_value(other)
            merged.append(item)
    return merged

def getPcv1Warm(items, values):
    for item in items:
        item.assign_value(values)

def parse_result_file(benchmark, file_name):
    f=codecs.open(file_name, 'r')
    html_str = f.read()
    html_str = html_str.replace("&", "_")
    hist_jsons = parseHtml(html_str)
    histogram_values = {}
    histogram_items  = []
    if PAGE_CYCLER_NAME in benchmark:
        for hist_json in hist_jsons:
            histogram_obj = parseJson(benchmark, hist_json)
            if histogram_obj is not None:
                if isinstance(histogram_obj, ValueHistogram):
                    if not histogram_obj.ref_id in histogram_values:
                        histogram_values[histogram_obj.ref_id] = []
                    histogram_values[histogram_obj.ref_id].append(histogram_obj)
                else:
                    histogram_items.append(histogram_obj)
        getPcv1Warm(histogram_items, histogram_values)
        histogram_items = mergeSameUrl(histogram_items)
    elif SMOOTHNESS_NAME in benchmark \
          or TAB_SWITCHING_NAME == benchmark \
          or WEBRTC_NAME == benchmark:
        for hist_json in hist_jsons:
            histogram_obj = parseJson(benchmark, hist_json)
            if histogram_obj is not None:
                histogram_items.append(histogram_obj)
    return histogram_items

def savetocsv(filename, items):
    with open(filename, 'w+') as file:
        for item in items:
            file.write(item.to_csv_line())
        file.close()

def getAverage(items, indicator_name=None):
    sum = 0.0
    average = 0.0
    num_items = 0
    for item in items:
        if indicator_name == None:
            sum = sum + item.get_digital_value()
            if (item.get_digital_value() > 0):
                num_items = num_items + 1
        else:
            if item.name == indicator_name:
               sum = sum + item.get_digital_value()
               if (item.get_digital_value() > 0):
                   num_items = num_items + 1
    if num_items > 0:
        average = sum / num_items
    return average

def updatetext(index, filename, items, benchmark):
    if os.path.isfile(filename):
        with open(filename, 'r+') as file:
            lines = file.readlines()
            file.seek(0)
            file.truncate()
            line_num = 0
            for line in lines:
                if SCORE_LINE in line:
                    if line_num == index:
                        if PAGE_CYCLER_NAME in benchmark:
                            line = "[['metric, score,'], ['timeToOnload, %f,']]\n" % getAverage(items)
                        elif SMOOTHNESS_NAME in benchmark:
                            line = "[['metric, score,'], ['%s, %f,']]\n" % (PERCENTAGE_SMOOTH, getAverage(items))
                        elif TAB_SWITCHING_NAME == benchmark:
                            line = "[['metric, score,'], ['%s, %f,']]\n" % (TAB_SWITCH_RESULT, getAverage(items))
                        elif WEBRTC_NAME == benchmark:
                            scores_str = ""
                            for result in WEBRTC_RESULTS:
                                scores_str = scores_str + "['%s, %f,'], " % (result, getAverage(items, result))
                            line = "[['metric, score,'], %s]\n" % scores_str[:-2]
                    line_num += 1
                file.write(line)


if __name__== "__main__":
    items = parse_result_file("webrtcIntel", "webrtcIntel_reef_0_results.html")
    savetocsv("./sample_results.csv", items)
    updatetext(0, "webrtcIntel.txt", items, "webrtcIntel")
