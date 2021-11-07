import json
import requests
import boto3
from requests_aws4auth import AWS4Auth

def lambda_handler(event, context):
    print("EVENT -> ", event)
    
    client = boto3.client('lex-runtime')
    
    query = event["queryStringParameters"]['q']
    
    response_lex = client.post_text(
        botName='PhotoAlbum',
        botAlias="PhotoAlbum",
        userId="123",
        inputText= query
    )
    
    
    print("LEX RESPONSE -> ", response_lex)
    #print(inputText)
    print("This is my query -> ", query)
    
    labels = []
    if(response_lex["slots"]["slotOne"] is not None):
        labels.append(response_lex["slots"]["slotOne"])
    if(response_lex["slots"]["slotTwo"] is not None):
        labels.append(response_lex["slots"]["slotTwo"])
    #labels.append(event["currentIntent"]["slots"]["slotThree"])
    len(labels)
    print(labels)
    
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    host = 'https://search-photos-u2ytndgra4ucoxadjahxn3bs5m.us-east-1.es.amazonaws.com'
    index = 'photos'
    url = host + '/' + index + '/_search'
    headers = { "Content-Type": "application/json" }
    
    resp = []
    imageNameList = []
    for label in labels:
        print("Label is ", label)
        qry = label.upper()
    
        query = {
            "query": {
                "multi_match": {
                    "query": qry,
                    "fields": ["labels"]
                }
            }
        }
    
        r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
        #r = requests.get(url1, auth=awsauth, headers=headers)
    
        response_data = []
        hits = []
        response_data = r.json()
        print("Response data is ", response_data)
        hits = response_data["hits"]["hits"]
        print(hits)
        for hit in hits:
            objectKey = hit["_source"]["objectKey"]
            print(objectKey)
            if objectKey not in imageNameList:
                imageNameList.append(objectKey)
        #https://nyu-photo-album.s3.amazonaws.com/architecture.png
    print("ImageNameList is ", imageNameList)
    for imageName in imageNameList:
        url = "https://nyu-photo-album.s3.amazonaws.com/" + imageName
        resp.append(url)
    
    print("Imagelist is ", imageNameList)
    print("resp is ", resp)
    
    # response = {
    #         "dialogAction": {
    #             "type": "Close",
    #             "fulfillmentState": "Fulfilled",
    #             "message": {
    #                 "contentType": "PlainText",   
    #                 "content": json.dumps(resp)
    #             }
    #         }
    #     }
    # return response
    
    if not resp:
        return{
            'statusCode':200,
            "headers": {"Access-Control-Allow-Origin":"*"},
            'body': json.dumps('No Results Found')
        }
    else:
        return{
            'statusCode':200,
            "headers": {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Credentials":True,"Content-Type":"application/json"},
            'body': json.dumps(resp)
        }
        
    
