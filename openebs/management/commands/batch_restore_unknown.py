import csv

from datetime import date, datetime
from django.core.management import BaseCommand

from kv1.models import Kv1Journey
from openebs.models import Kv17Change
from openebs.views_push import Kv17PushMixin
from utils.time import get_operator_date


class Command(BaseCommand):

    # TODO: This defines a default timeout, we may want to/need to change this for batch operations
    pusher = Kv17PushMixin()

    last_row_date = ""
    date = get_operator_date()
    BATCH_SIZE = 100

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)

    def handle(self, *args, **options):
        with open(options['filename'][0], 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            first = True
            to_send = []
            to_send_trips = []

            for row in reader:
                if first:
                    first = False
                else:
                    dataowner, lineplanningnumber, journeynumber = row[0].split(':')
                    if self.last_row_date != row[1]:
                        split = row[1].split('-')
                        self.date = date(int(split[0]), int(split[1]), int(split[2]))
                    trip = Kv1Journey.find_from_realtime(dataowner, row[0], date=self.date)
                    if trip is None:
                        self.stdout.write("Not found: %s on %s " % (row[0], row[1]))
                    else:
                        cancelled = Kv17Change(dataownercode=trip.dataownercode, operatingday=self.date, line=trip.line, journey=trip)
                        cancelled.save()
                        cancelled.delete()
                        to_send.append(cancelled.to_xml())
                        to_send_trips.append(row[0])
                        print ("Restored: %s:%s:%s on %s" % (cancelled.dataownercode, cancelled.line.lineplanningnumber,
                                                             cancelled.journey.journeynumber, cancelled.operatingday))

                    if len(to_send) > 0 and len(to_send) % self.BATCH_SIZE == 0:
                        to_send, to_send_trips = self.send(to_send, to_send_trips)

            if len(to_send) > 0:
                to_send, to_send_trips = self.send(to_send, to_send_trips)

    def send(self, to_send, to_send_trips):
        self.stdout.write("Sending batch of %s" % self.BATCH_SIZE)
        start = datetime.now()
        success = self.pusher.push_message(to_send)
        self.stdout.write("Took %s seconds" % (datetime.now() - start).seconds)
        if not success:
            self.stdout.write("Failed to send batch! %s" % to_send_trips)
        to_send = []
        to_send_trips = []
        return to_send, to_send_trips