from django import forms

class UploadEDIDForm(forms.Form):
    edid_file = forms.FileField(label='EDID File')
