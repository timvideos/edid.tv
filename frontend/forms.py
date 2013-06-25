from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Layout, Submit
from crispy_forms.bootstrap import FormActions, InlineRadios, Tab, TabHolder

from frontend.models import EDID

class UploadEDIDForm(forms.Form):
    edid_file = forms.FileField(label='EDID File')

class EditEDIDForm(forms.ModelForm):
    class Meta:
        model = EDID
        fields = [#Main Fields
                  'manufacturer', 'manufacturer_product_code', 'manufacturer_serial_number',
                  'week_of_manufacture', 'year_of_manufacture', 'EDID_version',
                  'monitor_name', 'monitor_serial_number', 'monitor_data_string',
                  #Basic Display Parameters
                  'bdp_video_input', 'bdp_signal_level_standard', 'bdp_blank_to_black_setup',
                  'bdp_separate_syncs', 'bdp_composite_sync', 'bdp_sync_on_green_video',
                  'bdp_vsync_serration', 'bdp_video_input_DFP_1', 'bdp_max_horizontal_image_size',
                  'bdp_max_vertical_image_size', 'bdp_display_gamma', 'bdp_feature_display_type',
                  'bdp_feature_standby', 'bdp_feature_suspend', 'bdp_feature_active_off',
                  'bdp_feature_standard_sRGB', 'bdp_feature_preferred_timing_mode', 'bdp_feature_default_GTF',
                  #Chromaticity
                  'chr_red_x', 'chr_red_y', 'chr_green_x', 'chr_green_y', 'chr_blue_x', 'chr_blue_y',
                  'chr_white_x', 'chr_white_y', 'est_timings_720_400_70', 'est_timings_720_400_88',
                  #Established Timings
                  'est_timings_640_480_60', 'est_timings_640_480_67', 'est_timings_640_480_72',
                  'est_timings_640_480_75', 'est_timings_800_600_56', 'est_timings_800_600_60',
                  'est_timings_800_600_72', 'est_timings_800_600_75', 'est_timings_832_624_75',
                  'est_timings_1024_768_87', 'est_timings_1024_768_60', 'est_timings_1024_768_70',
                  'est_timings_1024_768_75', 'est_timings_1280_1024_75',
                  #Monitor Range Limits
                  'monitor_range_limits', 'mrl_min_horizontal_rate', 'mrl_max_horizontal_rate',
                  'mrl_min_vertical_rate', 'mrl_max_vertical_rate', 'mrl_max_pixel_clock',
                  'mrl_secondary_GTF_curve_supported', 'mrl_secondary_GTF_start_frequency', 'mrl_secondary_GTF_C',
                  'mrl_secondary_GTF_M', 'mrl_secondary_GTF_K', 'mrl_secondary_GTF_J']

        widgets = {'bdp_blank_to_black_setup': forms.CheckboxInput,
                   'bdp_separate_syncs': forms.CheckboxInput,
                   'bdp_composite_sync': forms.CheckboxInput,
                   'bdp_sync_on_green_video': forms.CheckboxInput,
                   'bdp_vsync_serration': forms.CheckboxInput,
                   'bdp_video_input_DFP_1': forms.CheckboxInput,
                   'mrl_secondary_GTF_curve_supported': forms.CheckboxInput}

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    'Main Fields',
                    'manufacturer',
                    'manufacturer_product_code',
                    'manufacturer_serial_number',
                    'week_of_manufacture',
                    'year_of_manufacture',
                    'EDID_version',
                    'monitor_name',
                    'monitor_serial_number',
                    'monitor_data_string'
                ),
                Tab(
                    'Basic Display Parameters',
                    InlineRadios('bdp_video_input'),
                    'bdp_signal_level_standard',
                    'bdp_blank_to_black_setup',
                    'bdp_separate_syncs',
                    'bdp_composite_sync',
                    'bdp_sync_on_green_video',
                    'bdp_vsync_serration',
                    'bdp_video_input_DFP_1',
                    'bdp_max_horizontal_image_size',
                    'bdp_max_vertical_image_size',
                    'bdp_display_gamma',
                    'bdp_feature_display_type',
                    'bdp_feature_standby',
                    'bdp_feature_suspend',
                    'bdp_feature_active_off',
                    'bdp_feature_standard_sRGB',
                    'bdp_feature_preferred_timing_mode',
                    'bdp_feature_default_GTF'
                ),
                Tab(
                    'Chromaticity',
                    'chr_red_x',
                    'chr_red_y',
                    'chr_green_x',
                    'chr_green_y',
                    'chr_blue_x',
                    'chr_blue_y',
                    'chr_white_x',
                    'chr_white_y'
                ),
                Tab(
                    'Established Timings',
                    'est_timings_720_400_70',
                    'est_timings_720_400_88',
                    'est_timings_640_480_60',
                    'est_timings_640_480_67',
                    'est_timings_640_480_72',
                    'est_timings_640_480_75',
                    'est_timings_800_600_56',
                    'est_timings_800_600_60',
                    'est_timings_800_600_72',
                    'est_timings_800_600_75',
                    'est_timings_832_624_75',
                    'est_timings_1024_768_87',
                    'est_timings_1024_768_60',
                    'est_timings_1024_768_70',
                    'est_timings_1024_768_75',
                    'est_timings_1280_1024_75'
                ),
                Tab(
                    'Monitor Range Limits',
                    'monitor_range_limits',
                    'mrl_min_horizontal_rate',
                    'mrl_max_horizontal_rate',
                    'mrl_min_vertical_rate',
                    'mrl_max_vertical_rate',
                    'mrl_max_pixel_clock',
                    'mrl_secondary_GTF_curve_supported',
                    'mrl_secondary_GTF_start_frequency',
                    'mrl_secondary_GTF_C',
                    'mrl_secondary_GTF_M',
                    'mrl_secondary_GTF_K',
                    'mrl_secondary_GTF_J',
                )
            ),
            FormActions(
                Submit('submit', 'Submit'),
                #TODO: Use show_edid link
                Button('cancel', 'Cancel', onclick='history.go(-1);')
            )
        )
        super(EditEDIDForm, self).__init__(*args, **kwargs)
