#!/usr/bin/env python

"""
Here we use the Rekognition, DynamoDB, and S3 boto3 clients to recognise the number
and record it for posterity. We copy rather than move the image when renaming in 
order not to stop aws s3 sync from working on the client side
"""

import boto3
import json
import re
import os

###
# Getting our environment variables
###
# Our DynamoDB table
# dynamodb_table = os.environ['dynamodb_table']

### Our Regex to match good strings
drawing_id_regex='^[0-9]-[0-9]{4}/?[0-9]?$'

# our boto3 rekognition client
rekognition_client=boto3.client('rekognition')
dynamodb_client=boto3.client('dynamodb')
s3=boto3.resource('s3')

def find_number(bucket, key):
    # The bottom-most, rightmost number that matches the regex is the
    # number for which the bottom-right corner is furthest from the
    # top-left of the image. So we find the x and y coords and select
    # the maximum of sqrt(x^2 + y^2)=> max(x^2 + y^2)
    # The algorithm could be wrong if we aren't doing 0,0 at top-left,
    # but I think we are

    # First, we run ocr on the image
    response = rekognition_client.detect_text(
        Image={
            "S3Object": {
		"Bucket": bucket,
		"Name": key,
            }
        }
    )
    winner='0-0000'
    winner_distance_squared=0.0
    print(response)
    for dt in response['TextDetections']:
        print(dt)
        vacuumed_dt = dt['DetectedText'].replace(" ","") # in case we erroneously see spaces
        if re.match(drawing_id_regex, vacuumed_dt):
            bottom_y = dt['Geometry']['BoundingBox']['Height'] + dt['Geometry']['BoundingBox']['Top']
            right_x = dt['Geometry']['BoundingBox']['Width'] + dt['Geometry']['BoundingBox']['Left']
            distance_squared = bottom_y**2 + right_x**2

            if distance_squared > winner_distance_squared:
                winner_distance_squared = distance_squared
                winner = vacuumed_dt
    if winner == '0-0000':
        return False
    return winner


def lambda_handler(event, context):
    """
    Main Lambda handler
    """
    print json.dumps(event)
    # our incoming event is the S3 put event notification
    s3_message = event
    # get the object key and bucket name
    key = s3_message['Records'][0]['s3']['object']['key']
    bucket = s3_message['Records'][0]['s3']['bucket']['name']
    source_object = {
        'Bucket' : bucket,
        'Key' : key
        }
    
    # first we use Rekognise to find the bottommost, rightmost, number that matches the regex
    new_filename = find_number(bucket, key)
    if new_filename:
        print("Detected Label!")
        print(new_filename)
        new_filename = 'output/' + new_filename.replace("/","_") + '.' + key.split('.')[-1] # we can't have / in filenames
        print(new_filename)
    else:
        print("No ID detected!")
        new_filename = key.replace('landingzone','undetected')
    s3.meta.client.copy(source_object, bucket, new_filename)
