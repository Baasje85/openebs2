#from kv1.views import DataImportView
#from kv1.models import Kv1JourneyDate
# from openebs.views_baasje_new_1 import ChangeLineCancelCreateView
#
#
# from datetime import datetime, timedelta
#
# my_dict = {"Vandaag": 0, "Morgen": 0, "Overmorgen": 0}
# for i in range(0,3):
#     day = datetime.today() + timedelta(days=i)
#     date = day.strftime('%d-%m-%Y')
#     if i == 0:
#         my_dict["Vandaag"] = date
#     elif i == 1:
#         my_dict["Morgen"] = date
#     elif i == 2:
#         my_dict["Overmorgen"] = date
# #DAYS = tuple(zip(my_dict.keys(), my_dict.values())) #(werkt wel!!)
#
#
#
# x = ChangeLineCancelCreateView()
# DAYS = x.get_days()
#
# #print("qry from days-baasje: ", DAYS)
DAYS = []
