from django.contrib.gis.db import models
from json_field import JSONField
from kv15.enum import DATAOWNERCODE, STOPTYPES
from django.utils.translation import ugettext_lazy as _


class Kv1Line(models.Model):
    dataownercode = models.CharField(max_length=10, choices=DATAOWNERCODE)
    lineplanningnumber = models.CharField(max_length=10)
    publiclinenumber = models.CharField(max_length=10)
    headsign = models.CharField(max_length=100)
    stop_map = JSONField()

    class Meta:
        verbose_name = _("Lijn")
        verbose_name_plural = _("Lijninformatie")
        unique_together = ('dataownercode', 'lineplanningnumber')

    def __unicode__(self):
        return "%s - %s" % (self.dataownercode, self.headsign)


class Kv1Stop(models.Model):
    userstopcode = models.CharField(max_length=10)
    dataownercode = models.CharField(max_length=10, choices=DATAOWNERCODE)
    name = models.CharField(max_length=50)
    location = models.PointField()

    # Custom manager for geomodels/searches
    objects = models.GeoManager()

    class Meta:
        verbose_name = _("Halte")
        verbose_name_plural = _("Halteinformatie")
        unique_together = ('dataownercode', 'userstopcode')

    def __unicode__(self):
        return "%s - %s" % (self.dataownercode, self.name)

    @staticmethod
    def find_stop(dataowner, stopcode):
        result = Kv1Stop.objects.filter(dataownercode=dataowner, userstopcode=stopcode)
        if result.count() == 1:
            return result[0]

    @staticmethod
    def find_stops_from_haltes(halte_string):
        out = []
        for halte in halte_string.split(','):
            halte_split = halte.split('_')
            if len(halte_split) == 2:
                stop = Kv1Stop.find_stop(halte_split[0], halte_split[1])
                if stop:
                    out.append(stop)
        return out

class Kv1Journey(models.Model):
    dataownercode = models.CharField(max_length=10, choices=DATAOWNERCODE)
    line = models.ForeignKey(Kv1Line, related_name="journeys")  # Represent lineplanningnumber\
    journeynumber = models.PositiveIntegerField(max_length=6)  # 0 - 999999
    scheduleref = models.PositiveIntegerField() # Field 'availabilityconditionref'
    departuretime = models.PositiveIntegerField(db_index=True) # In seconds
    arrivaltime = models.PositiveIntegerField(db_index=True) # Also in seconds
    direction = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return "%s%s - %s" % (self.dataownercode, self.line.publiclinenumber, self.journeynumber)

    class Meta:
        verbose_name = _("Rit")
        verbose_name_plural = _("Ritinformatie")
        unique_together = ('dataownercode', 'line', 'journeynumber', 'scheduleref')


class Kv1JourneyStop(models.Model):
    journey = models.ForeignKey(Kv1Journey, related_name="stops")
    stop = models.ForeignKey(Kv1Stop)
    stoporder = models.SmallIntegerField()
    stoptype = models.CharField(choices=STOPTYPES, default="INTERMEDIATE", max_length=12)
    targetarrival = models.TimeField()
    targetdeparture = models.TimeField()

    def __unicode__(self):
        return "%s - Stop #%s: %s" % (self.journey.journeynumber, self.stoporder, self.stop)

    class Meta:
        verbose_name = _("Rithalte")
        verbose_name_plural = _("Rithaltes")
        unique_together = (('journey', 'stop'), ('journey', 'stoporder'))


class Kv1JourneyDate(models.Model):
    journey = models.ForeignKey(Kv1Journey, related_name='dates')  # A journey has dates
    date = models.DateField()

    def __unicode__(self):
        return "%s (%s)" % (self.journey.journeynumber, self.date)

    class Meta:
        verbose_name = _("Ritdag")
        verbose_name_plural = _("Ritdag")
        unique_together = (('journey', 'date'))

