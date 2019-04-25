from cProfile import label
from collections import namedtuple
from itertools import chain, repeat
Measurement = namedtuple('Measurement', ['units', 'perf_pattern', 'perf_spl'])


class CoremarkIntelResults():
    def __init__(self):
        self.pattern = '\s+\d+'
        self.labels = ['iterations']


class CrXprtIntelResults():
    """
    Process test_that results for CrXPRT. Example output as follows.

    <snip>/graphics_CrXprtIntel [  PASSED  ]
    <snip>/graphics_CrXprtIntel   3dmath                   9641
    <snip>/graphics_CrXprtIntel   collage_pnacl            2740
    <snip>/graphics_CrXprtIntel   facedetect               3378
    <snip>/graphics_CrXprtIntel   genome                   8805
    <snip>/graphics_CrXprtIntel   notes                    439
    <snip>/graphics_CrXprtIntel   photoedit                589.5
    <snip>/graphics_CrXprtIntel   score                    72.6
    <snip>/graphics_CrXprtIntel   stocksdash               1381.5
    """
    def __init__(self):
        self.pattern = '\s+\d.+'
        self.labels = ['3dmath', 'collage_pnacl', 'facedetect', 'genome',
                       'notes', 'photoedit', 'score', 'stocksdash']
        self.measurements = []
        for lbl in self.labels:
            self.measurements.append(Measurement('score',
                                                 lbl + ", .*?,",
                                                 lbl + ", "))


class StreamIntelResults():
    def __init__(self):
        self.pattern = '\s+\d+'
        self.labels = ['Add', 'Copy', 'Scale', 'Triad']
        self.measurements = []
        for lbl in self.labels:
            self.measurements.append(Measurement(lbl,
                                                 lbl + ", .*?,",
                                                 lbl + ", "))


class SpecIntelResults():
    def __init__(self):
        self.pattern = '\s+\W+\d+\W+\d+\.*\d*\W+'
        self.labels = ["164.gzip", "175.vpr", "176.gcc",
                       "181.mcf", "186.crafty", "197.parser",
                       "252.eon", "253.perlbmk", "254.gap",
                       "255.vortex", "256.bzip2", "300.twolf",
                       "Overall"]


class BootPerfResults():
    def __init__(self):
        self.pattern = '\s+\d+'
        self.labels = ['seconds_kernel_to_login',
                       'seconds_power_on_to_login',
                       'seconds_reboot_time']
        self.measurements = []
        for lbl in self.labels:
            self.measurements.append(Measurement(lbl,
                                                 lbl + ", .*?,",
                                                 lbl + ", "))


class Glmark2Results():
    def __init__(self):
        self.pattern = '\s+\d+'
        self.has_subtests = True
        self.labels = [
            'buffer.columns_200.interleave_false.update-dispersion_0.9.update'
            '-fraction_0.5.update-method_map',
            'buffer.columns_200.interleave_false.update-dispersion_0.9.update'
            '-fraction_0.5.update-method_subdata',
            'buffer.columns_200.interleave_true.update-dispersion_0.9.update-'
            'fraction_0.5.update-method_map',
            'build.use-vbo_false',
            'build.use-vbo_true',
            'bump.bump-render_height',
            'bump.bump-render_high-poly',
            'bump.bump-render_normals',
            'conditionals.fragment-steps_0.vertex-steps_0',
            'conditionals.fragment-steps_0.vertex-steps_5',
            'conditionals.fragment-steps_5.vertex-steps_0',
            'desktop.blur-radius_5.effect_blur.passes_1.separable_true.windows_4',
            'desktop.effect_shadow.windows_4',
            'effect2d.kernel_0-1-0_1--4-1_0-1-0_',
            'effect2d.kernel_1-1-1-1-1_1-1-1-1-1_1-1-1-1-1_',
            'function.fragment-complexity_low.fragment-steps_5',
            'function.fragment-complexity_medium.fragment-steps_5',
            'gem_objects_bytes',
            'gem_objects_objects',
            'glmark2_score',
            'ideas.speed_duration',
            'jellyfish.default',
            'loop.fragment-loop_false.fragment-steps_5.vertex-steps_5',
            'loop.fragment-steps_5.fragment-uniform_false.vertex-steps_5',
            'loop.fragment-steps_5.fragment-uniform_true.vertex-steps_5',
            'meminfo_MemUsed',
            'meminfo_SwapUsed',
            'memory_bytes',
            'memory_objects',
            'pulsar.light_false.quads_5.texture_false',
            'refract.default',
            'shading.shading_blinn-phong-inf',
            'shading.shading_cel',
            'shading.shading_gouraud',
            'shading.shading_phong',
            'shadow.default',
            'terrain.default',
            'texture.texture-filter_linear',
            'texture.texture-filter_mipmap',
            'texture.texture-filter_nearest']
        self.measurements = []
        for lbl in self.labels:
            self.measurements.append(Measurement(lbl,
                                                 lbl + ", .*?,",
                                                 lbl + ", "))


