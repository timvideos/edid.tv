import base64
import json

from django.db.models import Count
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.edit import (FormView, CreateView, UpdateView,
                                       DeleteView)

from braces.views import (CsrfExemptMixin, JSONResponseMixin,
                          LoginRequiredMixin, PrefetchRelatedMixin,
                          StaffuserRequiredMixin)
import reversion

from edid_parser.edid_parser import EDID_Parser, EDIDParsingError

from frontend.models import (Manufacturer, EDID, StandardTiming,
                             DetailedTiming, Comment)
from frontend.forms import (EDIDTextUploadForm, EDIDUpdateForm, EDIDUploadForm,
                            StandardTimingForm, DetailedTimingForm,
                            CommentForm)


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
        queryset = queryset.annotate(Count('standardtiming', distinct=True)) \
                           .annotate(Count('detailedtiming', distinct=True))

        context['edid_list'] = queryset

        return context


### EDID
class EDIDList(ListView):
    model = EDID

    def get_context_data(self, **kwargs):
        """
        Retrieves list of EDIDs and annotates their timings count.

        Adds `edid_list` to template context.
        """

        context = super(EDIDList, self).get_context_data(**kwargs)

        queryset = self.get_queryset()

        # Add count of timings to EDIDs
        queryset = queryset.annotate(Count('standardtiming', distinct=True)) \
                           .annotate(Count('detailedtiming', distinct=True))

        context['edid_list'] = queryset

        return context

    def get_queryset(self):
        queryset = super(EDIDList, self).get_queryset()

        queryset = queryset.order_by('-created')[:10]

        return queryset


class EDIDBinaryUpload(FormView):
    form_class = EDIDUploadForm
    template_name = 'frontend/edid_upload_binary.html'

    def form_valid(self, form):
        # Create EDID entry
        edid_object = EDID.create(file_base64=form.edid_base64,
                                  edid_data=form.edid_data)

        # Set the user
        if self.request.user.is_authenticated():
            edid_object.user = self.request.user

        # Save the entry
        edid_object.save()
        # Add timings
        edid_object.populate_timings_from_edid_parser(form.edid_data)
        # Save the updated entry
        edid_object.save()

        # Set revision comment
        reversion.set_comment('EDID parsed.')

        return HttpResponseRedirect(reverse('edid-detail',
                                            kwargs={'pk': edid_object.pk}))


class EDIDTextUpload(FormView):
    form_class = EDIDTextUploadForm
    template_name = 'frontend/edid_upload_text.html'

    def __init__(self):
        super(EDIDTextUpload, self).__init__()

        self.succeeded = 0
        self.failed = 0
        self.duplicate = 0
        self.edid_list = []

    def form_valid(self, form):
        for edid_bytes in form.edid_list:
            self._process_edid(edid_bytes)

        return self.render_to_response(self.get_context_data(
            form=form,
            valid=True,
            succeeded=self.succeeded,
            failed=self.failed,
            duplicate=self.duplicate,
            edid_list=self.edid_list
        ))

    def _process_edid(self, edid_bytes):
        # Encode in base64
        edid_base64 = base64.b64encode(edid_bytes)

        if EDID.objects.filter(file_base64=edid_base64).exists():
            self.duplicate += 1
        else:
            # Parse EDID file and add it
            try:
                edid_data = EDID_Parser(edid_bytes).data
                self._create_edid(edid_base64, edid_data)
                self.succeeded += 1
            except EDIDParsingError:
                self.failed += 1

    def _create_edid(self, edid_base64, edid_data):
        # Override RevisionMiddleware
        # RevisionMiddleware creates a revision per request,
        # we want a revision per EDID object created
        with reversion.create_revision(manage_manually=True):
            # Create EDID entry
            edid_object = EDID.create(file_base64=edid_base64,
                                      edid_data=edid_data)
            # Save the entry
            edid_object.save()

            # Add timings
            edid_object.populate_timings_from_edid_parser(edid_data)
            # Save the updated entry
            edid_object.save()

            # Set revision comment
            reversion.set_comment('EDID parsed.')
            # Create revision for EDID
            reversion.default_revision_manager.save_revision([edid_object])

            self.edid_list.append(edid_object)


