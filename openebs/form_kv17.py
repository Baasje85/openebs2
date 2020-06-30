from builtins import object
import logging
from crispy_forms.bootstrap import AccordionGroup, Accordion
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Hidden
import floppyforms.__future__ as forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from kv1.models import Kv1Journey, Kv1JourneyDate, Kv1Line, Kv1Stop
from kv15.enum import REASONTYPE, SUBREASONTYPE, ADVICETYPE, SUBADVICETYPE, MONITORINGERROR
from openebs.models import Kv17Change, Kv17Shorten
from openebs.models import Kv17JourneyChange, Kv17MutationMessage
from utils.time import get_operator_date
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware, utc
from datetime import datetime, time, timedelta
from django.db.models import Q, Max

log = logging.getLogger('openebs.forms')


class Kv17ChangeForm(forms.ModelForm):
    # This is duplication, but should work
    operatingday = forms.ChoiceField(label=_("Datum"), required=True)
    begintime_part = forms.TimeField(label=_('Ingangstijd'), required=False, widget=forms.TimeInput(format='%H:%M:%S'))
    endtime_part = forms.TimeField(label=_('Eindtijd'), required=False, widget=forms.TimeInput(format='%H:%M:%S'))
    reasontype = forms.ChoiceField(choices=REASONTYPE, label=_("Type oorzaak"), required=False)
    subreasontype = forms.ChoiceField(choices=SUBREASONTYPE, label=_("Oorzaak"), required=False)
    reasoncontent = forms.CharField(max_length=255, label=_("Uitleg oorzaak"), required=False,
                                    widget=forms.Textarea(attrs={'cols': 40, 'rows': 4, 'class': 'col-lg-6'}))
    advicetype = forms.ChoiceField(choices=ADVICETYPE, label=_("Type advies"), required=False)
    subadvicetype = forms.ChoiceField(choices=SUBADVICETYPE, label=_("Advies"), required=False)
    advicecontent = forms.CharField(max_length=255, label=_("Uitleg advies"), required=False,
                                    widget=forms.Textarea(attrs={'cols': 40, 'rows': 4, 'class': 'col-lg-6'}))
    monitoring_error = forms.ChoiceField(choices=MONITORINGERROR, required=False)

    def clean(self):
        cleaned_data = super(Kv17ChangeForm, self).clean()

        operatingday = parse_date(self.data['operatingday'])
        if operatingday is None:
            raise ValidationError(_("Er staan geen ritten in de database"))

        if 'journeys' not in self.data:
            raise ValidationError(_("Een of meer geselecteerde ritten zijn ongeldig"))

        if self.data['begintime_part'] != '':
            hh, mm = self.data['begintime_part'].split(':')
            begintime = make_aware(datetime.combine(operatingday, time(int(hh), int(mm))))
        else:
            begintime = None

        if self.data['endtime_part'] != '':
            hh_e, mm_e = self.data['endtime_part'].split(':')
            endtime = make_aware(datetime.combine(operatingday, time(int(hh_e), int(mm_e))))
            if begintime:
                if begintime > endtime:  # if endtime before begintime
                    endtime = endtime + timedelta(days=1)  # endtime is next day
                    if endtime.time() >= time(6, 0):  # and after 6 am: validation error
                        raise ValidationError(_("Eindtijd valt op volgende operationele dag"))
        else:
            endtime = None

        dataownercode = self.user.userprofile.company

        if 'Alle ritten' in self.data['journeys']:
            valid_journeys = self.clean_all_journeys(operatingday, dataownercode, begintime, endtime)
        elif 'Hele vervoerder' in self.data['lines']:
            valid_journeys = self.clean_all_lines(operatingday, dataownercode, begintime, endtime)
        else:
            valid_journeys = self.clean_journeys(operatingday, dataownercode)

        if valid_journeys == 0:
            raise ValidationError(_("Er zijn geen ritten geselecteerd om op te heffen"))

        return cleaned_data

    def clean_journeys(self, operatingday, dataownercode):
        valid_journeys = 0
        if self.data['journeys'] != '':
            for journey in self.data['journeys'].split(',')[0:-1]:
                journey_qry = Kv1Journey.objects.filter(dataownercode=dataownercode,
                                                        pk=journey,
                                                        dates__date=operatingday)
                if journey_qry.count() == 0:
                    raise ValidationError(_("Een of meer geselecteerde ritten zijn ongeldig"))

                database = Kv17Change.objects.filter(journey__pk=journey,
                                                     line=journey_qry[0].line,
                                                     dataownercode=dataownercode,
                                                     operatingday=operatingday,
                                                     is_recovered=False)

                if 'Annuleren' in self.data:
                    if database.filter(is_cancel=True):
                        raise ValidationError(_("Een of meer geselecteerde ritten zijn al aangepast."))

                    # delete recovered if query is the same.
                    Kv17Change.objects.filter(dataownercode=dataownercode,
                                              journey__pk=journey,
                                              line=journey_qry[0].line,
                                              operatingday=operatingday,
                                              is_recovered=True,
                                              is_cancel=True).delete()

                    # change not_monitored to 'recovered=True' if cancel_query is the same
                    Kv17Change.objects.filter(journey__pk=journey,
                                              dataownercode=dataownercode,
                                              line=journey_qry[0].line,
                                              operatingday=operatingday,
                                              monitoring_error__isnull=False,
                                              is_recovered=False).update(is_recovered=True)

                else:  # NotMonitored Journey
                    if database.filter(Q(monitoring_error__isnull=False) | Q(is_cancel=True)):
                        raise ValidationError(_("Een of meer geselecteerde ritten zijn al aangepast"))

                    # delete recovered if query is the same.
                    Kv17Change.objects.filter(journey__pk=journey,
                                              line=journey_qry[0].line,
                                              dataownercode=dataownercode,
                                              operatingday=operatingday,
                                              monitoring_error__isnull=False,
                                              is_recovered=True).delete()
        else:
            raise ValidationError(_("Er werd geen rit geselecteerd."))

        valid_journeys += 1

        return valid_journeys

    def clean_all_journeys(self, operatingday, dataownercode, begintime, endtime):
        valid_journeys = 0

        if 'lines' in self.data:
            if self.data['lines'] != '':
                for line in self.data['lines'].split(',')[0:-1]:
                    line_qry = Kv1Line.objects.filter(pk=line)

                    if line_qry.count() == 0:
                        raise ValidationError(_("Geen lijn gevonden."))

                    database_alljourneys = Kv17Change.objects.filter(dataownercode=dataownercode,
                                                                     is_alljourneysofline=True,
                                                                     line=line_qry[0],
                                                                     operatingday=operatingday,
                                                                     is_recovered=False)

                    database_alllines = Kv17Change.objects.filter(dataownercode=dataownercode,
                                                                  is_alllines=True,
                                                                  operatingday=operatingday,
                                                                  is_recovered=False)

                    if 'Annuleren' in self.data:

                        # delete recovered if query is the same.
                        Kv17Change.objects.filter(dataownercode=dataownercode,
                                                  line=line_qry[0],
                                                  is_alljourneysofline=True,
                                                  is_recovered=True,
                                                  is_cancel=True,
                                                  operatingday=operatingday,
                                                  begintime=begintime,
                                                  endtime=endtime).delete()

                        # change not_monitored to 'recovered=True' if cancel_query is the same
                        Kv17Change.objects.filter(dataownercode=dataownercode,
                                                  line=line_qry[0],
                                                  is_alljourneysofline=True,
                                                  is_recovered=True,
                                                  monitoring_error__isnull=False,
                                                  operatingday=operatingday,
                                                  begintime=begintime,
                                                  endtime=endtime).update(is_recovered=True)

                        if database_alllines:
                            begintime = datetime.utcnow().replace(tzinfo=utc) if begintime is None else begintime
                            if database_alllines.filter(Q(endtime__gt=begintime) | Q(endtime=None) &
                                                        Q(begintime__lt=begintime),
                                                        is_cancel=True):
                                raise ValidationError(_(
                                    "De gehele vervoerder is al aangepast voor de aangegeven ingangstijd."))

                        elif database_alljourneys:
                            begintime = datetime.utcnow().replace(tzinfo=utc) if begintime is None else begintime
                            if database_alljourneys.filter(Q(endtime__gt=begintime) | Q(endtime=None) &
                                                           Q(begintime__lt=begintime),
                                                           is_cancel=True):
                                raise ValidationError(_(
                                    "Een of meer geselecteerde lijnen zijn al aangepast voor de aangegeven ingangstijd."))

                    else:  # NotMonitored Line
                        # delete recovered if query is the same.
                        Kv17Change.objects.filter(dataownercode=dataownercode,
                                                  line=line_qry[0],
                                                  is_alljourneysofline=True,
                                                  is_recovered=True,
                                                  monitoring_error__isnull=False,
                                                  operatingday=operatingday,
                                                  begintime=begintime,
                                                  endtime=endtime).delete()

                        if database_alllines:
                            begintime = datetime.utcnow().replace(tzinfo=utc) if begintime is None else begintime
                            if database_alllines.filter(Q(monitoring_error__isnull=False) | Q(is_cancel=True) &
                                                        Q(endtime__gt=begintime) | Q(endtime=None) &
                                                        Q(begintime__lt=begintime)):
                                raise ValidationError(_(
                                    "De gehele vervoerder is al aangepast voor de aangegeven ingangstijd."))

                        elif database_alljourneys:
                            begintime = datetime.utcnow().replace(tzinfo=utc) if begintime is None else begintime
                            if database_alljourneys.filter(Q(monitoring_error__isnull=False) | Q(is_cancel=True) &
                                                         Q(endtime__gt=begintime) | Q(endtime=None) &
                                                         Q(begintime__lt=begintime)):
                                raise ValidationError(_("Een of meer geselecteerde lijnen zijn al aangepast"))

        else:
            raise ValidationError(_("Geen geldige lijn geselecteerd"))

        valid_journeys += 1

        return valid_journeys

    def clean_all_lines(self, operatingday, dataownercode, begintime, endtime):
        valid_journeys = 0

        database_alllines = Kv17Change.objects.filter(dataownercode=dataownercode,
                                                      is_alllines=True,
                                                      operatingday=operatingday,
                                                      is_recovered=False)

        if 'Annuleren' in self.data:
            # delete recovered if query is the same.
            Kv17Change.objects.filter(dataownercode=dataownercode,
                                      is_alllines=True,
                                      is_cancel=True,
                                      is_recovered=True,
                                      operatingday=operatingday,
                                      begintime=begintime,
                                      endtime=endtime).delete()

            # change not_monitored to 'recovered=True' if cancel_query is the same
            Kv17Change.objects.filter(dataownercode=dataownercode,
                                      is_alllines=True,
                                      monitoring_error__isnull=False,
                                      is_recovered=False,
                                      operatingday=operatingday,
                                      begintime=begintime,
                                      endtime=endtime).update(is_recovered=True)

            if database_alllines:
                begintime = datetime.utcnow().replace(tzinfo=utc) if begintime is None else begintime
                if database_alllines.filter(Q(endtime__gt=begintime) | Q(endtime=None) &
                                            Q(begintime__lt=begintime),
                                            is_cancel=True):
                    raise ValidationError(_("De ingangstijd valt al binnen een geplande operatie."))

        else:  # NotMonitored dataownercode
            # delete recovered if query is the same.
            Kv17Change.objects.filter(dataownercode=dataownercode,
                                      is_alllines=True,
                                      monitoring_error__isnull=False,
                                      is_recovered=True,
                                      operatingday=operatingday,
                                      begintime=begintime,
                                      endtime=endtime).delete()

            if database_alllines:
                begintime = datetime.utcnow().replace(tzinfo=utc) if begintime is None else begintime
                if database_alllines.filter(Q(monitoring_error__isnull=False) | Q(is_cancel=True) &
                                            Q(endtime__gt=begintime) | Q(endtime=None) &
                                            Q(begintime__lt=begintime)):
                    raise ValidationError(_(
                        "De gehele vervoerder is al aangepast voor de aangegeven ingangstijd."))

        valid_journeys += 1

        return valid_journeys

    def save(self, force_insert=False, force_update=False, commit=True):
        ''' Save each of the journeys in the model. This is a disaster, we return the XML
        TODO: Figure out a better solution fo this! '''
        operatingday = parse_date(self.data['operatingday'])
        if self.data['begintime_part'] != '':
            hh, mm = self.data['begintime_part'].split(':')
            begintime = make_aware(datetime.combine(operatingday, time(int(hh), int(mm))))
        else:
            begintime = None

        if self.data['endtime_part'] != '':
            hh_end, mm_end = self.data['endtime_part'].split(':')
            # if begintime is set and endtime is earlier than begintime add 1 day to operatingday of endtime
            if begintime and time(int(hh_end), int(mm_end)) < time(int(hh), int(mm)):
                if time(0, 0) <= time(int(hh_end), int(mm_end)) < time(6, 0):
                    operatingday_endtime = operatingday + timedelta(days=1)
                endtime = make_aware(datetime.combine(operatingday_endtime, time(int(hh_end), int(mm_end))))
            # else, operatingday is given day
            else:
                endtime = make_aware(datetime.combine(operatingday, time(int(hh_end), int(mm_end))))
        else:
            endtime = None

        if 'Annuleren' in self.data:
            if 'Alle ritten' in self.data['journeys']:
                xml_output = self.save_all_journeys(operatingday, begintime, endtime)
            elif 'Hele vervoerder' in self.data['lines']:
                xml_output = self.save_all_lines(operatingday, begintime, endtime)
            else:
                xml_output = self.save_journeys(operatingday)
        else:
            xml_output = self.save_notmonitored(operatingday, begintime, endtime)

        return xml_output

    def save_all_lines(self, operatingday, begintime, endtime):
        xml_output = []

        self.instance.pk = None
        self.instance.is_alllines = True
        self.instance.operatingday = operatingday
        self.instance.begintime = begintime
        self.instance.endtime = endtime
        self.instance.is_cancel = True
        self.instance.monitoring_error = None

        # Unfortunately, we can't place this any earlier, because we don't have the dataownercode there
        if self.instance.dataownercode == self.user.userprofile.company:
            self.instance.save()

            # Add details
            if self.data['reasontype'] != '0' or self.data['advicetype'] != '0':
                Kv17JourneyChange(change=self.instance, reasontype=self.data['reasontype'],
                                  subreasontype=self.data['subreasontype'],
                                  reasoncontent=self.data['reasoncontent'],
                                  advicetype=self.data['advicetype'],
                                  subadvicetype=self.data['subadvicetype'],
                                  advicecontent=self.data['advicecontent']).save()

            xml_output.append(self.instance.to_xml())
        else:
            log.error(
                "Oops! mismatch between dataownercode of line (%s) and of user (%s) when saving journey cancel" %
                (self.instance.line.dataownercode, self.instance.dataownercode))

        return xml_output

    def save_all_journeys(self, operatingday, begintime, endtime):
        xml_output = []

        for line in self.data['lines'].split(',')[0:-1]:
            qry = Kv1Line.objects.filter(id=line)
            if qry.count() == 1:
                self.instance.pk = None
                self.instance.is_alljourneysofline = True
                self.instance.line = qry[0]
                self.instance.operatingday = operatingday
                self.instance.begintime = begintime
                self.instance.endtime = endtime
                self.instance.is_cancel = True
                self.instance.monitoring_error = None

                # Unfortunately, we can't place this any earlier, because we don't have the dataownercode there
                if self.instance.line.dataownercode == self.instance.dataownercode:
                    self.instance.save()

                    # Add details
                    if self.data['reasontype'] != '0' or self.data['advicetype'] != '0':
                        Kv17JourneyChange(change=self.instance, reasontype=self.data['reasontype'],
                                          subreasontype=self.data['subreasontype'],
                                          reasoncontent=self.data['reasoncontent'],
                                          advicetype=self.data['advicetype'],
                                          subadvicetype=self.data['subadvicetype'],
                                          advicecontent=self.data['advicecontent']).save()

                    xml_output.append(self.instance.to_xml())
                else:
                    log.error(
                        "Oops! mismatch between dataownercode of line (%s) and of user (%s) when saving journey cancel" %
                        (self.instance.line.dataownercode, self.instance.dataownercode))

            else:
                log.error("Failed to find line %s" % line)

        return xml_output

    def save_journeys(self, operatingday):
        xml_output = []

        for journey in self.data['journeys'].split(',')[0:-1]:
            qry = Kv1Journey.objects.filter(id=journey, dates__date=operatingday)
            if qry.count() == 1:
                self.instance.pk = None
                self.instance.journey = qry[0]
                self.instance.line = qry[0].line
                self.instance.operatingday = operatingday
                self.instance.is_cancel = True
                self.instance.monitoring_error = None
                # shouldn't be necessary, but just in case...
                self.instance.begintime = None
                self.instance.endtime = None

                # Unfortunately, we can't place this any earlier, because we don't have the dataownercode there
                if self.instance.journey.dataownercode == self.instance.dataownercode:
                    self.instance.save()

                    # Add details
                    if self.data['reasontype'] != '0' or self.data['advicetype'] != '0':
                        Kv17JourneyChange(change=self.instance, reasontype=self.data['reasontype'],
                                          subreasontype=self.data['subreasontype'],
                                          reasoncontent=self.data['reasoncontent'],
                                          advicetype=self.data['advicetype'],
                                          subadvicetype=self.data['subadvicetype'],
                                          advicecontent=self.data['advicecontent']).save()

                    xml_output.append(self.instance.to_xml())
                else:
                    log.error(
                        "Oops! mismatch between dataownercode of line (%s) and of user (%s) when saving journey cancel" %
                        (self.instance.journey.dataownercode, self.instance.dataownercode))
            else:
                log.error("Failed to find journey %s" % journey)

        return xml_output

    def save_notmonitored(self, operatingday, begintime, endtime):
        xml_output = []

        if 'Hele vervoerder' in self.data['lines']:  # hele vervoerder
            self.instance.pk = None
            self.instance.operatingday = operatingday
            self.instance.monitoring_error = self.data['notMonitored']
            self.instance.autorecover = False
            self.instance.showcancelledtrip = False
            self.instance.is_cancel = False
            self.instance.is_alllines = True
            self.instance.begintime = begintime
            self.instance.endtime = endtime

            # Unfortunately, we can't place this any earlier, because we don't have the dataownercode there
            if self.instance.dataownercode == self.user.userprofile.company:
                self.instance.save()

                xml_output.append(self.instance.to_xml())
            else:
                log.error(
                    "Oops! mismatch between dataownercode of line (%s) and of user (%s) when saving journey cancel" %
                    (self.instance.journey.dataownercode, self.instance.dataownercode))

        elif 'Alle ritten' in self.data['journeys']:  # hele lijn(en)
            for line in self.data['lines'].split(',')[0:-1]:
                qry = Kv1Line.objects.filter(id=line)
                if qry.count == 0:
                    log.error("Failed to find line %s" % line)
                else:
                    self.instance.pk = None
                    self.instance.line = qry[0]
                    self.instance.operatingday = operatingday
                    self.instance.begintime = begintime
                    self.instance.endtime = endtime
                    self.instance.is_alljourneysofline = True
                    self.instance.monitoring_error = self.data['notMonitored']
                    self.instance.autorecover = False
                    self.instance.showcancelledtrip = False
                    self.instance.is_cancel = False

                    # Unfortunately, we can't place this any earlier, because we don't have the dataownercode there
                    if self.instance.line.dataownercode == self.instance.dataownercode:
                        self.instance.save()

                        xml_output.append(self.instance.to_xml())
                    else:
                        log.error(
                            "Oops! mismatch between dataownercode of line (%s) and of user (%s) when saving journey cancel" %
                            (self.instance.journey.dataownercode, self.instance.dataownercode))

        else:  # enkele rit(ten)
            for journey in self.data['journeys'].split(',')[0:-1]:
                qry = Kv1Journey.objects.filter(id=journey, dates__date=operatingday)
                if qry.count == 0:
                    log.error("Failed to find journey %s" % journey)
                else:
                    # check if there's already a kv17change on this journey that is not a cancel
                    qry_kv17change = Kv17Change.objects.filter(journey=qry[0],
                                                               operatingday=parse_date(self.data['operatingday']),
                                                               # shouldn't be neccessary, but just in case:
                                                               is_cancel=False,
                                                               is_recovered=False)
                    if qry_kv17change.count() == 1:
                        self.instance = qry_kv17change[0]
                    else:
                        self.instance.pk = None
                        self.instance.journey = qry[0]
                        self.instance.line = qry[0].line
                        self.instance.operatingday = operatingday
                        self.instance.begintime = None
                        self.instance.endtime = None
                        self.instance.monitoring_error = self.data['notMonitored']
                        self.instance.autorecover = False
                        self.instance.showcancelledtrip = False
                        self.instance.is_cancel = False

                # Unfortunately, we can't place this any earlier, because we don't have the dataownercode there
                if self.instance.journey.dataownercode == self.instance.dataownercode:
                    if qry_kv17change.count() == 0:
                        self.instance.save()
                    else:
                        # update database-object
                        Kv17Change.objects.filter(journey=qry[0],
                                                  operatingday=parse_date(self.data['operatingday'])).update(
                                                  monitoring_error=self.data['notMonitored'])
                        # update self.instance
                        self.instance.monitoring_error = self.data['notMonitored']
                    xml_output.append(self.instance.to_xml())
                else:
                    log.error(
                        "Oops! mismatch between dataownercode of line (%s) and of user (%s) when saving journey cancel" %
                        (self.instance.journey.dataownercode, self.instance.dataownercode))
        return xml_output

    class Meta(object):
        model = Kv17Change
        exclude = ['dataownercode', 'operatingday', 'line', 'journey', 'is_recovered', 'reinforcement']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(Kv17ChangeForm, self).__init__(*args, **kwargs)

        DAYS = [[str(d['date'].strftime('%Y-%m-%d')), str(d['date'].strftime('%d-%m-%Y'))] for d in
                Kv1JourneyDate.objects.all()
                              .filter(date__gte=datetime.today() - timedelta(days=1))
                              .values('date')
                              .distinct('date')
                              .order_by('date')]

        OPERATING_DAY = DAYS[((datetime.now().hour < 4) * -1) + 1] if len(DAYS) > 1 else None
        self.fields['operatingday'].choices = DAYS
        self.fields['operatingday'].initial = OPERATING_DAY

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Accordion(
                AccordionGroup(_('Datum en tijd'),
                               'operatingday',
                               'begintime_part',
                               'endtime_part'
                               ),
                AccordionGroup(_('Oorzaak'),
                               'reasontype',
                               'subreasontype',
                               'reasoncontent'
                               ),
                AccordionGroup(_('Advies'),
                               'advicetype',
                               'subadvicetype',
                               'advicecontent'
                               ),
                AccordionGroup(_('Opties'),
                               'autorecover',
                               'showcancelledtrip'
                               )
            )
        )


