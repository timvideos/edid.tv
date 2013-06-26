from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView

from frontend.models import EDID
from frontend.forms import EDIDUpdateForm, EDIDUploadForm


#EDID
class EDIDList(ListView):
    model = EDID
    context_object_name = 'edid_list'

class EDIDUpload(FormView):
    form_class = EDIDUploadForm
    template_name = 'frontend/edid_upload.html'

    def form_valid(self, form):
        #Create EDID entry
        edid_object = EDID()
        #Add basic data
        edid_object.populate_from_edid_parser(form.edid_data)

        # We can check for duplicate EDID file here, based on manufacturer_name_id, manufacturer_product_code
        #                                                     and manufacturer_serial_number
        # or probably somewhere else!

        #Save the entry
        edid_object.save()
        #Add timings
        edid_object.populate_timings_from_edid_parser(form.edid_data)
        #Save the updated entry
        edid_object.save()

        return HttpResponseRedirect(reverse('edid-detail', kwargs={'pk': edid_object.pk}))

class EDIDDetailView(DetailView):
    queryset = EDID.public.all()

class EDIDUpdate(UpdateView):
    model = EDID
    form_class = EDIDUpdateForm
