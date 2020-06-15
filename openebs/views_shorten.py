import logging
from braces.views import LoginRequiredMixin
from datetime import timedelta, datetime, date
from django.urls import reverse_lazy
from django.db.models import Q, F, Count
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, DeleteView, DetailView, TemplateView
from kv1.models import Kv1Journey, Kv1Line, Kv1Stop
from openebs.form_kv17 import Kv17ChangeForm, Kv17ShortenForm
from openebs.models import Kv17Change, Kv17Shorten, Kv1StopFilter
from openebs.views_push import Kv17PushMixin
from openebs.views_utils import FilterDataownerMixin
from utils.time import get_operator_date, get_operator_date_aware
from utils.views import AccessMixin, ExternalMessagePushMixin, JSONListResponseMixin
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from djgeojson.views import GeoJSONLayerView
from django.contrib.gis.db.models import Extent



log = logging.getLogger('openebs.views.changes')


class ShortenCreateView(AccessMixin, Kv17PushMixin, CreateView):
    permission_required = 'openebs.add_shorten'
    model = Kv17Shorten
    form_class = Kv17ShortenForm
    success_url = reverse_lazy('change_index')

    def get_context_data(self, **kwargs):
        data = super(ShortenCreateView, self).get_context_data(**kwargs)
        data['operator_date'] = get_operator_date()
        if 'journey' in self.request.GET:
            self.add_journeys_from_request(data)
        return data

    def add_journeys_from_request(self, data):
        journey_errors = 0
        journeys = []

        for journeynumber in self.request.GET['journey'].split(','):
            if journeynumber == "":
                continue
            log.info("Finding journey %s for '%s'" % (journeynumber, self.request.user))
            j = Kv1Journey.find_from_realtime(self.request.user.userprofile.company, journeynumber)
            if j:
                journeynumber.append(j)
            else:
                journey_errors += 1
                log.error("User '%s' (%s) failed to find journey '%s' " % (
                self.request.user, self.request.user.userprofile.company, journeynumber))
        data['journeys'] = journeys
        if journey_errors > 0:
            data['journey_errors'] = journey_errors

    def form_invalid(self, form):
        log.error("Form for KV17 shorten invalid!")
        print(form.errors)
        return super(ShortenCreateView, self).form_invalid(form)

    def form_valid(self, form):
        form.instance.dataownercode = self.request.user.userprofile.company

        # TODO this is a bad solution - totally gets rid of any benefit of Django's CBV and Forms
        xml = form.save()

        if len(xml) == 0:
            log.error("Tried to communicate KV17 empty line change, rejecting")
            # This is kinda weird, but shouldn't happen, everything has validation
            return HttpResponseRedirect(self.success_url)

        """
        haltes = self.request.POST.get('haltes', None)
        stops = []
        if haltes:
            stops = Kv1Stop.find_stops_from_haltes(haltes)

        # Save and then log
        #ret = super(ShortenCreateView, self).form_valid(form)

        # Add stop data
        for stop in stops:
            form.instance.kv17shorten.create(change=form.instance, stop=stop)
        #Kv15Log.create_log_entry(form.instance, get_client_ip(self.request))
        """
        # Push message to GOVI
        if self.push_message(xml):
            log.info("Sent KV17 line change to subscribers: %s" % self.request.POST.get('journeys', "<unknown>"))
        else:
            log.error("Failed to communicate KV17 line change to subscribers")

        # Another hack to redirect correctly
        return HttpResponseRedirect(self.success_url)


class ShortenDeleteView(AccessMixin, Kv17PushMixin, FilterDataownerMixin, DeleteView):
    permission_required = 'openebs.add_shorten'
    model = Kv17Shorten
    success_url = reverse_lazy('change_index')


class ShortenUpdateView(AccessMixin, Kv17PushMixin, FilterDataownerMixin, DeleteView):
    """ This is a really weird view - it's redoing a change that you deleted   """
    permission_required = 'openebs.add_shorten'
    model = Kv17Shorten
    success_url = reverse_lazy('change_index')


class ShortenDetailsView(AccessMixin, FilterDataownerMixin, DetailView):
    permission_required = 'openebs.view_shorten'
    permission_level = 'read'
    model = Kv17Change
    template_name = 'openebs/kv17shorten_detail.html'


class ShortenStopsAjaxView(LoginRequiredMixin, GeoJSONLayerView):
    model = Kv1Stop
    geometry_field = 'location'
    properties = ['name', 'userstopcode', 'dataownercode']

    def get_queryset(self):
        qry = super(ShortenStopsAjaxView, self).get_queryset()
        qry = qry.filter(stop_shorten__change_id=self.kwargs.get('pk', None))

        if not (self.request.user.has_perm("openebs.view_shorten") or self.request.user.has_perm("openebs.add_shorten")):
            qry = qry.filter(kv17change__dataownercode=self.request.user.userprofile.company)

        return qry


class ShortenStopsBoundAjaxView(LoginRequiredMixin, JSONListResponseMixin, DetailView):
    model = Kv1Stop
    render_object = 'object'

    def get_object(self, **kwargs):
        qry = self.get_queryset()
        return {'extent': qry.aggregate(Extent('location')).get('location__extent')}

    def get_queryset(self):
        qry = super(ShortenStopsBoundAjaxView, self).get_queryset()
        pk = self.request.GET.get('id', None)
        pk_2 = self.kwargs.get('id', None)
        qry = qry.filter(stop_shorten__change_id=pk)

        if not (self.request.user.has_perm("openebs.view_all") or self.request.user.has_perm("openebs.edit_all")):
            qry = qry.filter(dataownercode=self.request.user.userprofile.company)

        return qry


class ActiveShortenStopListView(LoginRequiredMixin, GeoJSONLayerView):
    """
    Show stops with active messages on the map, creates GeoJSON
    """
    model = Kv1Stop
    geometry_field = 'location'
    properties = ['id', 'name', 'userstopcode', 'dataownercode', 'timingpointcode']

    def get_queryset(self):
        today = date.today()
        qry = self.model.objects.filter(stop_shorten__change__operatingday__gte=today)

        if not self.request.user.has_perm("openebs.view_all"):
            qry = qry.filter(dataownercode=self.request.user.userprofile.company)
        return qry


class ActiveShortenForStopView(LoginRequiredMixin, JSONListResponseMixin, DetailView):
    """
    Show active messages on an active stop on the map, creates JSON
    """
    model = Kv1Stop
    render_object = 'object'

    def get_queryset(self):
        tpc = self.kwargs.get('tpc', None)
        if tpc is None or tpc == '0':
            return None
        qry = self.model.objects.filter(messages__stopmessage__messagestarttime__lte=now(),
                                        messages__stopmessage__messageendtime__gte=now(),
                                        messages__stopmessage__isdeleted=False,
                                        timingpointcode=tpc).distinct('kv15stopmessage__id')
        if not self.request.user.has_perm("openebs.view_all"):
            qry = qry.filter(dataownercode=self.request.user.userprofile.company)
        return qry.values('id', 'dataownercode', 'kv15stopmessage__dataownercode',
                          'kv15stopmessage__messagecodenumber',
                          'kv15stopmessage__messagecontent', 'kv15stopmessage__id')

    def get_object(self):
        return list(self.get_queryset())