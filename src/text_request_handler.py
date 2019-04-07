import boto3
import json
import driver

#TODO: Update Cancellation Time

def lambda_handler(event, context):
    text = event['Body']
    phone_number = event['From'][-10:]

    #invalid text
    if text != 'OK':
        return

    #first step is to delete the item from the queue
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('rider_queue')
    
    #get rider reqs
    ride_reqs = table.get_item(
        Key={
            'phone_number': int(phone_number)
        }
    )

    if 'Item' not in ride_reqs:
        return '<?xm1l version=\"1.0\" encoding=\"UTF-8\"?>'\
    '<Response><Message>You do not have an active request.</Message></Response>'
        
    ride_req = ride_reqs['Item']
    if int(ride_req['request_status']) != 0:    
        return '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'\
        '<Response><Message>Your request is in progress. It cannot be cancelled at this point.</Message></Response>'
        
    req_time = int(ride_req['request_time'])
    req_driver = ride_req['driver_id']

    #delete item from rider queue
    response = table.delete_item(
        Key={
            'phone_number': int(phone_number)
        })
    
    #if driver hasn't been assigned
    if req_driver == 'EMPTY_STRING':
        return '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'\
        '<Response><Message>Your request has been cancelled.</Message></Response>'

    table = dynamodb.Table('driver_queue')
    
    res_driver = table.get_item(
        Key={
            'driver_id': req_driver
        }
    )

    if 'Item' not in res_driver:
        return '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'\
        '<Response><Message>Your request is in progress. It cannot be cancelled at this point.</Message></Response>'
    
    res_driver = res_driver['Item']
    driver_queue = res_driver['queue']

    eve = driver.load(driver_queue)
    cleaned_events = []
    num_in_req = 0
    for x in eve:
        if (x[0] != int(phone_number)):
            cleaned_events.append(x)
        else:
            num_in_req = int(x[3])
            

    stringed_queue = driver.stringify(cleaned_events)

    table.update_item(
        Key={
            'driver_id': req_driver
        },
        UpdateExpression="SET num_passengers=:p, queue=:q",
        ExpressionAttributeValues={
            ':p': (int(res_driver['num_passengers']) - num_in_req),
            ':q': stringed_queue
        },
        ReturnValues="UPDATED_NEW"
    )

    table = dynamodb.Table('ride_requests')
    
    table.update_item(
        Key={
            'phone_number': int(phone_number),
            'request_time': req_time
        },
        UpdateExpression="SET request_status = :s",
        ExpressionAttributeValues={
            ':s': 3
        },
        ReturnValues="UPDATED_NEW"
    )


    return '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'\
    '<Response><Message>Your request has been cancelled.</Message></Response>'
