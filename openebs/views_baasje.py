import logging
from braces.views import LoginRequiredMixin
from datetime import timedelta
from django.shortcuts import render
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.views.generic import ListView, CreateView, DeleteView, DetailView
from kv1.models import Kv1Journey, Kv1Line
from openebs.form import Kv17ChangeForm, Kv17ChangeLineForm, ChangeLineCancelCreateForm
from openebs.models import Kv17Change, Kv17ChangeLine
from openebs.views_push import Kv17PushMixin
from openebs.views_utils import FilterDataownerMixin
from utils.time import get_operator_date
from utils.views import AccessMixin, ExternalMessagePushMixin, JSONListResponseMixin
from django.views.generic import CreateView, UpdateView, DeleteView

class ChangeLineCancelCreateView(AccessMixin, Kv17PushMixin, CreateView):
    permission_required = 'openebs.add_change'
    model = Kv17ChangeLine
    form_class = ChangeLineCancelCreateForm
    template_name = 'openebs/lines_list.html'
    success_url = reverse_lazy('change_line_cancel_index')

    def get_context_data(self, **kwargs):
        data = super(ChangeLineCancelCreateView, self).get_context_data(**kwargs)
        return self.get_lines()

    def get_lines(self):
        #search_fields = ('publiclinenumber')
        line_dict = {}
        line_list = Kv1Line.objects.all() \
            .filter(dataownercode=self.request.user.userprofile.company) \
            .values('publiclinenumber','headsign', 'dataownercode') \
            .order_by('publiclinenumber')
        line_dict['operator_date'] = get_operator_date()
        line_dict['header'] = ['Lijn', 'Eindbestemming']
        line_dict['lines'] = list(line_list)
        return line_dict
        # return super(CreateView, self)
        # return render(self.request, 'openebs/lines_list.html', context=line_dict)

    def form_invalid(self, form):
        log.error("Form for KV17 change invalid!")
        return super(ChangeLineCancelCreateView, self).form_invalid(form)

    def form_valid(self, form):
        form.instance.dataownercode = self.request.user.userprofile.company

        # TODO this is a bad solution - totally gets rid of any benefit of Django's CBV and Forms
        xml = form.save()

        if len(xml) == 0:
            log.error("Tried to communicate KV17 empty line change, rejecting")
            # This is kinda weird, but shouldn't happen, everything has validation
            return HttpResponseRedirect(self.success_url)

        # Push message to GOVI
        if self.push_message(xml):
            log.info("Sent KV17 line change to subscribers: %s" % self.request.POST.get('lines', "<unknown>"))
        else:
            log.error("Failed to communicate KV17 line change to subscribers")

        # Another hack to redirect correctly
        return HttpResponseRedirect(self.success_url)

# kopie uit views_change om te knippen/plakken naar eigen view
#class ChangeCreateView(AccessMixin, Kv17PushMixin, CreateView):
#    permission_required = 'openebs.add_change'
#    model = Kv17Change
#    form_class = Kv17ChangeForm
#    success_url = reverse_lazy('change_index')

#    def get_context_data(self, **kwargs):
#        data = super(ChangeCreateView, self).get_context_data(**kwargs)
        #data['operator_date'] = get_operator_date()
#        if 'line' in self.request.GET:
#            self.add_line_from_request(data)
#        return data

#    def add_line_from_request(self, data):
#        line_errors = 0
#        lines = []
#        for line in self.request.GET['line'].split(','):
#            if line == "":
#                continue
#            log.info("Finding line %s for '%s'" % (line, self.request.user))
#            l = Kv1Line.find_from_realtime(self.request.user.userprofile.company, line)
#            if l:
#                lines.append(l)
#            else:
#                line_errors += 1
#                log.error("User '%s' (%s) failed to find line '%s' " % (self.request.user, self.request.user.userprofile.company, line))
#        data['lines'] = lines
#        if line_errors > 0:
#            data['line_errors'] = line_errors

#    def form_invalid(self, form):
#        log.error("Form for KV17 change invalid!")
#        return super(ChangeCreateView, self).form_invalid(form)

#    def form_valid(self, form):
#        form.instance.dataownercode = self.request.user.userprofile.company

        # TODO this is a bad solution - totally gets rid of any benefit of Django's CBV and Forms
#        xml = form.save()

#        if len(xml) == 0:
#            log.error("Tried to communicate KV17 empty line change, rejecting")
            # This is kinda weird, but shouldn't happen, everything has validation
#            return HttpResponseRedirect(self.success_url)

        # Push message to GOVI
#        if self.push_message(xml):
#            log.info("Sent KV17 line change to subscribers: %s" % self.request.POST.get('lines', "<unknown>"))
#        else:
#            log.error("Failed to communicate KV17 line change to subscribers")

        # Another hack to redirect correctly
#        return HttpResponseRedirect(self.success_url)

#kopie uit models om te weten wat eruit wordt gehaald
#class Kv17ChangeLine(models.Model):
#    """
#    Container for a kv17 change for a complete line
#    """
#    dataownercode = models.CharField(max_length=10, choices=DATAOWNERCODE, verbose_name=_("Vervoerder"))
#    operatingday = models.DateField(verbose_name=_("Datum"))
#    line = models.ForeignKey(Kv1Line, verbose_name=_("Lijn"), on_delete=models.CASCADE)
    #journey = models.ForeignKey(Kv1Journey, verbose_name=_("Rit"), related_name="changes", on_delete=models.CASCADE)  # "A journey has changes"
    #reinforcement = models.IntegerField(default=0, verbose_name=_("Versterkingsnummer"))  # Never fill this for now
#    is_cancel = models.BooleanField(default=True, verbose_name=_("Opgeheven?"),
#                                    help_text=_("Rit kan ook een toelichting zijn voor een halte"))
#    is_recovered = models.BooleanField(default=False, verbose_name=_("Teruggedraaid?"))
#    created = models.DateTimeField(auto_now_add=True)
#    recovered = models.DateTimeField(null=True, blank=True)  # Not filled till recovered

#    def delete(self):
#        self.is_recovered = True
#        self.recovered = now()
#        self.save()
        # Warning: Don't perform the actual delete here!

#    def force_delete(self):
#        super(Kv17ChangeLine, self).delete()

#    def to_xml(self):
#        """
#        This xml will reflect the status of the object - wheter we've been canceled or recovered
#        """
#        return render_to_string('xml/kv17journey.xml', {'object': self}).replace(os.linesep, '')

#    class Meta(object):
#        verbose_name = _('Lijnaanpassing')
#        verbose_name_plural = _("Lijnaanpassingen")
#        unique_together = ('operatingday', 'line')
#        permissions = (
#            ("view_change", _("Ritaanpassingen bekijken")),
#            ("add_change", _("Ritaanpassingen aanmaken")),
#        )

#    def __unicode__(self):
#        return "%s Lijn %s Rit# %s" % (self.operatingday, self.line, self.journey.journeynumber)

#    def realtime_id(self):
#        return "%s:%s:%s" % (self.dataownercode, self.line.lineplanningnumber, self.journey.journeynumber)
