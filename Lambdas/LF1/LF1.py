import json
import urllib.parse
import requests
import boto3
from requests_aws4auth import AWS4Auth 

print('Loading function')

s3 = boto3.client('s3')

credentials = boto3.Session().get_credentials()
print(credentials.token)
print(credentials.access_key)
print(credentials.secret_key)

def detect_labels(photo, bucket):

    client=boto3.client('rekognition')
    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
        MaxLabels=10)
    print('Detected labels for ' + photo) 
    print("Label response is ", response)   
    label_list = []
    for label in response['Labels']:
        label_list.append(label['Name'].upper())
        """
        print ("Label: " + label['Name'])
        print ("Confidence: " + str(label['Confidence']))
        print ("Instances:")
        for instance in label['Instances']:
            print ("  Bounding box")
            print ("    Top: " + str(instance['BoundingBox']['Top']))
            print ("    Left: " + str(instance['BoundingBox']['Left']))
            print ("    Width: " +  str(instance['BoundingBox']['Width']))
            print ("    Height: " +  str(instance['BoundingBox']['Height']))
            print ("  Confidence: " + str(instance['Confidence']))
            print()
        print ("Parents:")
        for parent in label['Parents']:
            print ("   " + parent['Name'])
        print ("----------")
        print ()
        """
    #return len(response['Labels'])
    return label_list


def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))
    print("Event is ", event)
    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    photo = event['Records'][0]['s3']['object']['key']
    print(photo)
    print(bucket)
    timestamp = event['Records'][0]["eventTime"]
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    metaresponse = s3.head_object(Bucket=bucket, Key=key)
    print("META-DATA: ", metaresponse)
    
    if metaresponse["Metadata"]:
        customLabels = (metaresponse["Metadata"]["customlabels"]).split(",")
    
    
    #print("CUSTOM - LABELS -> ", customLabels)  # Gets Custom Labels
    #print("Bucket name is ", bucket)
    #print("Photo name is ", photo)
    label_names = detect_labels(photo,bucket)
    
    if metaresponse["Metadata"]:
        for c_labels in customLabels:
            c_labels = c_labels.strip()
            c_labels = c_labels.upper()
            if c_labels not in label_names:
                label_names.append(c_labels)
            
            
    print("FINAL LABELS -> ", label_names)  #appends custom labels to final labels
    
    input_json = {}
    input_json["objectKey"] = photo
    input_json["bucket"] = bucket
    input_json["createdTimestamp"] = timestamp
    input_json["labels"] = label_names
    print(input_json)
    
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        print("CONTENT TYPE: " + response['ContentType'])
        
        url = "https://search-photos-u2ytndgra4ucoxadjahxn3bs5m.us-east-1.es.amazonaws.com/photos/0"
        headers = {"Content-Type": "application/json"}
        
        
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 'us-east-1', 'es', session_token=credentials.token)
        print("AWSAuth ", awsauth)
        data_as_str = json.dumps(input_json).encode("utf-8")
        r = requests.post(url, auth=awsauth, headers=headers, data=data_as_str)
        print(r.text)
        
    
        
        response = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': 'https://www.example.com',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps('Hello from Lambda!')
        }
        
        return response
        
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e


#Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#PDX-License-Identifier: MIT-0 (For details, see https://github.com/awsdocs/amazon-rekognition-developer-guide/blob/master/LICENSE-SAMPLECODE.)

"""
def main():
    photo=''
    bucket=''
    label_count=detect_labels(photo, bucket)
    print("Labels detected: " + str(label_count))


if __name__ == "__main__":
    main()

"""