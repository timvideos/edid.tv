from django.db.models import Count
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.edit import (FormView, CreateView, UpdateView,
                                       DeleteView)

from braces.views import (LoginRequiredMixin, PrefetchRelatedMixin,
                          StaffuserRequiredMixin)
import reversion

from frontend.models import Manufacturer, EDID, StandardTiming, DetailedTiming
from frontend.forms import (EDIDUpdateForm, EDIDUploadForm,
                            StandardTimingForm, DetailedTimingForm)


### Manufacturer
class ManufacturerList(ListView):
    model = Manufacturer
    context_object_name = 'manufacturer_list'
    paginate_by = 20

    def get_queryset(self):
        queryset = super(ManufacturerList, self).get_queryset()

        # Add count of EDIDs to items
        queryset = queryset.annotate(Count('edid'))

        # Filter items with EDID count > 0 only
        queryset = queryset.filter(edid__count__gt=0)

        return queryset


class ManufacturerDetail(DetailView):
    model = Manufacturer

    def get_context_data(self, **kwargs):
        """
        Retrieves list of related EDIDs and annotates their timings count.

        Adds `edid_list` to template context to be used in place of
        `manufacturer.edid_set` RelatedManager.
        """

        context = super(ManufacturerDetail, self).get_context_data(**kwargs)

        queryset = EDID.objects.filter(manufacturer=context['manufacturer'].pk)

        # Add count of timings to EDIDs
        queryset = queryset.annotate(Count('standardtiming', distinct=True))
        queryset = queryset.annotate(Count('detailedtiming', distinct=True))

        context['edid_list'] = queryset

        return context


### EDID
class EDIDList(ListView):
    model = EDID
    context_object_name = 'edid_list'


class EDIDUpload(FormView):
    form_class = EDIDUploadForm
    template_name = 'frontend/edid_upload.html'

    def form_valid(self, form):
        # Create EDID entry
        edid_object = EDID()

        edid_object.checksum = form.edid_checksum

        # Set the user
        if self.request.user.is_authenticated():
            edid_object.user = self.request.user

        # Add basic data
        edid_object.populate_from_edid_parser(form.edid_data)

        # Save the binary file
        edid_object.file.save('edid.bin', ContentFile(form.edid_binary))

        # Save the entry
        edid_object.save()
        # Add timings
        edid_object.populate_timings_from_edid_parser(form.edid_data)
        # Save the updated entry
        edid_object.save()

        return HttpResponseRedirect(reverse('edid-detail',
                                            kwargs={'pk': edid_object.pk}))


class EDIDDetailView(PrefetchRelatedMixin, DetailView):
    model = EDID
    prefetch_related = ['standardtiming_set', 'detailedtiming_set']

    def get_object(self, queryset=None):
        """
        Injects timings sets as attributes to EDID object.

        See EDIDRevisionDetail for details.
        """

        object = super(EDIDDetailView, self).get_object(queryset)

        object.standardtimings = object.standardtiming_set.all()
        object.detailedtimings = object.detailedtiming_set.all()

        return object


class EDIDUpdate(LoginRequiredMixin, PrefetchRelatedMixin, UpdateView):
    model = EDID
    form_class = EDIDUpdateForm
    prefetch_related = ['standardtiming_set', 'detailedtiming_set']

    def form_valid(self, form):
        """
        Set the user.
        """

        form.instance.user = self.request.user

        return super(EDIDUpdate, self).form_valid(form)


### EDID Revisions
class EDIDRevisionList(ListView):
    context_object_name = 'versions_list'
    template_name = 'frontend/edid_revision_list.html'

    def get_queryset(self):
        """
        Returns versions list queryset based on edid_pk.
        """

        edid_pk = self.kwargs.get('edid_pk', None)

        edid = get_object_or_404(EDID, pk=edid_pk)
        versions_list = reversion.get_for_object(edid)

        return versions_list

    def get_context_data(self, **kwargs):
        """
        Injects edid_pk into template context.
        """

        context = super(EDIDRevisionList, self).get_context_data(**kwargs)
        context['edid_pk'] = self.kwargs['edid_pk']

        return context


class EDIDRevisionDetail(DetailView):
    template_name = 'frontend/edid_detail.html'

    def get_object(self, queryset=None):
        """
        Returns EDID versioned instance based on edid_pk and revision_pk.
        Injects timings sets as attributes to EDID object.

        We can't use RelaltedManager to get versioned timings, instead we store
        timings in EDID object attributes.
        """

        edid_pk = self.kwargs.get('edid_pk', None)
        revision_pk = self.kwargs.get('revision_pk', None)

        # Get version based on edid_pk and revision_pk or return 404.
        version = reversion.get_for_object_reference(EDID, edid_pk) \
                           .filter(revision__pk=revision_pk)

        try:
            version = version.get()
        except version.model.DoesNotExist:
            raise Http404('No revision were found.')

        # Assign EDID instance to edid
        edid =  version.object_version.object

        # Flag EDID instance as revision
        edid.is_revision = True

        # Get set of all versions (objects) in the revision
        revision_versions = version.revision.version_set.all()

        # Split timings by type
        standardtimings = []
        detailedtimings = []

        for related_version in revision_versions:
            if isinstance(related_version.object_version.object,
                          StandardTiming):
                standardtimings.append(related_version.object_version.object)
            elif isinstance(related_version.object_version.object,
                            DetailedTiming):
                detailedtimings.append(related_version.object_version.object)

        edid.standardtimings = standardtimings
        edid.detailedtimings = detailedtimings

        # Return EDID instance
        return edid


