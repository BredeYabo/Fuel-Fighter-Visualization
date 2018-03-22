# Used for creating random data to use
import csv
import random
import os


def createCSV():
    with open('sample.csv', 'w', newline='') as csvfile:
        fieldnames = ['Time', 'BMS_State', 'BMS_PreChargeTimeout', 'BMS_LTC_LossOfSignal', 'BMS_OverVoltage', 'BMS_UnderVoltage', 'BMS_OverCurrent', 'BMS_OverTemp', 'BMS_NoDataOnStartup', 'BMS_Battery_Current', 'BMS_Battery_Voltage']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if os.stat('sample.csv').st_size == 0:
            writer.writeheader()
        writer.writerow({'Time': '1',
        "BMS_State": '1', # (0/1/2/3)
        "BMS_PreChargeTimeout": 'True', # Boolean
        "BMS_LTC_LossOfSignal": 'False',# Boolean
        "BMS_OverVoltage": 'True',# Boolean
        "BMS_UnderVoltage": 'False',# Boolean
        "BMS_OverCurrent": 'True',# Boolean
        "BMS_OverTemp": 'False',# Boolean
        "BMS_NoDataOnStartup": 'True',# Boolean
        "BMS_Battery_Current": str(random.randrange(10,20)),# int
        "BMS_Battery_Voltage": str(random.randrange(20,30))}) # int

createCSV()
