import unittest
import datetime 
import tools
from PyQt5 import QtCore
from unittest.mock import Mock
from mock import patch
from datetime import datetime
from freezegun import freeze_time

class tools_test(unittest.TestCase):
    Fack_today = datetime(year=2023, month=5, day=5)
    Mock_datetime = Mock()
    Mock_datetime.datetime.today.return_value = Fack_today
    def test_changeDateMonth(self):
        input_date = datetime(2024,1,1)
        input_number = 1
        result = tools.changeDateMonth(input_date, input_number)
        self.assertEqual(result , datetime(2024,2,1))
    def test_QtDate2DateTime(self):
        input_date = QtCore.QDate(2024,2,1)
        result = tools.QtDate2DateTime(input_date)
        self.assertEqual(result, datetime(2024,2,1))
    def test_DateTime2String(self):
        input_date = datetime(2024,1,25)
        result = tools.DateTime2String(input_date)
        self.assertEqual(result, '2024-1-25')
    def test_check_monthDate(self):
        input_month = 5
        input_day = 28
        result = tools.check_monthDate(input_month,input_day)
        self.assertEqual(result, 28)
    def test_backWorkDays(self):
        input_date = datetime(2024,1,22)
        input_number = 1
        result = tools.backWorkDays(input_date,input_number)
        self.assertEqual(result,datetime(2024,1,19))
    def test_Total_with_Handling_fee_and_Tax(self):
        input_price = 100
        input_amount = 5
        result = tools.Total_with_Handling_fee_and_Tax(input_price,input_amount)
        self.assertEqual(result,(input_price * input_amount) + ((input_price * input_amount)*((0.1425)/100)))
    def test_Count_Stock_Amount(self):
        input_price = 100
        input_money = 50000
        result = tools.Count_Stock_Amount(input_money,input_price)
        self.assertEqual(result,(int)(input_money/(input_price*(100.1425/100))))
    @freeze_time("2023-05-05")
    def test_CheckFS_season(self):
        input_date = datetime(2023,5,1)
        result = tools.CheckFS_season(input_date)
        self.assertEqual(result, False) 
    @freeze_time("2023-05-05")
    def test_Have_MonthRP(self):
        input_date = datetime(2023,5,1)
        result = tools.Have_MonthRP(input_date)
        self.assertEqual(result, False) 
    @freeze_time("2023-05-01")
    def test_Have_DayRP(self):
        input_date = datetime(2023,5,1)
        result = tools.Have_DayRP(input_date)
        self.assertEqual(result, False) 


if __name__ == '__main__':
    unittest.main()
