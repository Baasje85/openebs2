import logging
from StringIO import StringIO
from gzip import GzipFile
from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.conf import settings
from django.db import transaction
from django.utils.timezone import now
import zmq
from openebs.models import Kv15Stopmessage, MessageStatus

__author__ = 'joel'


class Command(BaseCommand):
    log = logging.getLogger('openebs.kv8verify')

    def handle(self, *args, **options):
        print 'Setting up a ZeroMQ SUB: %s\n' % (settings.GOVI_VERIFY_FEED)
        context = zmq.Context()
        sub = context.socket(zmq.SUB)
        sub.connect(settings.GOVI_VERIFY_FEED)
        sub.setsockopt(zmq.SUBSCRIBE, settings.GOVI_VERIFY_SUB)

        while True:
            multipart = sub.recv_multipart()
            try:
                content = GzipFile('','r',0,StringIO(''.join(multipart[1:]))).read()
            except:
                content = ''.join(multipart[1:])
            self.recvPackage(content)

    def recvPackage(self, content):
        print "Got content"
        for line in content.split('\r\n')[:-1]:
            if line[0] == '\\':
                    # control characters
                if line[1] == 'G':
                    label, name, subscription, path, endian, enc, res1, timestamp, _ = line[2:].split('|')
                elif line[1] == 'T':
                    type = line[2:].split('|')[1]
                elif line[1] == 'L':
                    keys = line[2:].split('|')
            else:
                row = {}
                values = line.split('|')
                for k,v in map(None, keys, values):
                    if v == '\\0':
                        row[k] = None
                    else:
                        row[k] = v
                self.log.debug("Got new message of type %s" % type)
                if type == 'GENERALMESSAGEUPDATE':
                    self.processMessage(row)
                elif type == 'GENERALMESSAGEDELETE':
                    self.processDelMessage(row)
                else:
                    self.log.warning("Don't have a handler for messages of type %s" % type)

    @transaction.commit_on_success
    def processMessage(self, row):

        msg, created = Kv15Stopmessage.objects.get_or_create(dataownercode=row['DataOwnerCode'], messagecodedate=row['MessageCodeDate'],
                                       messagecodenumber=row['MessageCodeNumber'], defaults={ 'user' : self.get_user()})
        self.log.info("Setting status confirmed for message:  %s" % msg)
        msg.status = MessageStatus.CONFIRMED
        if created:
            self.log.info("Creating new message which wasn't in DB: %s" % msg)
            msg.messagecontent = row['MessageContent']
            msg.messagestarttime = row['MessageStartTime']
            msg.messageendtime = row['MessageEndTime']
            msg.messagetimestamp = row['MessageTimeStamp']
            msg.messagetype = row['MessageType']
            msg.messagedurationtype = row['MessageDurationType']
            msg.reasontype = row['ReasonType']
            msg.subreasontype = row['SubReasonType']
            msg.reasoncontent = row['ReasonContent']
            msg.effecttype = row['EffectType']
            msg.subeffecttype = row['SubEffectType']
            msg.effectcontent = row['EffectContent']
            msg.measuretype = row['MeasureType']
            msg.submeasuretype = row['SubMeasureType']
            msg.measurecontent = row['MeasureContent']
            msg.advicetype = row['AdviceType']
            msg.subadvicetype = row['SubAdviceType']
            msg.advicecontent = row['AdviceContent']
        msg.save()

    @transaction.commit_on_success
    def processDelMessage(self, row):
        try:
            msg = Kv15Stopmessage.objects.get(dataownercode=row['DataOwnerCode'], messagecodedate=row['MessageCodeDate'],
                                       messagecodenumber=row['MessageCodeNumber'])
            msg.status = MessageStatus.DELETE_CONFIRMED
            msg.isdeleted = True
            msg.messageendtime = now()
            msg.save()
            self.log.error("Confirmed deletion of message: %s" % msg)
        except Kv15Stopmessage.DoesNotExist:
            self.log.error("Tried to delete message that doesn't exist: %s" % row)

    def get_user(self):
        return User.objects.get_or_create(username="kv8update")[0]


