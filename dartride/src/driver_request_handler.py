import json
import hashlib
import boto3
from botocore.vendored import requests
from botocore.vendored.requests.auth import HTTPBasicAuth
import driver

def lambda_handler(event, context):
    # TODO implement
    # req = json.loads(str(event))
    # e = str(event['body'])
    # req = json.loads(str(e))
    # req = json.loads("{hello : world}")
    # two = 1 + 1
    
    req = json.loads(event['body'])
    action = req['action']
    if action == 'login':
        
        # Ensure username was submitted
        if not req["username"]:
            return {
                'statusCode': 403,
                "headers": {
                    'Access-Control-Allow-Origin' : '*',
                    'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Credentials' : True,
                    'Content-Type': 'application/json'
                },
                'body': json.dumps("must provide username")
            }

        # # Ensure username was submitted
        if not req["password"]:
            return {
                'statusCode': 403,
                "headers": {
                    'Access-Control-Allow-Origin' : '*',
                    'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Credentials' : True,
                    'Content-Type': 'application/json'
                },
                'body': json.dumps('must provide password')
            }
        username = req["username"]
        password = req["password"]
        
        # Query database for username
        dynamodb = boto3.client('dynamodb')
        

        
        # Ensure username exists and password is correct
        
        item = dynamodb.get_item(
            TableName='driver_login',
            Key={'driver_id':{'S':username}}
        )
        if 'Item' in item:
            item = item['Item']
            tablePass = item['password']['S']
            if tablePass == password:
                response = '{"success": true, "drivertoken": "' + item['driver_id']['S'] +'"}'
                return {
                    'statusCode': 200,
                    "headers": {
                        'Access-Control-Allow-Origin' : '*',
                        'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                        'Access-Control-Allow-Credentials' : True,
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps(response)
                }
            else:
                return {
                    'statusCode': 200,
                    "headers": {
                        'Access-Control-Allow-Origin' : '*',
                        'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                        'Access-Control-Allow-Credentials' : True,
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps('{"success": false}')
                }
        
        else:
            return {
                'statusCode': 200,
                "headers": {
                    'Access-Control-Allow-Origin' : '*',
                    'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Credentials' : True,
                    'Content-Type': 'application/json'
                },
                'body': json.dumps('{"success": false}')
            }
        
        
        
    elif action == 'gettasks':
        drivertoken = req["drivertoken"]
        
        
        dynamodb = boto3.client('dynamodb')
        item = dynamodb.get_item(
            TableName='driver_login',
            Key={'driver_id':{'S':drivertoken}}
        )
        
        
        
        
        if 'Item' in item:
            item = item['Item']
            driver_id = item['driver_id']['S']
            # generate the queue you wanna show to the driver from db
            
            item = dynamodb.get_item(
            TableName='driver_queue',
                Key={'driver_id':{'S':driver_id}}
            )['Item']
            
            queue = item['queue']['S']
            queue = driver.load(queue)
            seen = set()
            
            stop_idx = len(queue)
            
            
            for idx, ele in enumerate(queue):
                if ele[0] in seen:
                    stop_idx = idx + 1
                    break
                else:
                    seen.add(ele[0])
            
            queue = queue[:stop_idx]
            
            responseq = []
            for t in queue:
                d = {
                    "location" : t[1],
                    "phone" : t[0],
                    "riders" : t[3]
                }
                if t[2]:
                    d["action"] = "Pick Up"
                else:
                    d["action"] = "Drop Off"
                responseq.append(d)
            
            response = '{"success": true, "tasks": ' + str(responseq) +'}'
            response = response.replace("'", '"')
            return {
                'statusCode': 200,
                "headers": {
                    'Access-Control-Allow-Origin' : '*',
                    'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Credentials' : True,
                    'Content-Type': 'application/json'
                },
                'body': json.dumps(response)
            }
            
            return {
                'statusCode': 200,
                "headers": {
                    'Access-Control-Allow-Origin' : '*',
                    'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Credentials' : True,
                    'Content-Type': 'application/json'
                },
                'body': json.dumps('{"success": true}')
            }
        else:
            # invalid drivertoken
            return {
                'statusCode': 200,
                "headers": {
                    'Access-Control-Allow-Origin' : '*',
                    'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Credentials' : True,
                    'Content-Type': 'application/json'
                },
                'body': json.dumps('{"success": false}')
            }
    elif action == 'logoff':
        # does not have to be handled at the moment
        return {
            'statusCode': 200,
            "headers": {
                'Access-Control-Allow-Origin' : '*',
                'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Credentials' : True,
                'Content-Type': 'application/json'
            },
            'body': json.dumps(req)
        }
    elif action == 'completetask':
        drivertoken = req["drivertoken"]
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('driver_queue')
    
        
        
        res_driver = table.get_item(
            Key={'driver_id': drivertoken}
        )

        res_driver = res_driver['Item']

        dq = driver.load(res_driver['queue'])
        
        total_queue_count = int(res_driver['num_passengers'])
        
        elt = dq[0]
        
        dropoff_count = 0
        if not elt[2]:
            dropoff_count = int(elt[3])
        
        ret_queue = dq[1:]
        
        try:
            next_stop = dq[1]
            if next_stop[2]: #next stop is a pickup
                next_phone_num = next_stop[0]
                send_notification(next_phone_num)
        except IndexError:
            pass
        
    
        #if pick up update the variable
        rider_tab = dynamodb.Table('rider_queue')
        if elt[2]:
            rider_tab.update_item(
                Key={
                    'phone_number': int(elt[0])
                },
                UpdateExpression="SET request_status = :s",
                ExpressionAttributeValues={
                    ':s': 1
                },
                ReturnValues="UPDATED_NEW"
            )
        else:
            rider_tab.delete_item(
                Key={'phone_number': int(elt[0])}
            )
            
        table.update_item(
            Key={'driver_id': drivertoken},
            UpdateExpression="SET num_passengers=:p, queue=:q",
            ExpressionAttributeValues={
                ':p': (total_queue_count - dropoff_count),
                ':q': driver.stringify(ret_queue)
            },
            ReturnValues="UPDATED_NEW"
        )
        
        return {
            'statusCode': 200,
            "headers": {
                'Access-Control-Allow-Origin' : '*',
                'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Credentials' : True,
                'Content-Type': 'application/json'
            },
            "body": json.dumps(req)
        }
    else:
        return {
            'statusCode': 200,
            "headers": {
                'Access-Control-Allow-Origin' : '*',
                'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Credentials' : True,
                'Content-Type': 'application/json'
            },
            "body": json.dumps(event)
        }

def send_notification(phone_number):
    twilio_sid = 'AC5ccb2e64b0498a6d299fcdc60bf86d23'
    twilio_auth = '312d31c6b1b019a87710f310bb6ecaa3'
    twilio_url = 'https://api.twilio.com/2010-04-01/Accounts/' + twilio_sid + '/Messages'

    auth = HTTPBasicAuth(twilio_sid, twilio_auth)

    values = {
        'Body': "Your driver is on the way. Get ready to be picked up!",
        'From': '+16148086615',
        'To': '+1' + str(phone_number)
    }

    requests.post(twilio_url, data=values, auth=auth)