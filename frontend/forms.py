from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Layout, Submit
from crispy_forms.bootstrap import AppendedText, FormActions, InlineRadios, Tab, TabHolder

from frontend.models import EDID

class UploadEDIDForm(forms.Form):
    edid_file = forms.FileField(label='EDID File')

class BaseForm(forms.ModelForm):
    """Base class for forms, provides common functions."""

    def _check_required_field(self, cleaned_data, fields):
        """Return validation error when a required field is empty.

        To be used for fields that are required depending on other field value."""

        for field in fields:
            if not cleaned_data.get(field):
                self._errors[field] = self.error_class(['This field is required.'])
                if field in cleaned_data:
                    del cleaned_data[field]

        return cleaned_data

    def _nullify_field(self, cleaned_data, fields):
        """Sets field value to Null.

        To be used for unused fields.
        """

        for field in fields:
            cleaned_data[field] = None

        return cleaned_data

class EditEDIDForm(BaseForm):
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
                    AppendedText('bdp_max_horizontal_image_size', 'cm'),
                    AppendedText('bdp_max_vertical_image_size', 'cm'),
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
                    AppendedText('mrl_min_horizontal_rate', 'kHz'),
                    AppendedText('mrl_max_horizontal_rate', 'kHz'),
                    AppendedText('mrl_min_vertical_rate', 'Hz'),
                    AppendedText('mrl_max_vertical_rate', 'Hz'),
                    AppendedText('mrl_max_pixel_clock', 'MHz'),
                    'mrl_secondary_GTF_curve_supported',
                    AppendedText('mrl_secondary_GTF_start_frequency', 'kHz'),
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

        # ID Serial Number, 32-bit
        # MinValueValidator is added by field type PositiveIntegerField
        self.fields['manufacturer_serial_number'].validators.append(MaxValueValidator(4294967295))

        # Year of manufacture, 1990-2245
        self.fields['year_of_manufacture'].validators.append(MinValueValidator(1990))
        self.fields['year_of_manufacture'].validators.append(MaxValueValidator(2245))

        ###bdp=Basic display parameters
        self.fields['bdp_max_horizontal_image_size'].validators.append(MaxValueValidator(255))
        self.fields['bdp_max_vertical_image_size'].validators.append(MaxValueValidator(255))

        self.fields['bdp_display_gamma'].validators.append(MinValueValidator(1.00))
        self.fields['bdp_display_gamma'].validators.append(MaxValueValidator(3.54))

        ###chr=Chromaticity
        for chr_color in ['chr_red_x', 'chr_red_y', 'chr_green_x', 'chr_green_y',
                          'chr_blue_x', 'chr_blue_y', 'chr_white_x', 'chr_white_y']:
            self.fields[chr_color].validators.append(MinValueValidator(0.0))
            self.fields[chr_color].validators.append(MaxValueValidator(0.999))

        ###mrl=Monitor range limits
        self.fields['mrl_min_horizontal_rate'].validators.append(MinValueValidator(1))
        self.fields['mrl_min_horizontal_rate'].validators.append(MaxValueValidator(255))

        self.fields['mrl_max_horizontal_rate'].validators.append(MinValueValidator(1))
        self.fields['mrl_max_horizontal_rate'].validators.append(MaxValueValidator(255))

        self.fields['mrl_min_vertical_rate'].validators.append(MinValueValidator(1))
        self.fields['mrl_min_vertical_rate'].validators.append(MaxValueValidator(255))

        self.fields['mrl_max_vertical_rate'].validators.append(MinValueValidator(1))
        self.fields['mrl_max_vertical_rate'].validators.append(MaxValueValidator(255))

        self.fields['mrl_max_pixel_clock'].validators.append(MinValueValidator(10))
        self.fields['mrl_max_pixel_clock'].validators.append(MaxValueValidator(255))

        self.fields['mrl_secondary_GTF_start_frequency'].validators.append(MaxValueValidator(510))

        self.fields['mrl_secondary_GTF_C'].validators.append(MaxValueValidator(127))
        self.fields['mrl_secondary_GTF_M'].validators.append(MaxValueValidator(65535))
        self.fields['mrl_secondary_GTF_K'].validators.append(MaxValueValidator(255))
        self.fields['mrl_secondary_GTF_J'].validators.append(MaxValueValidator(127))

    def clean_week_of_manufacture(self):
        week_of_manufacture = self.cleaned_data['week_of_manufacture']

        weeks_range = range(0, 55)
        weeks_range.append(255)

        if week_of_manufacture not in weeks_range:
            raise forms.ValidationError('This field allowed range is 0-54 or 255.')

        return week_of_manufacture

    def clean_mrl_max_pixel_clock(self):
        mrl_max_pixel_clock = self.cleaned_data['mrl_max_pixel_clock']

        if mrl_max_pixel_clock:
            if not mrl_max_pixel_clock % 10 == 0:
                raise forms.ValidationError('This field should be a multiple of 10MHz.')

        return mrl_max_pixel_clock

    def clean(self):
        cleaned_data = super(EditEDIDForm, self).clean()

        ###Basic display video input
        #Set unused video input fields to null
        bdp_video_input = cleaned_data.get('bdp_video_input')
        if not bdp_video_input:
            #Analog
            self._nullify_field(cleaned_data, ['bdp_video_input_DFP_1'])

            if not cleaned_data.get('bdp_signal_level_standard'):
                cleaned_data = self._check_required_field(cleaned_data, ['bdp_signal_level_standard'])
        else:
            #Digital
            self._nullify_field(cleaned_data, ['bdp_signal_level_standard', 'bdp_blank_to_black_setup',
                                               'bdp_separate_syncs', 'bdp_composite_sync', 'bdp_sync_on_green_video',
                                               'bdp_vsync_serration'])

        ###Monitor Range Limits
        mrl_fields = ['mrl_min_horizontal_rate', 'mrl_max_horizontal_rate',
                      'mrl_min_vertical_rate', 'mrl_max_vertical_rate',
                      'mrl_max_pixel_clock']
        mrl_secondary_GTF_fields = ['mrl_secondary_GTF_start_frequency', 'mrl_secondary_GTF_C', 'mrl_secondary_GTF_M',
                                    'mrl_secondary_GTF_K', 'mrl_secondary_GTF_J']

        #If Monitor Range Limits is enabled make sure all its fields are required
        monitor_range_limits = cleaned_data.get('monitor_range_limits')
        if monitor_range_limits:
            cleaned_data = self._check_required_field(cleaned_data, mrl_fields)

            #If Secondary GTF curve is enabled make sure all its fields are required
            mrl_secondary_GTF_curve_supported = cleaned_data.get('mrl_secondary_GTF_curve_supported')
            if mrl_secondary_GTF_curve_supported:
                cleaned_data = self._check_required_field(cleaned_data, mrl_secondary_GTF_fields)
            #If Secondary GTF curve is disabled set all its fields to null
            else:
                self._nullify_field(cleaned_data, mrl_secondary_GTF_fields)
        #If Monitor Range Limits is disabled set all its fields to null
        else:
            self._nullify_field(cleaned_data, mrl_fields)
            self._nullify_field(cleaned_data, ['mrl_secondary_GTF_curve_supported'])
            self._nullify_field(cleaned_data, mrl_secondary_GTF_fields)

        return cleaned_data