class EDIDDetailView(PrefetchRelatedMixin, DetailView):
    model = EDID
    prefetch_related = ['standardtiming_set', 'detailedtiming_set',
                        'comment_set']

    def get_object(self, queryset=None):
        """
        Injects timings sets as attributes to EDID object.

        See EDIDRevisionDetail for details.
        """

        object = super(EDIDDetailView, self).get_object(queryset)

        object.standardtimings = object.standardtiming_set.all()
        object.detailedtimings = object.detailedtiming_set.all()

        return object

    def get_context_data(self, **kwargs):
        """
        Inject comment form in context.
        """
        context = super(EDIDDetailView, self).get_context_data(**kwargs)

        context['comments'] = self.object.get_comments()
        context['comment_form'] = CommentForm(initial={'edid': self.object})

        return context


class EDIDUpdate(LoginRequiredMixin, PrefetchRelatedMixin, UpdateView):
    model = EDID
    form_class = EDIDUpdateForm
    prefetch_related = ['standardtiming_set', 'detailedtiming_set']

    def form_valid(self, form):
        """
        Set the user.
        """

        form.instance.user = self.request.user

        # Set revision comment
        # TODO: Include updated fields list
        reversion.set_comment('Updated EDID.')

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
            raise Http404()

        # Assign EDID instance to edid
        edid = version.object_version.object

        # Flag EDID instance as revision
        edid.is_revision = True

        # Get set of all versions (related objects) in the revision
        revision_versions = version.revision.version_set.all()

        # Split timings by type
        standardtimings = []
        detailedtimings = []

        for related_version in revision_versions:
            timing = related_version.object_version.object
            if isinstance(timing, StandardTiming):
                standardtimings.append(timing)
            elif isinstance(timing, DetailedTiming):
                detailedtimings.append(timing)

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

        # Revert the revision, delete new timings not included in the revision
        revision.revert(delete=True)

        # Set revision comment
        reversion.set_comment('Reverted to revision %s' % revision.pk)

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
            raise Http404()

        # Check revision and EDID date
        # FIXME: Works fine, but tests fail due to milliseconds difference
        if version.revision.date_created == version.object.modified:
            return HttpResponseBadRequest(
                'You can not revert to the current revision.'
            )

        self.kwargs['revision'] = version.revision

        # Return EDID instance
        return version.object

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
        in form initial data.

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

        # For CreateView, set EDID
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

        # Set revision comment
        if isinstance(self, CreateView):
            comment = 'Created %s %s.'
        elif isinstance(self, UpdateView):
            comment = 'Updated %s %s.'

        reversion.set_comment(comment % (
            form.instance._meta.verbose_name, form.instance
        ))

        return super(TimingMixin, self).form_valid(form)

    def delete(self, request, *args, **kwargs):
        """
        Deletes the timing and then redirects to the success URL.

        Used for DeleteView.
        """

        self.object = self.get_object()
        self.object.delete()

        # Did not actually update EDID, just to make sure EDID and all its
        # related objects are included in the revision
        self.object.EDID.save()

        # Set revision comment
        reversion.set_comment('Deleted %s %s.' % (
            self.object._meta.verbose_name, self.object
        ))

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
                return HttpResponseBadRequest(
                    'You can not move up a timing if it is the first one.'
                )

            prev_timing = self.model.objects.get(
                EDID_id=edid_pk, identification=identification - 1
            )
            current_timing = self.model.objects.get(
                EDID_id=edid_pk, identification=identification
            )

            prev_timing.identification += 1
            prev_timing.user = request.user
            prev_timing.save()

            current_timing.identification -= 1
            current_timing.user = request.user
            current_timing.save()

            # Set revision comment
            reversion.set_comment('Moved %s %s up.' % (
                current_timing._meta.verbose_name, current_timing
            ))

            return HttpResponseRedirect(self.get_success_url())
        elif direction == 'down':
            count = self.model.objects.filter(EDID_id=edid_pk).count()

            if identification == count:
                return HttpResponseBadRequest(
                    'You can not move down a timing if it is the last one.'
                )

            current_timing = self.model.objects.get(
                EDID_id=edid_pk, identification=identification
            )
            next_timing = self.model.objects.get(
                EDID_id=edid_pk, identification=identification + 1
            )

            next_timing.identification -= 1
            next_timing.user = request.user
            next_timing.save()

            current_timing.identification += 1
            current_timing.user = request.user
            current_timing.save()

            # Set revision comment
            reversion.set_comment('Moved %s %s down.' % (
                current_timing._meta.verbose_name, current_timing
            ))

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


