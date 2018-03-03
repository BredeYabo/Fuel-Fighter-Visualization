import pandas as pd
import io
import boto3

BUCKET_NAME = 'ff-fipy-csv'
KEY = 'sample.csv'

s3 = boto3.resource('s3')
# s3_client = boto3.client('s3')

s3.Bucket(BUCKET_NAME).download_file(KEY, 'sample.csv')

# Example usage
# pd_read_csv_s3("s3://my_bucket/my_folder/file.csv", skiprows=2)
