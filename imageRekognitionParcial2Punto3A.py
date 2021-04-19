import json
from urllib.parse import unquote_plus
import boto3
from decimal import Decimal
import urllib.request as urlreq
import cv2

s3 = boto3.client('s3')
client = boto3.client('rekognition', 'us-east-1')
dynamoDB = boto3.resource('dynamodb','us-east-1')

def lambda_handler(event, context):
    # TODO implement
    
    
    
    ### New Bucket
    newBucket='bucketresultsfenix'
    
    ###Get the name bucket
    nameBucket=event['Records'][0]['s3']['bucket']['name']
    
    ### Get Time
    time = event['Records'][0]['eventTime']
    
    ###Get the name of event
    ###nameObject=(unquote_plus(event['Records'][0]['s3']['object']['key']).split('/')[-1]).split('.')[0]
    nameObject=(unquote_plus(event['Records'][0]['s3']['object']['key']).split('/')[-1])
    
    key=unquote_plus(event['Records'][0]['s3']['object']['key'])
    
    
    ### Download path
    download_path = '/tmp/{}'.format(nameObject)
    
    ### Download path
    s3.download_file(nameBucket,key,download_path)
    
    # Read image
    image = cv2.imread(download_path)
    print('shape:',image.shape)
    
    ### Upload path
    ###upload_path = '/tmp/{}'.format(newName)
    # upload_path= key.replace(key.split('/')[-1],newName)
    
    print('nameBucket: ',nameBucket)
    print('time: ',time)
    print('nameObject: ',nameObject)
    print('key: ',key)
    # Use of Rekognition with the object event
    response = client.detect_labels(
        Image={
            'S3Object': {
                'Bucket': nameBucket,
                'Name': key
            }
        }
    
    )
    print(response)
    
    
    table = dynamoDB.Table('images')
    
    
    # Creation of Dict and List
    newList=[]
    dictImages={}
    auxDict=response['Labels']
    # Add keys to the Dict
    for data in auxDict:
      dictImages={}
      dictImages['category'] = nameObject
      dictImages['subCategory'] = data['Name']
      dictImages['ruta'] = key
      dictImages['metadata'] = data
      newList.append(dictImages)
      if (dictImages['metadata']['Instances']!=[]):
        height = newList[5]['metadata']['Instances'][0]['BoundingBox']['Height']
        left = newList[5]['metadata']['Instances'][0]['BoundingBox']['Left']
        top = newList[5]['metadata']['Instances'][0]['BoundingBox']['Top']
        width = newList[5]['metadata']['Instances'][0]['BoundingBox']['Width']
        ## height
        alto = image.shape[0]
        ## width
        ancho = image.shape[1]
        ## Image Result
        imageResult = image[int(alto*top):int(alto*top+alto*height),int(ancho*left):int(ancho*left+ancho*width)]
        
        cv2.imwrite('imagenResult.jpg',imageResult)
        ### Upload image
        upload_path= 'category={}/subCategory={}/{}.j'.format(nameObject,data['Name'],data['Name'])
        s3.upload_file('imagenResult.jpg',nameBucket,upload_path)
        
        print('nueva imagen')
    
    #Parse float
    ddb_data = json.loads(json.dumps(newList), parse_float=Decimal)
    
    count = 0
    for data in ddb_data:
        count+=1
        print('inserting...',count)
        table.put_item(Item = data)
    print('End')
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
