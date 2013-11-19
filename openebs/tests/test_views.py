from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import Client
from django.utils.unittest.case import TestCase
from kv1.models import Kv1Stop
from openebs.models import Kv15MessageStop, UserProfile
from openebs.tests.utils import TestUtils


class TestOpenEbsViews(TestCase):
    haltes = []

    @classmethod
    def setUpClass(cls):
        # Setup user and assign company
        cls.user = User.objects.create_user(username="test_view", password="test")
        cls.user.save()
        p = UserProfile(user=cls.user, company='HTM')
        p.save()

        # Setup stops
        h1 = Kv1Stop(pk=10, dataownercode='HTM', userstopcode='111', name="Om de hoek", location=Point(1, 1))
        h2 = Kv1Stop(pk=11, dataownercode='HTM', userstopcode='112', name="Hier", location=Point(1, 1))
        h1.save()
        h2.save()
        cls.haltes.append(h1)
        cls.haltes.append(h2)

    def setUp(self):
        self.client = Client()

    def test_active_stops_deleted_message(self):
        """
        Test that a deleted message doesn't show up in the list of stops that are active as per the AJAX view
        """
        msg1 = TestUtils.create_message_default(self.user)
        msg1.save()
        Kv15MessageStop(stopmessage=msg1, stop=self.haltes[0]).save()

        msg2 = TestUtils.create_message_default(self.user)
        msg2.save()
        Kv15MessageStop(stopmessage=msg2, stop=self.haltes[1]).save()

        result = self.client.login(username="test_view", password="test")
        self.assertTrue(result)
        resp = self.client.get('/bericht/haltes.json')

        # TODO Check response for deleted messages before and after