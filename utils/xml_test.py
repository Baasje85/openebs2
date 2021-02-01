from doctest import Example

from django.test import TestCase
from lxml.doctestcompare import LXMLOutputChecker

__author__ = 'joel'


class XmlTest(TestCase):
    # Adapted from http://stackoverflow.com/questions/321795/comparing-xml-in-a-unit-test-in-python
    @staticmethod
    def assertXmlEqual(got, want):
        checker = LXMLOutputChecker()
        if not checker.check_output(want, got, 0):
            message = checker.output_difference(Example("", want), got, 0)
            raise AssertionError(message)

    @staticmethod
    def getCompareXML(file):
        with open(file) as f:
            return f.read()