class GlbenchResults():
    def __init__(self):
        self.pattern = '\s+\d+'
        self.has_subtests = True
        self.labels = ['attribute_fetch_shader',
                       'attribute_fetch_shader_2_attr',
                       'attribute_fetch_shader_4_attr',
                       'attribute_fetch_shader_8_attr',
                       'clear_color',
                       'clear_colordepth',
                       'clear_colordepthstencil',
                       'clear_depth',
                       'clear_depthstencil',
                       'compositing',
                       'compositing_no_fill',
                       'context_glsimple',
                       'context_nogl',
                       'fbofill_tex_bilinear_1024',
                       'fbofill_tex_bilinear_128',
                       'fbofill_tex_bilinear_2048',
                       'fbofill_tex_bilinear_256',
                       'fbofill_tex_bilinear_32',
                       'fbofill_tex_bilinear_4096',
                       'fbofill_tex_bilinear_512',
                       'fbofill_tex_bilinear_64',
                       'fill_solid',
                       'fill_solid_blended',
                       'fill_solid_depth_neq',
                       'fill_solid_depth_never',
                       'fill_tex_bilinear',
                       'fill_tex_nearest',
                       'fill_tex_trilinear_linear_01',
                       'fill_tex_trilinear_linear_04',
                       'fill_tex_trilinear_linear_05',
                       'gem_objects_bytes',
                       'gem_objects_objects',
                       'meminfo_MemUsed',
                       'meminfo_SwapUsed',
                       'memory_bytes',
                       'memory_objects',
                       'pixel_read',
                       'pixel_read_2',
                       'pixel_read_3',
                       'swap_glsimple',
                       'swap_nogl',
                       'texture_reuse_luminance_teximage2d_1024',
                       'texture_reuse_luminance_teximage2d_128',
                       'texture_reuse_luminance_teximage2d_1536',
                       'texture_reuse_luminance_teximage2d_2048',
                       'texture_reuse_luminance_teximage2d_256',
                       'texture_reuse_luminance_teximage2d_32',
                       'texture_reuse_luminance_teximage2d_512',
                       'texture_reuse_luminance_teximage2d_768',
                       'texture_reuse_luminance_texsubimage2d_1024',
                       'texture_reuse_luminance_texsubimage2d_128',
                       'texture_reuse_luminance_texsubimage2d_1536',
                       'texture_reuse_luminance_texsubimage2d_2048',
                       'texture_reuse_luminance_texsubimage2d_256',
                       'texture_reuse_luminance_texsubimage2d_32',
                       'texture_reuse_luminance_texsubimage2d_512',
                       'texture_reuse_luminance_texsubimage2d_768',
                       'texture_reuse_rgba_teximage2d_1024',
                       'texture_reuse_rgba_teximage2d_128',
                       'texture_reuse_rgba_teximage2d_1536',
                       'texture_reuse_rgba_teximage2d_2048',
                       'texture_reuse_rgba_teximage2d_256',
                       'texture_reuse_rgba_teximage2d_32',
                       'texture_reuse_rgba_teximage2d_512',
                       'texture_reuse_rgba_teximage2d_768',
                       'texture_reuse_rgba_texsubimage2d_1024',
                       'texture_reuse_rgba_texsubimage2d_128',
                       'texture_reuse_rgba_texsubimage2d_1536',
                       'texture_reuse_rgba_texsubimage2d_2048',
                       'texture_reuse_rgba_texsubimage2d_256',
                       'texture_reuse_rgba_texsubimage2d_32',
                       'texture_reuse_rgba_texsubimage2d_512',
                       'texture_reuse_rgba_texsubimage2d_768',
                       'texture_update_luminance_teximage2d_1024',
                       'texture_update_luminance_teximage2d_128',
                       'texture_update_luminance_teximage2d_1536',
                       'texture_update_luminance_teximage2d_2048',
                       'texture_update_luminance_teximage2d_256',
                       'texture_update_luminance_teximage2d_32',
                       'texture_update_luminance_teximage2d_512',
                       'texture_update_luminance_teximage2d_768',
                       'texture_update_luminance_texsubimage2d_1024',
                       'texture_update_luminance_texsubimage2d_128',
                       'texture_update_luminance_texsubimage2d_1536',
                       'texture_update_luminance_texsubimage2d_2048',
                       'texture_update_luminance_texsubimage2d_256',
                       'texture_update_luminance_texsubimage2d_32',
                       'texture_update_luminance_texsubimage2d_512',
                       'texture_update_luminance_texsubimage2d_768',
                       'texture_update_rgba_teximage2d_1024',
                       'texture_update_rgba_teximage2d_128',
                       'texture_update_rgba_teximage2d_1536',
                       'texture_update_rgba_teximage2d_2048',
                       'texture_update_rgba_teximage2d_256',
                       'texture_update_rgba_teximage2d_32',
                       'texture_update_rgba_teximage2d_512',
                       'texture_update_rgba_teximage2d_768',
                       'texture_update_rgba_texsubimage2d_1024',
                       'texture_update_rgba_texsubimage2d_128',
                       'texture_update_rgba_texsubimage2d_1536',
                       'texture_update_rgba_texsubimage2d_2048',
                       'texture_update_rgba_texsubimage2d_256',
                       'texture_update_rgba_texsubimage2d_32',
                       'texture_update_rgba_texsubimage2d_512',
                       'texture_update_rgba_texsubimage2d_768',
                       'texture_upload_luminance_teximage2d_1024',
                       'texture_upload_luminance_teximage2d_128',
                       'texture_upload_luminance_teximage2d_1536',
                       'texture_upload_luminance_teximage2d_2048',
                       'texture_upload_luminance_teximage2d_256',
                       'texture_upload_luminance_teximage2d_32',
                       'texture_upload_luminance_teximage2d_512',
                       'texture_upload_luminance_teximage2d_768',
                       'texture_upload_luminance_texsubimage2d_1024',
                       'texture_upload_luminance_texsubimage2d_128',
                       'texture_upload_luminance_texsubimage2d_1536',
                       'texture_upload_luminance_texsubimage2d_2048',
                       'texture_upload_luminance_texsubimage2d_256',
                       'texture_upload_luminance_texsubimage2d_32',
                       'texture_upload_luminance_texsubimage2d_512',
                       'texture_upload_luminance_texsubimage2d_768',
                       'texture_upload_rgba_teximage2d_1024',
                       'texture_upload_rgba_teximage2d_128',
                       'texture_upload_rgba_teximage2d_1536',
                       'texture_upload_rgba_teximage2d_2048',
                       'texture_upload_rgba_teximage2d_256',
                       'texture_upload_rgba_teximage2d_32',
                       'texture_upload_rgba_teximage2d_512',
                       'texture_upload_rgba_teximage2d_768',
                       'texture_upload_rgba_texsubimage2d_1024',
                       'texture_upload_rgba_texsubimage2d_128',
                       'texture_upload_rgba_texsubimage2d_1536',
                       'texture_upload_rgba_texsubimage2d_2048',
                       'texture_upload_rgba_texsubimage2d_256',
                       'texture_upload_rgba_texsubimage2d_32',
                       'texture_upload_rgba_texsubimage2d_512',
                       'texture_upload_rgba_texsubimage2d_768',
                       'triangle_setup',
                       'triangle_setup_all_culled',
                       'triangle_setup_half_culled',
                       'varyings_shader_1',
                       'varyings_shader_2',
                       'varyings_shader_4',
                       'varyings_shader_8',
                       'yuv_shader_1',
                       'yuv_shader_2',
                       'yuv_shader_3',
                       'yuv_shader_4',
                       'gem_objects_bytes',
                       'gem_objects_objects',
                       'meminfo_MemUsed',
                       'meminfo_SwapUsed',
                       'memory_bytes',
                       'memory_objects']

        self.measurements = []
        for lbl in self.labels:
            self.measurements.append(Measurement(lbl,
                                                 lbl + ", .*?,",
                                                 lbl + ", "))

