# E1002: Use of super on an old style class
# pylint: disable-msg=E1002

import base64
import re

from django import forms
from django.conf import settings
from django.urls import reverse
from django.core.validators import MaxValueValidator, MinValueValidator

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Fieldset, HTML, Layout, Submit
from crispy_forms.bootstrap import (AppendedText, FormActions, InlineRadios,
                                    Tab, TabHolder)

from edid_parser.edid_parser import EDIDParser, EDIDParsingError

from frontend.models import (EDID, StandardTiming, DetailedTiming, Comment,
                             GrabberRelease)
from frontend.utils import form_nullify_fields


class EDIDUploadForm(forms.Form):
    edid_file = forms.FileField(label='EDID File')

    def __init__(self, *args, **kwargs):
        super(EDIDUploadForm, self).__init__(*args, **kwargs)
        self.edid_binary = None
        self.edid_data = None
        self.edid_base64 = None

    def clean_edid_file(self):
        edid_file = self.cleaned_data['edid_file']

        self.edid_binary = edid_file.read()

        # Parse EDID file
        try:
            self.edid_data = EDIDParser(self.edid_binary).data
        except EDIDParsingError as msg:
            raise forms.ValidationError(msg)

        # Encode in base64
        self.edid_base64 = base64.b64encode(self.edid_binary)

        # Check for checksum in DB
        if EDID.objects.filter(file_base64=self.edid_base64).exists():
            raise forms.ValidationError('This file have been uploaded before.')

        return edid_file


class EDIDTextUploadForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)
    text_type = forms.CharField(widget=forms.HiddenInput)

    _hex_addresses = re.compile(r'0x[0-9A-Fa-f]+')
    _whitespaces = re.compile(r'\s')
    _non_hex = re.compile(r'[^0-9A-Fa-f]')

    def __init__(self, *args, **kwargs):
        super(EDIDTextUploadForm, self).__init__(*args, **kwargs)
        self.edid_list = []

    def clean_text_type(self):
        text_type = self.cleaned_data['text_type']

        if text_type not in ['hex', 'xrandr']:
            raise forms.ValidationError('Text type is invalid.')

        return text_type

    def clean(self):
        cleaned_data = super(EDIDTextUploadForm, self).clean()

        text = cleaned_data.get('text')
        text_type = cleaned_data.get('text_type')

        if not text or not text_type:
            raise forms.ValidationError('Please fill the form.')

        if text_type == 'hex':
            # Remove hex addresses, like 0x40
            text = self._hex_addresses.sub('', text)

            # Remove spaces, tabs and newlines
            text = self._whitespaces.sub('', text)

            # Check for non-hex digits
            if bool(self._non_hex.search(text)):
                raise forms.ValidationError(
                    'Please remove all non-hex digits.'
                )

            # Convert hex to binary and add it to EDIDs list
            self.edid_list.append(text.decode('hex'))
        elif text_type == 'xrandr':
            inside_edid = False
            edid_hex = ''

            # Parse text line-by-line
            for line in text.splitlines():
                # If inside edid block
                if inside_edid:
                    if line.startswith(u'\t\t'):
                        edid_hex += line[2:]
                    # edid block ended
                    else:
                        inside_edid = False
                        # Convert hex to binary and add it to EDIDs list
                        self.edid_list.append(edid_hex.decode('hex'))
                # Look for edid block
                elif line == u'\tEDID:':
                    inside_edid = True

        if self.edid_list == []:
            raise forms.ValidationError('No EDID was parsed.')

        return cleaned_data


class BaseForm(forms.ModelForm):
    """Base class for forms, provides common functions."""

    def _check_required_field(self, cleaned_data, fields):
        """Return validation error when a required field is empty.

        To be used for fields that are required depending on other field
        value."""

        for field in fields:
            # It passed other validators
            if field not in self._errors:
                # No value found for it
                if cleaned_data.get(field) is None:
                    self._errors[field] = self.error_class(
                        ['This field is required.']
                    )

                    # This field is no longer valid. Remove it from the
                    # cleaned data.
                    if field in cleaned_data:
                        del cleaned_data[field]

        return cleaned_data