class CancelLinesForm(forms.Form):
    verify_ok = forms.BooleanField(initial=True, widget=forms.HiddenInput)

    def clean_verify_ok(self):
        if self.cleaned_data.get('verify_ok') is not True:
            raise ValidationError(_("Je moet goedkeuring geven om alle lijnen op te heffen"))

    def __init__(self, *args, **kwargs):
        super(CancelLinesForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = 'journey_redbutton'
        self.helper.layout = Layout(
            Hidden('verify_ok', 'true'),
            Submit('submit', _("Hef alle ritten op"), css_class="text-center btn-danger btn-tall col-sm-3 pull-right")
        )


class Kv17ShortenForm(forms.ModelForm):
    operatingday = forms.ChoiceField(label=_("Datum"), required=True)
    reasontype = forms.ChoiceField(choices=REASONTYPE, label=_("Type oorzaak"), required=False)
    subreasontype = forms.ChoiceField(choices=SUBREASONTYPE, label=_("Oorzaak"), required=False)
    reasoncontent = forms.CharField(max_length=255, label=_("Uitleg oorzaak"), required=False,
                                    widget=forms.Textarea(attrs={'cols': 40, 'rows': 4, 'class': 'col-lg-6'}))
    advicetype = forms.ChoiceField(choices=ADVICETYPE, label=_("Type advies"), required=False)
    subadvicetype = forms.ChoiceField(choices=SUBADVICETYPE, label=_("Advies"), required=False)
    advicecontent = forms.CharField(max_length=255, label=_("Uitleg advies"), required=False,
                                    widget=forms.Textarea(attrs={'cols': 40, 'rows': 4, 'class': 'col-lg-6'}))

    def clean(self):
        cleaned_data = super(Kv17ShortenForm, self).clean()

        #Kv17Change.objects.all().delete()
        #Kv17Shorten.objects.all().delete()

        operating_day = self.data['operatingday']
        if operating_day is None:
            raise ValidationError(_("Er staan geen ritten in de database"))

        dataownercode = self.user.userprofile.company

        valid_journeys = 0
        if self.data['journeys'] != '':
            for journey in self.data['journeys'].split(',')[0:-1]:
                journey_qry = Kv1Journey.objects.filter(dataownercode=dataownercode,
                                                        pk=journey,
                                                        dates__date=operating_day)
                if journey_qry.count() == 0:
                    raise ValidationError(_("Een of meer geselecteerde ritten zijn ongeldig"))
                valid_stops = []
                unique_stops = 0
                # splits stopdict per lijn: .split(;)
                for line in self.data['stopdict'].split(";"):
                    if line != '':
                        if line.split(":")[0] == journey_qry[0].line.publiclinenumber:
                            haltes = line.split(":")[1].split(",")
                            for halte in haltes:
                                if halte != '':
                                    halte_split = halte.split('_')
                                    if len(halte_split) == 2:
                                        stop = Kv1Stop.find_stop(halte_split[0], halte_split[1])
                                        if stop:
                                            valid_stops.append(stop.pk)
                                        else:
                                            raise ValidationError(
                                                _("Datafout: halte niet gevonden in database. Meld dit bij een beheerder."))

                                    if Kv17Shorten.objects.filter(stop=stop.pk,
                                                                  change__journey__pk=journey,
                                                                  change__line=journey_qry[0].line,
                                                                  change__operatingday=operating_day,
                                                                  change__is_recovered=False).count() == 0:
                                        unique_stops += 1

                if len(valid_stops) == 0:
                    raise ValidationError(_("Selecteer minimaal een halte"))

                if unique_stops == 0:
                    raise ValidationError(
                        _("De geselecteerde halte(s) zijn al aangepast voor de geselecteerde rit(ten)"))

                # if same shorten_query in database as 'is-recovered', delete
                Kv17Change.objects.filter(line=self.instance.line,
                                          journey=self.instance.journey,
                                          operatingday=self.instance.operatingday,
                                          begintime=self.instance.begintime,
                                          endtime=self.instance.endtime,
                                          is_cancel=False,
                                          is_recovered=True,
                                          shorten_details__stop=stop).delete()

            valid_journeys += 1

        if valid_journeys == 0:
            raise ValidationError(_("Er zijn geen ritten geselecteerd om op te heffen"))

        return cleaned_data

    def save(self, force_insert=False, force_update=False, commit=True):
        """ Save each of the journeys in the model. This is a disaster, we return the XML
        TODO: Figure out a better solution fo this! """

        xml_output = []
        for journey in self.data['journeys'].split(',')[0:-1]:
            qry = Kv1Journey.objects.filter(id=journey, dates__date=self.data['operatingday'])
            if qry.count() == 1:
                qry_kv17change = Kv17Change.objects.filter(journey=qry[0], operatingday=parse_date(self.data['operatingday']))
                if qry_kv17change.count() == 1:
                    self.instance = qry_kv17change[0]
                else:
                    self.instance.pk = None
                    self.instance.journey = qry[0]
                    self.instance.line = qry[0].line
                    self.instance.operatingday = parse_date(self.data['operatingday'])
                    self.instance.begintime = None
                    self.instance.endtime = None
                    self.instance.is_cancel = False

                # Unfortunately, we can't place this any earlier, because we don't have the dataownercode there
                if self.instance.journey.dataownercode == self.instance.dataownercode:
                    if qry_kv17change.count() == 0:
                        self.instance.save()
                    else:
                        # update kv17change-object
                        Kv17Change.objects.filter(journey=qry[0], operatingday=parse_date(self.data['operatingday']))\
                                          .update(showcancelledtrip=self.cleaned_data['showcancelledtrip'])
                        # update self.instance
                        self.instance.showcancelledtrip = self.cleaned_data['showcancelledtrip']

                    self.save_shorten(qry_kv17change)
                    self.save_mutationmessage()
                    xml_output.append(self.instance.to_xml())

                else:
                    log.error(
                        "Oops! mismatch between dataownercode of line (%s) and of user (%s) when saving journey cancel" %
                        (self.instance.journey.dataownercode, self.instance.dataownercode))
            else:
                log.error("Failed to find journey %s" % journey)

        return xml_output

    def save_shorten(self, qry_kv17change):
        for halte in self.data['haltes'].split(','):
            if len(halte) == 0:
                continue

            halte_split = halte.split('_')
            if len(halte_split) != 2:
                continue

            stop = Kv1Stop.find_stop(halte_split[0], halte_split[1])

            if qry_kv17change.count() != 0:
                ids = qry_kv17change.values_list('id', flat=True)[0]
                if Kv17Shorten.objects.filter(change=self.instance,
                                              change_id=ids, stop=stop,
                                              # passagesequencenumber=0,   TODO: resolve this in the future
                                              ).count() == 0:
                    Kv17Shorten(change=self.instance,
                                change_id=ids, stop=stop,
                                # passagesequencenumber=0,   TODO: resolve this in the future
                                ).save()

            else:
                Kv17Shorten(change=self.instance, stop=stop,
                            # passagesequencenumber=0,   TODO: resolve this in the future
                            ).save()

    def save_mutationmessage(self):
        # Add details
        for halte in self.data['haltes'].split(','):
            if len(halte) == 0:
                continue

            halte_split = halte.split('_')
            if len(halte_split) != 2:
                continue

            stop = Kv1Stop.find_stop(halte_split[0], halte_split[1])

        if self.data['reasontype'] != '0' or self.data['advicetype'] != '0':
            Kv17MutationMessage(change=self.instance,
                                stop=stop,
                                # passagesequencenumber=0,  # TODO: resolve this in the future
                                reasontype=self.data['reasontype'],
                                subreasontype=self.data['subreasontype'],
                                reasoncontent=self.data['reasoncontent'],
                                advicetype=self.data['advicetype'],
                                subadvicetype=self.data['subadvicetype'],
                                advicecontent=self.data['advicecontent']).save()

    class Meta(Kv17ChangeForm.Meta):
        model = Kv17Change
        exclude = ['dataownercode', 'operatingday', 'line', 'journey', 'is_recovered', 'reinforcement', 'stop',
                   'passagesequencenumber', 'change', 'monitoring_error', 'stops']

        # inherit 'showcancelledtrip' from kv17Change to avoid duplication
        fields = ('showcancelledtrip',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(Kv17ShortenForm, self).__init__(*args, **kwargs)

        DAYS = [[str(d['date'].strftime('%Y-%m-%d')), str(d['date'].strftime('%d-%m-%Y'))] for d in
                Kv1JourneyDate.objects.all()
                    .filter(date__gte=datetime.today() - timedelta(days=1))
                    .values('date')
                    .distinct('date')
                    .order_by('date')]

        OPERATING_DAY = DAYS[((datetime.now().hour < 4) * -1) + 1] if len(DAYS) > 1 else None
        self.fields['operatingday'].choices = DAYS
        self.fields['operatingday'].initial = OPERATING_DAY
        self.fields['showcancelledtrip'].initial = True

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Accordion(
                AccordionGroup(_('Datum'),
                               'operatingday',
                               ),
                AccordionGroup(_('Oorzaak'),
                               'reasontype',
                               'subreasontype',
                               'reasoncontent'
                               ),
                AccordionGroup(_('Advies'),
                               'advicetype',
                               'subadvicetype',
                               'advicecontent'
                               ),
                AccordionGroup(_('Opties'),
                               'showcancelledtrip'
                               )
            )
        )