class SpeedometerResults():
    def __init__(self):
        self.pattern = '\s+\d+'
        self.has_subtests = True
        self.labels = ['Avg AngularJS-TodoMVC', 'Sd  AngularJS-TodoMVC',
                       'Avg BackboneJS-TodoMVC', 'Sd  BackboneJS-TodoMVC',
                       'Avg EmberJS-TodoMVC', 'Sd  EmberJS-TodoMVC',
                       'Avg FlightJS-TodoMVC', 'Sd  FlightJS-TodoMVC',
                       'Avg React-TodoMVC', 'Sd  React-TodoMVC',
                       'Avg Total', 'Sd  Total',
                       'Avg VanillaJS-TodoMVC', 'Sd  VanillaJS-TodoMVC',
                       'Avg jQuery-TodoMVC', 'Sd  jQuery-TodoMVC']
        self.measurements = []
        for lbl in self.labels:
            self.measurements.append(Measurement("ms",
                                                 lbl + ", .*?,",
                                                 lbl + ", "))

class PageCyclerTypical25Results():
    def __init__(self):
        self.pattern = '\s+\d+'
        self.has_subtests = True
        self.labels = ['Avg cold_times', 'Sd  cold_times',
                       'Avg warm_times', 'Sd  warm_times']
        self.measurements = []
        for lbl in self.labels:
            self.measurements.append(Measurement("ms",
                                                 lbl + ", .*?,",
                                                 lbl + ", "))