class EDIDUpdateForm(BaseForm):
    class Meta(object):
        model = EDID
        fields = [
            # Main Fields
            'manufacturer', 'manufacturer_product_code',
            'manufacturer_serial_number', 'week_of_manufacture',
            'year_of_manufacture', 'version', 'monitor_name',
            'monitor_serial_number', 'monitor_data_string',
            # Basic Display Parameters
            'bdp_video_input', 'bdp_signal_level_standard',
            'bdp_blank_to_black_setup', 'bdp_separate_syncs',
            'bdp_composite_sync', 'bdp_sync_on_green_video',
            'bdp_vsync_serration', 'bdp_video_input_dfp_1',
            'bdp_max_horizontal_image_size', 'bdp_max_vertical_image_size',
            'bdp_display_gamma', 'bdp_feature_display_type',
            'bdp_feature_standby', 'bdp_feature_suspend',
            'bdp_feature_active_off', 'bdp_feature_standard_srgb',
            'bdp_feature_pref_timing_mode', 'bdp_feature_default_gtf',
            # Chromaticity
            'chr_red_x', 'chr_red_y', 'chr_green_x', 'chr_green_y',
            'chr_blue_x', 'chr_blue_y', 'chr_white_x', 'chr_white_y',
            # Established Timings
            'est_timings_720_400_70', 'est_timings_720_400_88',
            'est_timings_640_480_60', 'est_timings_640_480_67',
            'est_timings_640_480_72', 'est_timings_640_480_75',
            'est_timings_800_600_56', 'est_timings_800_600_60',
            'est_timings_800_600_72', 'est_timings_800_600_75',
            'est_timings_832_624_75', 'est_timings_1024_768_87',
            'est_timings_1024_768_60', 'est_timings_1024_768_70',
            'est_timings_1024_768_75', 'est_timings_1280_1024_75',
            # Monitor Range Limits
            'monitor_range_limits', 'mrl_min_horizontal_rate',
            'mrl_max_horizontal_rate', 'mrl_min_vertical_rate',
            'mrl_max_vertical_rate', 'mrl_max_pixel_clock',
            'mrl_secondary_gtf_curve_support',
            'mrl_secondary_gtf_start_freq', 'mrl_secondary_gtf_c',
            'mrl_secondary_gtf_m', 'mrl_secondary_gtf_k',
            'mrl_secondary_gtf_j',
        ]

        # Change widget for NullBooleanField fields to act like regular
        # BooleanField
        widgets = {
            'bdp_blank_to_black_setup': forms.CheckboxInput,
            'bdp_separate_syncs': forms.CheckboxInput,
            'bdp_composite_sync': forms.CheckboxInput,
            'bdp_sync_on_green_video': forms.CheckboxInput,
            'bdp_vsync_serration': forms.CheckboxInput,
            'bdp_video_input_dfp_1': forms.CheckboxInput,
            'mrl_secondary_gtf_curve_support': forms.CheckboxInput,
        }

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
                    'version',
                    'monitor_name',
                    'monitor_serial_number',
                    'monitor_data_string',
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
                    'bdp_video_input_dfp_1',
                    AppendedText('bdp_max_horizontal_image_size', 'cm'),
                    AppendedText('bdp_max_vertical_image_size', 'cm'),
                    'bdp_display_gamma',
                    'bdp_feature_display_type',
                    'bdp_feature_standby',
                    'bdp_feature_suspend',
                    'bdp_feature_active_off',
                    'bdp_feature_standard_srgb',
                    'bdp_feature_pref_timing_mode',
                    'bdp_feature_default_gtf',
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
                    'chr_white_y',
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
                    'est_timings_1280_1024_75',
                ),
                Tab(
                    'Monitor Range Limits',
                    'monitor_range_limits',
                    AppendedText('mrl_min_horizontal_rate', 'kHz'),
                    AppendedText('mrl_max_horizontal_rate', 'kHz'),
                    AppendedText('mrl_min_vertical_rate', 'Hz'),
                    AppendedText('mrl_max_vertical_rate', 'Hz'),
                    AppendedText('mrl_max_pixel_clock', 'MHz'),
                    'mrl_secondary_gtf_curve_support',
                    AppendedText('mrl_secondary_gtf_start_freq', 'kHz'),
                    'mrl_secondary_gtf_c',
                    'mrl_secondary_gtf_m',
                    'mrl_secondary_gtf_k',
                    'mrl_secondary_gtf_j',
                )
            ),
            FormActions(
                Submit('submit', 'Submit'),
                HTML('<a class="btn" href="'
                     "{% url 'edid-detail' form.instance.pk %}"
                     '">Cancel</a>'),
            )
        )
        super(EDIDUpdateForm, self).__init__(*args, **kwargs)

        # ID Serial Number, 32-bit
        # MinValueValidator is added by field type PositiveIntegerField
        self.fields['manufacturer_serial_number'].validators.append(
            MaxValueValidator(4294967295))

        # Year of manufacture, 1990-2245
        self.fields['year_of_manufacture'].validators.append(
            MinValueValidator(1990))
        self.fields['year_of_manufacture'].validators.append(
            MaxValueValidator(2245))

        # bdp=Basic display parameters
        self.fields['bdp_max_horizontal_image_size'].validators.append(
            MaxValueValidator(255))
        self.fields['bdp_max_vertical_image_size'].validators.append(
            MaxValueValidator(255))

        self.fields['bdp_display_gamma'].validators.append(
            MinValueValidator(1.00))
        self.fields['bdp_display_gamma'].validators.append(
            MaxValueValidator(3.54))

        # chr=Chromaticity
        for chr_color in ['chr_red_x', 'chr_red_y', 'chr_green_x',
                          'chr_green_y', 'chr_blue_x', 'chr_blue_y',
                          'chr_white_x', 'chr_white_y']:
            self.fields[chr_color].validators.append(
                MinValueValidator(0.0))
            self.fields[chr_color].validators.append(
                MaxValueValidator(0.999))

        # mrl=Monitor range limits
        self.fields['mrl_min_horizontal_rate'].validators.append(
            MinValueValidator(1))
        self.fields['mrl_min_horizontal_rate'].validators.append(
            MaxValueValidator(255))

        self.fields['mrl_max_horizontal_rate'].validators.append(
            MinValueValidator(1))
        self.fields['mrl_max_horizontal_rate'].validators.append(
            MaxValueValidator(255))

        self.fields['mrl_min_vertical_rate'].validators.append(
            MinValueValidator(1))
        self.fields['mrl_min_vertical_rate'].validators.append(
            MaxValueValidator(255))

        self.fields['mrl_max_vertical_rate'].validators.append(
            MinValueValidator(1))
        self.fields['mrl_max_vertical_rate'].validators.append(
            MaxValueValidator(255))

        self.fields['mrl_max_pixel_clock'].validators.append(
            MinValueValidator(10))
        self.fields['mrl_max_pixel_clock'].validators.append(
            MaxValueValidator(255))

        self.fields['mrl_secondary_gtf_start_freq'].validators.append(
            MaxValueValidator(510))

        self.fields['mrl_secondary_gtf_c'].validators.append(
            MaxValueValidator(127))
        self.fields['mrl_secondary_gtf_m'].validators.append(
            MaxValueValidator(65535))
        self.fields['mrl_secondary_gtf_k'].validators.append(
            MaxValueValidator(255))
        self.fields['mrl_secondary_gtf_j'].validators.append(
            MaxValueValidator(127))

    def clean_week_of_manufacture(self):
        week_of_manufacture = self.cleaned_data['week_of_manufacture']

        weeks_range = range(0, 55)
        weeks_range.append(255)
        weeks_range.append(None)

        if week_of_manufacture not in weeks_range:
            raise forms.ValidationError('This field allowed range is'
                                        ' 0-54 or 255.')

        return week_of_manufacture

    def clean_mrl_max_pixel_clock(self):
        mrl_max_pixel_clock = self.cleaned_data['mrl_max_pixel_clock']

        if mrl_max_pixel_clock:
            if not mrl_max_pixel_clock % 10 == 0:
                raise forms.ValidationError('This field should be a multiple'
                                            ' of 10MHz.')

        return mrl_max_pixel_clock

    def clean(self):
        cleaned_data = super(EDIDUpdateForm, self).clean()

        # Basic display video input
        # Set unused video input fields to null
        bdp_video_input = cleaned_data.get('bdp_video_input')
        if not bdp_video_input:
            # Analog
            cleaned_data = form_nullify_fields(
                cleaned_data, ['bdp_video_input_dfp_1'])

            cleaned_data = self._check_required_field(
                cleaned_data, ['bdp_signal_level_standard'])
        else:
            # Digital
            cleaned_data = form_nullify_fields(
                cleaned_data, ['bdp_signal_level_standard',
                               'bdp_blank_to_black_setup',
                               'bdp_separate_syncs', 'bdp_composite_sync',
                               'bdp_sync_on_green_video',
                               'bdp_vsync_serration'])

        # Monitor Range Limits
        mrl_fields = ['mrl_min_horizontal_rate', 'mrl_max_horizontal_rate',
                      'mrl_min_vertical_rate', 'mrl_max_vertical_rate',
                      'mrl_max_pixel_clock']
        mrl_secondary_gtf_fields = ['mrl_secondary_gtf_start_freq',
                                    'mrl_secondary_gtf_c',
                                    'mrl_secondary_gtf_m',
                                    'mrl_secondary_gtf_k',
                                    'mrl_secondary_gtf_j']

        # If monitor range limits is enabled make sure all its fields are
        # required
        monitor_range_limits = cleaned_data.get('monitor_range_limits')
        if monitor_range_limits:
            cleaned_data = self._check_required_field(cleaned_data, mrl_fields)

            # If Secondary GTF curve is enabled make sure all its fields are
            # required
            mrl_secondary_gtf_curve_support = cleaned_data.get(
                'mrl_secondary_gtf_curve_support')
            if mrl_secondary_gtf_curve_support:
                cleaned_data = self._check_required_field(
                    cleaned_data, mrl_secondary_gtf_fields)
            # If Secondary GTF curve is disabled set all its fields to null
            else:
                cleaned_data = form_nullify_fields(
                    cleaned_data, mrl_secondary_gtf_fields)
        # If Monitor Range Limits is disabled set all its fields to null
        else:
            cleaned_data = form_nullify_fields(cleaned_data, mrl_fields)
            cleaned_data = form_nullify_fields(
                cleaned_data, ['mrl_secondary_gtf_curve_support'])
            cleaned_data = form_nullify_fields(
                cleaned_data, mrl_secondary_gtf_fields)

        return cleaned_data

    def save(self, commit=True):
        """Overrides save() method to set status to private."""
        instance = super(EDIDUpdateForm, self).save(commit=False)
        instance.status = EDID.STATUS_EDITED

        if commit:
            instance.save()

        return instance


