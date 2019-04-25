# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from telemetry import story
from telemetry.page import page as page_module


class WebrtcIntelPage(page_module.Page):

  def __init__(self, url, page_set, name, tags):
    assert url.startswith('file://webrtc_intel_cases/')
    super(WebrtcIntelPage, self).__init__(
        url=url, page_set=page_set, name=name, tags=tags)

class VideoCallIntel(WebrtcIntelPage):
  """Why: Sets up a local video-only WebRTC 720p call for 45 seconds."""

  def __init__(self, page_set, tags):
    super(VideoCallIntel, self).__init__(
        url='file://webrtc_intel_cases/constraints.html',
        name='720p_call_45s',
        page_set=page_set, tags=tags)

  def RunPageInteractions(self, action_runner):
    with action_runner.CreateInteraction('Action_Create_PeerConnection',
                                         repeatable=False):
      action_runner.ExecuteJavaScript('minWidthInput.value = 1280')
      action_runner.ExecuteJavaScript('maxWidthInput.value = 1280')
      action_runner.ExecuteJavaScript('minHeightInput.value = 720')
      action_runner.ExecuteJavaScript('maxHeightInput.value = 720')
      action_runner.ClickElement('button[id="getMedia"]')
      action_runner.Wait(2)
      # Wait until local video FPS becomes larger than 29
      action_runner.WaitForJavaScriptCondition(
          'localVideoFps > 29')
      action_runner.ClickElement('button[id="connect"]')
      action_runner.Wait(45)

class WebrtcIntelPageSet(story.StorySet):
  def __init__(self):
    super(WebrtcIntelPageSet, self).__init__(
        cloud_storage_bucket=story.PUBLIC_BUCKET)

    self.AddStory(VideoCallIntel(self, tags=['peerconnection']))