### Comment
class CommentCreate(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    http_method_names = [u'post']

    def get_initial(self):
        """
        Uses edid_pk argument from URLConf to grab EDID object and inject it
        in form initial data.
        """

        initial = super(CommentCreate, self).get_initial()

        edid_pk = self.kwargs.get('edid_pk', None)

        edid = get_object_or_404(EDID, pk=edid_pk)
        initial.update({'edid': edid})

        return initial

    def get_context_data(self, **kwargs):
        """
        Uses edid_pk argument from URLConf to grab EDID object and inject it
        in template context.
        """

        context = super(CommentCreate, self).get_context_data(**kwargs)

        edid_pk = self.kwargs.get('edid_pk', None)

        edid = get_object_or_404(EDID, pk=edid_pk)
        context.update({'edid': edid, 'comments': edid.get_comments()})

        return context

    def get_success_url(self):
        """
        Returns url of EDID detail page.
        """

        edid_pk = self.kwargs.get('edid_pk')

        return reverse('edid-detail', kwargs={'pk': edid_pk})

    def form_valid(self, form):
        """
        Sets EDID, parent and user.
        """

        # Set EDID
        form.instance.EDID = form.EDID

        # Set user
        form.instance.user = self.request.user

        # Set nesting level
        if form.instance.parent:
            form.instance.level = form.instance.parent.level + 1
        else:
            form.instance.level = 0

        return super(CommentCreate, self).form_valid(form)


### API Upload
# TODO: Use braces.JsonRequestResponseMixin when it's released
class APIUpload(CsrfExemptMixin, JSONResponseMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        content = json.loads(request.body)

        if not 'edid_list' in content:
            return HttpResponseBadRequest(
                json.dumps({'error_message': 'List of EDIDs is missing.'})
            )

        self.succeeded = 0
        self.failed = 0

        for edid_base64 in content['edid_list']:
            self._process_edid(edid_base64)

        return self.render_json_response({'succeeded': self.succeeded,
                                          'failed': self.failed})

    def _process_edid(self, edid_base64):
        if EDID.objects.filter(file_base64=edid_base64).exists():
            self.failed += 1
        else:
            edid_binary = base64.b64decode(edid_base64)

            # Parse EDID file
            try:
                edid_data = EDID_Parser(edid_binary).data
                self._create_edid(edid_base64, edid_data)
                self.succeeded += 1
            except EDIDParsingError:
                self.failed += 1

    def _create_edid(self, edid_base64, edid_data):
        # Override RevisionMiddleware
        # RevisionMiddleware creates a revision per request,
        # we want a revision per EDID object created
        with reversion.create_revision(manage_manually=True):
            # Create EDID entry
            edid_object = EDID.create(file_base64=edid_base64,
                                      edid_data=edid_data)
            # Save the entry
            edid_object.save()

            # Add timings
            edid_object.populate_timings_from_edid_parser(edid_data)
            # Save the updated entry
            edid_object.save()

            # Set revision comment
            reversion.set_comment('EDID parsed.')
            # Create revision for EDID
            reversion.default_revision_manager.save_revision([edid_object])


class APITextUpload(CsrfExemptMixin, JSONResponseMixin, EDIDTextUpload):
    """
    Based on EDIDTextUpload, disables CSRF and returns JSON output.
    """

    http_method_names = ['post']

    def form_valid(self, form):
        for edid_bytes in form.edid_list:
            self._process_edid(edid_bytes)

        return self.render_json_response({'succeeded': self.succeeded,
                                          'failed': self.failed,
                                          'duplicate': self.duplicate})

    def form_invalid(self, form):
        return self.render_json_response({'error': 'Submittion failed!'})


### User Profile
class ProfileView(TemplateView):
    template_name = 'account/profile.html'
