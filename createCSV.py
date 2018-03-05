# Used for creating random data to use
import csv
import random
import os


def createCSV():
    with open('sample.csv', 'w', newline='') as csvfile:
        fieldnames = ['times', 'Speed', 'RPM', 'GPS', 'Hill slope', 'Accelerometer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if os.stat('sample.csv').st_size == 0:
            writer.writeheader()
        writer.writerow({'times': '1',
            'Speed': str(random.randrange(0,10)),
            'RPM': str(random.randrange(10,20)),
            'GPS': str(random.randrange(20,30)),
            'Hill slope': str(random.randrange(30,40)),
            'Accelerometer': str(random.randrange(40,50))})

createCSV()