class EDIDRevisionRevert(LoginRequiredMixin, StaffuserRequiredMixin,
                         DeleteView):
    """
    Provides reverting a revision.
    """

    template_name = 'frontend/edid_revision_revert.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        revision = self.kwargs.get('revision')

        revision.revert()

        return HttpResponseRedirect(self.get_success_url())

    def get_object(self, queryset=None):
        """
        Returns revision based on edid_pk and revision_pk.
        """

        edid_pk = self.kwargs.get('edid_pk', None)
        revision_pk = self.kwargs.get('revision_pk', None)

        # Get version based on edid_pk and revision_pk or return 404.
        version = reversion.get_for_object_reference(EDID, edid_pk) \
                           .filter(revision__pk=revision_pk)

        try:
            version = version.get()
        except version.model.DoesNotExist:
            raise Http404('No revision were found.')

        self.kwargs['revision'] = version.revision

        # Return EDID instance
        return version.object_version.object

    def get_context_data(self, **kwargs):
        context = super(EDIDRevisionRevert, self).get_context_data(**kwargs)

        context['revision'] = self.kwargs.get('revision')

        return context

    def get_success_url(self):
        edid_pk = self.kwargs.get('edid_pk')

        return reverse('edid-detail', kwargs={'pk': edid_pk})


### Timing Mixin
class TimingMixin(object):
    context_object_name = 'timing'

    def get_initial(self):
        """
        Uses edid_pk argument from URLConf to grab EDID object and inject it
        in the view.

        Used for CreateView and UpdateView.
        """

        initial = super(TimingMixin, self).get_initial()

        edid_pk = self.kwargs.get('edid_pk', None)

        edid = get_object_or_404(EDID, pk=edid_pk)
        initial.update({'edid': edid})

        return initial

    def get_object(self, queryset=None):
        """
        Gets timing object based on edid_pk and identification.

        Used for UpdateView and DeleteView.
        """

        queryset = self.get_queryset()

        edid_pk = self.kwargs.get('edid_pk', None)
        identification = self.kwargs.get('identification', None)

        obj = get_object_or_404(queryset, EDID=edid_pk,
                                identification=identification)

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
                count = self.model.objects.filter(EDID=form.instance.EDID)\
                                          .count()
                # Set identification to count + 1
                form.instance.identification = count + 1

        # Set the user
        form.instance.user = self.request.user

        return super(TimingMixin, self).form_valid(form)

    def delete(self, request, *args, **kwargs):
        """
        Deletes the timing and reorder the subsequent timings and then
        redirects to the success URL.

        Used for DeleteView.
        """

        self.object = self.get_object()
        self.object.delete()

        timings = self.model.objects.filter(EDID=self.object.EDID,
                      identification__gt=self.object.identification).all()

        for timing in timings:
            timing.identification = timing.identification - 1
            timing.save()

        return HttpResponseRedirect(self.get_success_url())


### Standard Timing
class StandardTimingCreate(LoginRequiredMixin, TimingMixin, CreateView):
    model = StandardTiming
    form_class = StandardTimingForm


class StandardTimingUpdate(LoginRequiredMixin, TimingMixin, UpdateView):
    model = StandardTiming
    form_class = StandardTimingForm


class StandardTimingDelete(LoginRequiredMixin, TimingMixin, DeleteView):
    model = StandardTiming


### Detailed Timing
class DetailedTimingCreate(LoginRequiredMixin, TimingMixin, CreateView):
    model = DetailedTiming
    form_class = DetailedTimingForm


class DetailedTimingUpdate(LoginRequiredMixin, TimingMixin, UpdateView):
    model = DetailedTiming
    form_class = DetailedTimingForm


class DetailedTimingDelete(LoginRequiredMixin, TimingMixin, DeleteView):
    model = DetailedTiming


### Timing Reorder Mixin
class TimingReorderMixin(object):
    http_method_names = [u'get']

    def get(self, request, *args, **kwargs):
        edid_pk = kwargs.get('edid_pk', None)
        identification = int(kwargs.get('identification', None))
        direction = kwargs.get('direction', None)

        if direction == 'up':
            if identification == 1:
                return HttpResponseForbidden('You can not move up a timing if'
                                             ' its identification is 1.')

            prev_timing = self.model.objects.get(EDID_id=edid_pk,
                              identification=identification - 1)
            current_timing = self.model.objects.get(EDID_id=edid_pk,
                                 identification=identification)

            prev_timing.identification += 1
            prev_timing.user = request.user
            prev_timing.save()

            current_timing.identification -= 1
            current_timing.user = request.user
            current_timing.save()

            return HttpResponseRedirect(self.get_success_url())
        elif direction == 'down':
            count = self.model.objects.filter(EDID_id=edid_pk).count()

            if identification == count:
                return HttpResponseForbidden('You can not move down a timing'
                                             ' if it is the last one.')

            current_timing = self.model.objects.get(EDID_id=edid_pk,
                                 identification=identification)
            next_timing = self.model.objects.get(EDID_id=edid_pk,
                              identification=identification + 1)

            next_timing.identification -= 1
            next_timing.user = request.user
            next_timing.save()

            current_timing.identification += 1
            current_timing.user = request.user
            current_timing.save()

            return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """
        Returns url of EDID updating page.
        """

        edid_pk = self.kwargs.get('edid_pk')

        return reverse('edid-update', kwargs={'pk': edid_pk})


### Standard Timing
class StandardTimingReorder(LoginRequiredMixin, TimingReorderMixin, View):
    model = StandardTiming


### Detailed Timing
class DetailedTimingReorder(LoginRequiredMixin, TimingReorderMixin, View):
    model = DetailedTiming


### User Profile
class ProfileView(TemplateView):
    template_name = 'account/profile.html'
