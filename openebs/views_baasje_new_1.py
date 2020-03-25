import logging
from braces.views import LoginRequiredMixin
import datetime #import timedelta, datetime
from django.shortcuts import render
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, DeleteView, DetailView
from kv1.models import Kv1Journey, Kv1Line
from openebs.form import Kv17ChangeForm, ChangeLineCancelCreateForm#, Kv17ChangeLineForm
from openebs.models import Kv17Change, Kv17ChangeLine

from openebs.views_push import Kv17PushMixin
from openebs.views_utils import FilterDataownerMixin
from utils.time import get_operator_date
from utils.views import AccessMixin, ExternalMessagePushMixin, JSONListResponseMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from kv1.models import Kv1JourneyDate
from kv1.views import DataImportView

log = logging.getLogger('openebs.views.changes')


class ChangeLineCancelCreateView(AccessMixin, Kv17PushMixin, CreateView):
    permission_required = 'openebs.add_change'
    model = Kv17ChangeLine
    form_class = ChangeLineCancelCreateForm
    #template_name = 'openebs/kv17change_form_baasje.html'
    template_name = 'openebs/kv17change_form_baasje_dropdown.html'
    success_url = reverse_lazy('change_line_index')

    def get_context_data(self, **kwargs):
        data = super(ChangeLineCancelCreateView, self).get_context_data(**kwargs)
        today = get_operator_date()

        self.get_lines(data)
        #self.get_lines_from_request(data)
        return data


    def get_lines(self, data):
        lines = []
        lines = Kv1Line.objects.all() \
            .filter(dataownercode=self.request.user.userprofile.company) \
            .values('publiclinenumber','headsign', 'dataownercode') \
            .order_by('publiclinenumber')
        data['header'] = ['Lijn', 'Eindbestemming']
        data['lines'] = lines


    def get_lines_from_request(self, data):
        data = super(ChangeLineCancelCreateView, self).get_context_data(**kwargs)

        print("get lines from request")
        #search_fields = ('publiclinenumber')
        line_errors = 0
        active_lines = []
        for line in self.request.POST["lijnen"].split(','):
        #for line in self.request.GET['line'].split(','):
            if line == "":
                continue
            log.info("Finding line %s for '%s'" % (line, self.request.user))
            l = Kv1Line.find_from_realtime(self.request.user.userprofile.company, line)
            if l:
                active_lines.append(l)
            else:
                line_errors += 1
                log.error("User '%s' (%s) failed to find line '%s' " % (self.request.user, self.request.user.userprofile.company, journey))
    #        print("Active_lines: ", active_lines)
        print('lijnen:', active_lines)
        data['lijnen'] = active_lines
        data['operatingday'] = self.request.POST["date"]
    #    data['header'] = ['Lijn', 'Eindbestemming']
        if line_errors > 0:
            data['line_errors'] = line_errors

        return data


    def form_invalid(self, form):
        log.error("Form for KV17 change invalid!")
        return super(ChangeLineCancelCreateView, self).form_invalid(form)

    def form_valid(self, form):
        print("...1")
        form.instance.dataownercode = self.request.user.userprofile.company

        # TODO this is a bad solution - totally gets rid of any benefit of Django's CBV and Forms
        xml = form.save()

        if len(xml) == 0:
            log.error("Tried to communicate KV17 empty line change, rejecting")
            # This is kinda weird, but shouldn't happen, everything has validation
            return HttpResponseRedirect(self.success_url)

        # Push message to GOVI
        if self.push_message(xml):
            #log.info("Sent KV17 line change to subscribers: %s" % self.request.POST.get('lines', "<unknown>"))
            log.info("Sent KV17 line change to subscribers: %s" % self.request.POST.get("lijnen", "<unknown>"))
        else:
            log.error("Failed to communicate KV17 line change to subscribers")

        # Another hack to redirect correctly
        return HttpResponseRedirect(self.success_url)


class ActiveDaysAjaxView(LoginRequiredMixin, JSONListResponseMixin, DetailView):
    model = Kv1Line
    render_object = 'object'

    def get_object(self):
        # Note, can't set this on the view, because it triggers the queryset cache
        queryset = self.model.objects.filter(changes__operatingday=get_operator_date(),
                                             # changes__is_recovered=False, # TODO Fix this - see bug #61
                                             # These two are double, but just in case
                                             changes__dataownercode=self.request.user.userprofile.company,
                                             dataownercode=self.request.user.userprofile.company).distinct()
        print("ActiveDaysAjax: ", list(queryset.values('id', 'dataownercode')))
        return list(queryset.values('id', 'dataownercode'))
