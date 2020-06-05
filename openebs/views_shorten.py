import logging
from braces.views import LoginRequiredMixin
from datetime import timedelta, datetime
from django.urls import reverse_lazy
from django.db.models import Q, F
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, DeleteView, DetailView
from kv1.models import Kv1Journey, Kv1Line
from openebs.form_kv17 import Kv17ChangeForm, Kv17ShortenForm
from openebs.models import Kv17Change, Kv17Shorten
from openebs.views_push import Kv17PushMixin
from openebs.views_utils import FilterDataownerMixin
from utils.time import get_operator_date, get_operator_date_aware
from utils.views import AccessMixin, ExternalMessagePushMixin, JSONListResponseMixin
from django.utils.dateparse import parse_date
from django.utils.timezone import now

log = logging.getLogger('openebs.views.changes')


class ShortenCreateView(AccessMixin, Kv17PushMixin, CreateView):
    permission_required = 'openebs.add_shorten'
    model = Kv17Shorten
    form_class = Kv17ShortenForm
    success_url = reverse_lazy('shorten_index')


class ShortenDeleteView(AccessMixin, Kv17PushMixin, FilterDataownerMixin, DeleteView):
    permission_required = 'openebs.add_shorten'
    model = Kv17Shorten
    success_url = reverse_lazy('shorten_index')


class ShortenUpdateView(AccessMixin, Kv17PushMixin, FilterDataownerMixin, DeleteView):
    """ This is a really weird view - it's redoing a change that you deleted   """
    permission_required = 'openebs.add_shorten'
    model = Kv17Shorten
    success_url = reverse_lazy('shorten_index')