class SmoothnessTop25SmoothResults():
    def __init__(self):
        self.pattern = '\s+\d+'
        self.has_subtests = False
        self.labels = ['percentage_smooth']
        self.measurements = []
        for lbl in self.labels:
            self.measurements.append(Measurement("percent",
                                                 lbl + ", .*?,",
                                                 lbl + ", "))

class PageCyclerV2Typical25Results():
    def __init__(self):
        self.pattern = '\s+\d+'
        self.has_subtests = False
        self.labels = ['timeToOnload']
        self.measurements = []
        for lbl in self.labels:
            self.measurements.append(Measurement("ms",
                                                 lbl + ", .*?,",
                                                 lbl + ", "))

class TabSwitchingTypical25Results():
    def __init__(self):
        self.pattern = '\s+\d+'
        self.has_subtests = False
        self.labels = ['tab_switching_latency']
        self.measurements = []
        for lbl in self.labels:
            self.measurements.append(Measurement("ms",
                                                 lbl + ", .*?,",
                                                 lbl + ", "))

class WebRtcResults():
    def __init__(self):
        self.pattern = '\s+\d+'
        self.has_subtests = False
        self.labels = ['peer_connection_0_bwe_goog_transmit_bitrate',
                       'peer_connection_1_video_goog_frame_rate_received']
        self.measurements = []

        for lbl in self.labels:
            units = "fps" if "frame_rate" in lbl else "bit/s"
            self.measurements.append(Measurement(units,
                                                 lbl + ", .*?,",
                                                 lbl + ", "))
