from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from frontend.models import EDID
from frontend.forms import UploadEDIDForm

from edid_parser.edid_parser import EDID_Parser

def index(request):
    edids = EDID.objects.filter()

    return render_to_response('index.html', {'edids': edids})

def show_edid(request, edid_id):
    edid = get_object_or_404(EDID, id=edid_id)

    return render_to_response('show_edid.html', {'edid': edid})

def upload_edid(request):
    if request.method == 'POST':
        form = UploadEDIDForm(request.POST, request.FILES)
        if form.is_valid():
            #Read EDID file
            edid_file = request.FILES['edid_file'].read()
            #Parse EDID file
            edid_data = EDID_Parser(edid_file)

            #Create EDID entry
            edid_object = EDID()
            #Add basic data
            edid_object.populate_from_edid_parser(edid_data.data)

            #We can check for duplicate EDID file here, based on manufacturer_name_id, manufacturer_product_code
            #                                                   and manufacturer_serial_number

            #Save the entry
            edid_object.save()
            #Add timings
            edid_object.populate_timings_from_edid_parser(edid_data.data)
            #Save the updated entry
            edid_object.save()

            return HttpResponseRedirect(reverse('show_edid', args=(edid_object.id,)))
    else:
        form = UploadEDIDForm()

    return render_to_response('upload.html', {'form': form}, context_instance=RequestContext(request))
