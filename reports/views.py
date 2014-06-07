# Create your views here.
from braces.views import LoginRequiredMixin
from django.views.generic import ListView, TemplateView
from kv1.models import Kv1Line
from reports.models import Kv6Log
from utils.views import JSONListResponseMixin, AccessMixin
import datetime


class VehicleReportView(AccessMixin, TemplateView):
    permission_required = 'openebs.view_dashboard'
    template_name = "reports/vehicle_report.html"

    def get_context_data(self, **kwargs):
        data = super(VehicleReportView, self).get_context_data(**kwargs)
        data['list'] = Kv6Log.do_report()
        return data


class VehicleReportDetailsView(AccessMixin, JSONListResponseMixin, TemplateView):
    permission_required = 'openebs.view_dashboard'
    render_object = 'details'

    def get_context_data(self, **kwargs):
        return {'details': Kv6Log.do_details() }

class LineDetailsView(AccessMixin, JSONListResponseMixin, ListView):
    permission_required = 'openebs.view_dashboard'
    render_object = 'object_list'
    model = Kv6Log

    def get_queryset(self):
        qryset = super(LineDetailsView, self).get_queryset()
        return qryset.filter(lineplanningnumber=self.kwargs['line'], operatingday=datetime.date.today(),
                             last_logged__gt=(datetime.datetime.now() - datetime.timedelta(minutes=15)))\
                     .order_by('vehiclenumber').values()

