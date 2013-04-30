from django.shortcuts import render_to_response
from django.template import RequestContext

from frontend.models import EDID

from edid_parser.edid_parser import EDID_Parser

def index(request):
    edids = EDID.objects.filter()

    return render_to_response('index.html', {'edids': edids}, context_instance=RequestContext(request))

def show_edid(request, edid_id):
    edid = EDID.objects.filter(id=edid_id)

    return render_to_response('show_edid.html', {'edid': edid})

def upload(request):
    edid_file = request.FILES['edid_file'].read()
    edid_data = EDID_Parser(edid_file)
    edid_object = EDID()
    edid_object.populate_from_edid_parser(edid_data.data)

    #We can check for duplicate EDID file here, based on manufacturer_name_id, manufacturer_product_code
    #                                                   and manufacturer_serial_number

    #Saving the entry in DB
    #edid_object.save()

    return render_to_response('index.html', {'edids': [edid_object]})
