# Used for creating random data to use
import csv

with open('sample.csv', 'w', newline='') as csvfile:
    fieldnames = ['t', 'x']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerow({'t': '1', 'x': '10'})
    writer.writerow({'t': '2', 'x': '15'})
    writer.writerow({'t': '3', 'x': '30'})
    writer.writerow({'t': '3', 'x': '30'})
    writer.writerow({'t': '3', 'x': '30'})
    writer.writerow({'t': '3', 'x': '30'})
    writer.writerow({'t': '3', 'x': '30'})
    writer.writerow({'t': '3', 'x': '30'})
    writer.writerow({'t': '3', 'x': '30'})