class StandardTimingForm(BaseForm):
    class Meta(object):
        model = StandardTiming
        fields = ['horizontal_active', 'vertical_active', 'refresh_rate',
                  'aspect_ratio']

    def __init__(self, *args, **kwargs):
        # Store EDID object in the form
        self.edid = kwargs['initial'].get('edid')

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            AppendedText('horizontal_active', 'pixels'),
            AppendedText('vertical_active', 'pixels'),
            AppendedText('refresh_rate', 'Hz'),
            'aspect_ratio',
            FormActions(
                Submit('submit', 'Submit'),
                HTML('<a class="btn" href="'
                     "{% url 'edid-update' form.edid.pk %}"
                     '">Cancel</a>'),
            )
        )

        super(StandardTimingForm, self).__init__(*args, **kwargs)

        # Horizontal active, 256-2288 pixels
        self.fields['horizontal_active'].validators.append(
            MinValueValidator(256))
        self.fields['horizontal_active'].validators.append(
            MaxValueValidator(2288))

        # Vertical active
        # Vertical active = 256 and aspect_ratio == 16/9
        self.fields['vertical_active'].validators.append(
            MinValueValidator(144))
        # Vertical active = 2288 and aspect_ratio == 5/4
        self.fields['vertical_active'].validators.append(
            MaxValueValidator(1831))

        # Refresh rate, 60-123 Hz
        self.fields['refresh_rate'].validators.append(
            MinValueValidator(60))
        self.fields['refresh_rate'].validators.append(
            MaxValueValidator(123))

    def clean_horizontal_active(self):
        horizontal_active = self.cleaned_data['horizontal_active']

        if horizontal_active:
            if not horizontal_active % 8 == 0:
                raise forms.ValidationError('This field should be a multiple'
                                            ' of 8.')

        return horizontal_active

    def clean_aspect_ratio(self):
        aspect_ratio = self.cleaned_data['aspect_ratio']

        old_versions = [EDID.VERSION_1_0, EDID.VERSION_1_1, EDID.VERSION_1_2]

        if aspect_ratio == StandardTiming.ASPECT_RATIO_1_1:
            if self.edid.version not in old_versions:
                raise forms.ValidationError('1:1 aspect ratio is not allowed'
                                            ' with EDID 1.3 or newer.')
        elif aspect_ratio == StandardTiming.ASPECT_RATIO_16_10:
            if self.edid.version in old_versions:
                raise forms.ValidationError('16:10 aspect ratio is not allowed'
                                            ' prior to EDID 1.3.')

        return aspect_ratio


