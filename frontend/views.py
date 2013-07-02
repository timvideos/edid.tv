from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
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


### Timing Mixin
class TimingMixin(object):
    context_object_name = 'timing'

    def get_object(self, queryset=None):
        """
        Gets timing object based on edid_pk and identification.

        Used for UpdateView and DeleteView.
        """

        queryset = self.get_queryset()

        edid_pk = self.kwargs.get('edid_pk', None)
        identification = self.kwargs.get('identification', None)

        obj = get_object_or_404(queryset, EDID=edid_pk, identification=identification)

        return obj

    def get_success_url(self):
        """
        Returns url of EDID updating page.

        Used for CreateView, UpdateView and DeleteView.
        """

        edid_pk = self.kwargs.get('edid_pk')

        return reverse('edid-update', kwargs={'pk': edid_pk})

    def form_valid(self, form):
        """
        Sets EDID and identification when creating new timing.

        Used for CreateView and UpdateView.
        """

        if not form.instance.EDID_id:
            form.instance.EDID = form.EDID
            if not form.instance.identification:
                # Get count of available timings
                count = self.model.objects.filter(EDID=form.instance.EDID).count()
                # Set identification to count + 1
                form.instance.identification = count + 1

        return super(TimingMixin, self).form_valid(form)


### Standard Timing
class StandardTimingCreate(TimingMixin, CreateView):
    model = StandardTiming
    form_class = StandardTimingForm

class StandardTimingUpdate(TimingMixin, UpdateView):
    model = StandardTiming
    form_class = StandardTimingForm

class StandardTimingDelete(TimingMixin, DeleteView):
    model = StandardTiming


### Detailed Timing
class DetailedTimingCreate(TimingMixin, CreateView):
    model = DetailedTiming
    form_class = DetailedTimingForm

class DetailedTimingUpdate(TimingMixin, UpdateView):
    model = DetailedTiming
    form_class = DetailedTimingForm

class DetailedTimingDelete(TimingMixin, DeleteView):
    model = DetailedTiming
