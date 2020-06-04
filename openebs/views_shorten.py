import logging
from braces.views import LoginRequiredMixin
from datetime import timedelta, datetime
from django.urls import reverse_lazy
from django.db.models import Q, F
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, DeleteView, DetailView
from kv1.models import Kv1Journey, Kv1Line
from openebs.form_kv17 import Kv17ChangeForm, Kv17ShortenForm
from openebs.models import Kv17Change
from openebs.views_push import Kv17PushMixin
from openebs.views_utils import FilterDataownerMixin
from utils.time import get_operator_date, get_operator_date_aware
from utils.views import AccessMixin, ExternalMessagePushMixin, JSONListResponseMixin
from django.utils.dateparse import parse_date
from django.utils.timezone import now

log = logging.getLogger('openebs.views.changes')


class ShortenListView(AccessMixin, ListView):
    permission_required = 'openebs.view_shorten'
    model = Kv17Change


class ShortenCreateView(AccessMixin, Kv17PushMixin, CreateView):
    permission_required = 'openebs.add_shorten'
    model = Kv17Change
    form_class = Kv17ShortenForm
    success_url = reverse_lazy('shorten_index')

    def get_context_data(self, **kwargs):
        data = super(ShortenCreateView, self).get_context_data(**kwargs)
        data['operator_date'] = get_operator_date()
        if 'journey' in self.request.GET:
            self.add_journeys_from_request(data)
        return data

    def add_journeys_from_request(self, data):
        journey_errors = 0
        journeys = []

        for journey in self.request.GET['journey'].split(','):
            if journey == "":
                continue
            log.info("Finding journey %s for '%s'" % (journey, self.request.user))
            j = Kv1Journey.find_from_realtime(self.request.user.userprofile.company, journey)
            if j:
                journeys.append(j)
            else:
                journey_errors += 1
                log.error("User '%s' (%s) failed to find journey '%s' " % (self.request.user, self.request.user.userprofile.company, journey))
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

        if len(self.xml) == 0:
            log.error("Tried to communicate KV17 empty line change, rejecting")
            # This is kinda weird, but shouldn't happen, everything has validation
            return HttpResponseRedirect(self.success_url)

        # Push message to GOVI
        if self.push_message(xml):
            log.info("Sent KV17 line change to subscribers: %s" % self.request.POST.get('journeys', "<unknown>"))
        else:
            log.error("Failed to communicate KV17 line change to subscribers")

        # Another hack to redirect correctly
        return HttpResponseRedirect(self.success_url)


class ShortenDeleteView(AccessMixin, Kv17PushMixin, FilterDataownerMixin, DeleteView):
    permission_required = 'openebs.add_shorten'
    model = Kv17Change
    success_url = reverse_lazy('shorten_index')


class ShortenUpdateView(AccessMixin, Kv17PushMixin, FilterDataownerMixin, DeleteView):
    """ This is a really weird view - it's redoing a change that you deleted   """
    permission_required = 'openebs.add_shorten'
    model = Kv17Change
    success_url = reverse_lazy('shorten_index')