class DetailedTimingForm(BaseForm):
    class Meta(object):
        model = DetailedTiming
        fields = [
            # Horizontal
            'horizontal_active', 'horizontal_blanking',
            'horizontal_sync_offset', 'horizontal_sync_pulse_width',
            'horizontal_image_size', 'horizontal_border',
            # Vertical
            'vertical_active', 'vertical_blanking', 'vertical_sync_offset',
            'vertical_sync_pulse_width', 'vertical_image_size',
            'vertical_border',
            # Flags
            'pixel_clock', 'flags_interlaced', 'flags_stereo_mode',
            'flags_sync_scheme', 'flags_horizontal_polarity',
            'flags_vertical_polarity', 'flags_serrate',
            'flags_composite_polarity', 'flags_sync_on_rgb',
        ]

        # Change widget for NullBooleanField fields to act like regular
        # BooleanField
        widgets = {'flags_horizontal_polarity': forms.CheckboxInput,
                   'flags_vertical_polarity': forms.CheckboxInput,
                   'flags_serrate': forms.CheckboxInput,
                   'flags_composite_polarity': forms.CheckboxInput,
                   'flags_sync_on_rgb': forms.CheckboxInput}

    def __init__(self, *args, **kwargs):
        # Store EDID object in the form
        self.edid = kwargs['initial'].get('edid')

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            Fieldset(
                'Horizontal',
                AppendedText('horizontal_active', 'pixels'),
                AppendedText('horizontal_blanking', 'pixels'),
                AppendedText('horizontal_sync_offset', 'pixels'),
                AppendedText('horizontal_sync_pulse_width', 'pixels'),
                AppendedText('horizontal_image_size', 'mm'),
                AppendedText('horizontal_border', 'pixels')),
            Fieldset(
                'Vertical',
                AppendedText('vertical_active', 'lines'),
                AppendedText('vertical_blanking', 'lines'),
                AppendedText('vertical_sync_offset', 'lines'),
                AppendedText('vertical_sync_pulse_width', 'lines'),
                AppendedText('vertical_image_size', 'mm'),
                AppendedText('vertical_border', 'lines')),
            Fieldset(
                'Flags',
                AppendedText('pixel_clock', 'kHz'),
                'flags_interlaced',
                'flags_stereo_mode',
                'flags_sync_scheme',
                'flags_horizontal_polarity',
                'flags_vertical_polarity',
                'flags_serrate',
                'flags_composite_polarity',
                'flags_sync_on_rgb',
            ),
            FormActions(
                Submit('submit', 'Submit'),
                HTML('<a class="btn" href="'
                     "{% url 'edid-update' form.edid.pk %}"
                     '">Cancel</a>'),
            )
        )
        super(DetailedTimingForm, self).__init__(*args, **kwargs)

        # Pixel clock in kHz
        self.fields['pixel_clock'].validators.append(MinValueValidator(10))
        self.fields['pixel_clock'].validators.append(MaxValueValidator(655350))

        # 12 bits
        self.fields['horizontal_active'].validators.append(
            MaxValueValidator(4095))
        self.fields['horizontal_blanking'].validators.append(
            MaxValueValidator(4095))
        self.fields['horizontal_image_size'].validators.append(
            MaxValueValidator(4095))
        self.fields['vertical_active'].validators.append(
            MaxValueValidator(4095))
        self.fields['vertical_blanking'].validators.append(
            MaxValueValidator(4095))
        self.fields['vertical_image_size'].validators.append(
            MaxValueValidator(4095))

        # 10 bits
        self.fields['horizontal_sync_offset'].validators.append(
            MaxValueValidator(1023))
        self.fields['horizontal_sync_pulse_width'].validators.append(
            MaxValueValidator(1023))

        # 8 bits
        self.fields['horizontal_border'].validators.append(
            MaxValueValidator(255))
        self.fields['vertical_border'].validators.append(
            MaxValueValidator(255))

        # 6 bits
        self.fields['vertical_sync_offset'].validators.append(
            MaxValueValidator(63))
        self.fields['vertical_sync_pulse_width'].validators.append(
            MaxValueValidator(63))

    def clean_pixel_clock(self):
        pixel_clock = self.cleaned_data['pixel_clock']

        if pixel_clock:
            if not pixel_clock % 10 == 0:
                raise forms.ValidationError('This field should be a multiple'
                                            ' of 10.')

        return pixel_clock

    def clean(self):
        cleaned_data = super(DetailedTimingForm, self).clean()

        flags_sync_scheme = cleaned_data.get('flags_sync_scheme')
        fields_to_nullify = []

