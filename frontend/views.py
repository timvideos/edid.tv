from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView

from frontend.models import EDID, StandardTiming, DetailedTiming
from frontend.forms import EDIDUpdateForm, EDIDUploadForm, StandardTimingForm, DetailedTimingForm


### EDID
class EDIDList(ListView):
    queryset = EDID.public.all()
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
    queryset = EDID.public.all()
    form_class = EDIDUpdateForm


### Standard Timing
class StandardTimingCreate(CreateView):
    model = StandardTiming
    form_class = StandardTimingForm

class StandardTimingUpdate(UpdateView):
    model = StandardTiming
    form_class = StandardTimingForm

    def get_success_url(self):
        # Returns url of EDID updating page
        return reverse('edid-update', kwargs={'pk': self.object.EDID.pk})

class StandardTimingDelete(DeleteView):
    model = StandardTiming
    form_class = StandardTimingForm
#    success_url = reverse_lazy('edid-update')


### Detailed Timing
class DetailedTimingCreate(CreateView):
    model = DetailedTiming
    form_class = DetailedTimingForm

class DetailedTimingUpdate(UpdateView):
    model = DetailedTiming
    form_class = DetailedTimingForm

    def get_success_url(self):
        # Returns url of EDID updating page
        return reverse('edid-update', kwargs={'pk': self.object.EDID.pk})

class DetailedTimingDelete(DeleteView):
    model = DetailedTiming
    form_class = DetailedTimingForm
#    success_url = reverse_lazy('edid-update')