#        analog_composite = (flags_sync_scheme ==
#                            DetailedTiming.Sync_Scheme.Analog_Composite)
#        bipolar_analog_composite = (flags_sync_scheme ==
#                          DetailedTiming.Sync_Scheme.Bipolar_Analog_Composite)
        digital_composite = (flags_sync_scheme ==
                             DetailedTiming.Sync_Scheme.Digital_Composite)
        digital_separate = (flags_sync_scheme ==
                            DetailedTiming.Sync_Scheme.Digital_Separate)

        if not digital_separate:
            fields_to_nullify.extend(['flags_horizontal_polarity',
                                      'flags_vertical_polarity'])
        else:
            fields_to_nullify.append('flags_serrate')

        if not digital_composite:
            fields_to_nullify.append('flags_composite_polarity')

        if digital_composite or digital_separate:
            fields_to_nullify.append('flags_sync_on_rgb')

        cleaned_data = form_nullify_fields(cleaned_data, fields_to_nullify)

        return cleaned_data


class CommentForm(forms.ModelForm):
    class Meta(object):
        model = Comment
        fields = ['EDID', 'parent', 'content']
        widgets = {'EDID': forms.HiddenInput,
                   'parent': forms.HiddenInput}

    def __init__(self, *args, **kwargs):
        # Store EDID object in the form
        self.edid = kwargs['initial'].get('edid')

        self.helper = FormHelper()
        self.helper.form_action = reverse('comment-create',
                                          kwargs={'edid_pk': self.edid.pk})
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            Field('content', rows=3, required=True),
            FormActions(
                Submit('submit', 'Submit'),
            ),
        )
        super(CommentForm, self).__init__(*args, **kwargs)

        self.fields['EDID'].initial = self.edid.pk
        self.fields['parent'].required = False
        self.fields['content'].label = 'Add Comment'

    def clean_parent(self):
        parent = self.cleaned_data['parent']

        if parent:
            if parent.level == parent.get_max_thread_level():
                raise forms.ValidationError('Comment nesting limit exceeded.')

        return parent


class GrabberReleaseUploadForm(BaseForm):
    platforms = {'linux': GrabberRelease.PLATFORM_LINUX,
                 'macosx': GrabberRelease.PLATFORM_MACOSX,
                 'windows': GrabberRelease.PLATFORM_WINDOWS}

    api_key = forms.CharField(widget=forms.PasswordInput)
    platform = forms.CharField()

    class Meta(object):
        model = GrabberRelease
        fields = ['release_file', 'commit']

    def __init__(self, *args, **kwargs):
        super(GrabberReleaseUploadForm, self).__init__(*args, **kwargs)
        self.file_data = None

    def clean_api_key(self):
        api_key = self.cleaned_data['api_key']

        if not hasattr(settings, 'EDID_GRABBER_RELEASE_UPLOAD_API_KEY') \
                or settings.EDID_GRABBER_RELEASE_UPLOAD_API_KEY is None:
            raise forms.ValidationError('This feature is disabled.')

        if not api_key == str(settings.EDID_GRABBER_RELEASE_UPLOAD_API_KEY) \
                .encode('utf-8'):
            raise forms.ValidationError('API key is incorrect.')

        return api_key

    def clean_release_file(self):
        release_file = self.cleaned_data['release_file']

        # TODO: Validate file content based on file name extension

        self.file_data = release_file.read()

        return release_file

    def clean_platform(self):
        platform = self.cleaned_data['platform']

        if platform not in self.platforms.iterkeys():
            raise forms.ValidationError('Platform is incorrect.')

        platform = self.platforms[platform]

        return platform
