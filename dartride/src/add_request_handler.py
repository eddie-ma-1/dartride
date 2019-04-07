#adds the request to the ride_request database
#sends a message back to the user confirming their ride request with an estimate for their spot in line
#runs routing algorithm and generates new queue for drivers with request
#stores queue in amazon s3 bucket

import json
import boto3
from ride_request import Ride_Request
import engine
import driver
import datetime
from botocore.vendored import requests
from botocore.vendored.requests.auth import HTTPBasicAuth

#TODO: check if phone number is already in the rider_queue


def lambda_handler(event, context):
    params = None
    try:
        params = event['queryStringParameters']
        assert(isinstance(params, dict))

    except (KeyError, AssertionError):
        return {
            'statusCode' : 200,
            "headers": {
                'Access-Control-Allow-Origin' : '*',
                'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Credentials' : True,
                'Content-Type': 'application/json'
            },
            'body': json.dumps('No paramaters found!')
        }
    #make sure the post request contains the required fields.
    validate = validate_post(params)
    if len(validate) != 0:
        return {
            'statusCode' : 200,
            "headers": {
                'Access-Control-Allow-Origin' : '*',
                'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Credentials' : True,
                'Content-Type': 'application/json'
            },
            'body': json.dumps(validate)
        } 

    req = create_ride_request(params)

    pair_info = pair_rider(req)

    req.driver_id = pair_info[1].driver_id

    add_to_ride_requests(req)

    add_to_rider_queue(req)

    next_in_line = update_driver_queue(req, pair_info[2], pair_info[3])

    send_confirmation_text(req.phone_number, next_in_line)

    return {
        'statusCode': 200,
        "headers": {
            'Access-Control-Allow-Origin' : '*',
            'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Credentials' : True,
            'Content-Type': 'application/json'
        },
        'body': json.dumps('Completed successfully!')
    }

#TODO: Add location checking
def validate_post(params):
    response = ''
    string_param_keys = ['student_ids', 'pickup_location', 'dropoff_location', 'driver_notes']

    for param_key in string_param_keys:
        try:
            params[param_key]
            if param_key != string_param_keys[3]: #driver notes can be empty.
                assert(len(params[param_key]) > 0)
        except (KeyError, AssertionError):
            response += 'missing ' + param_key + ' parameter! '

    try:
        int(params['phone_number'])
    except (KeyError, ValueError):
        response += 'phone number is missing or is not a number! '

    if (len(response) != 0):
        return response

    student_ids = params['student_ids'].split(',')

    if (len(student_ids) >  3):
        response += 'too many student ids. max riders is 3. '
        return response

    for id in student_ids:
        if not isValidStudentID(id):
            response += 'one or more student ids are invalid. '
            return response

    return response

#generates a ride request based on the ride_request class
def create_ride_request(params):
    print('started ride request creation.')
    current_time = datetime.datetime.now()
    request_time = int(str(current_time.date()).replace('-', '') + (str(current_time.time()).split('.', 1)[0].replace(':', '')))

    student_ids = list()


    student_ids = params['student_ids'].split(',')

    driver_notes = params['driver_notes']

    if len(driver_notes) == 0:
        driver_notes = 'EMPTY_STRING'

    
    return Ride_Request(
        phone_number        = int(params['phone_number']),
        student_ids         = student_ids,
        request_status      = 0,
        pickup_location     = params['pickup_location'],
        dropoff_location    = params['dropoff_location'],
        request_time        = request_time,
        pickup_time         = -1,
        dropoff_time        = -1,
        cancellation_time   = -1,
        driver_notes        = driver_notes,
        rider_feedback      = 'EMPTY_STRING'
    )


def add_to_ride_requests(ride_req):
    dynamodb = boto3.client('dynamodb')

    
    dynamodb.put_item(
        TableName='ride_requests', 
        Item={
            'phone_number': {'N': str(ride_req.phone_number)},
            'request_time': {'N': str(ride_req.request_time)},
            'student_ids': {'SS': ride_req.student_ids},
            'request_status': {'N': str(ride_req.request_status)},
            'pickup_location': {'S': ride_req.pickup_location},
            'dropoff_location': {'S': ride_req.dropoff_location},
            'pickup_time': {'N': str(ride_req.pickup_time)},
            'dropoff_time': {'N': str(ride_req.dropoff_time)},
            'cancellation_time': {'N': str(ride_req.cancellation_time)},
            'driver_notes': {'S': ride_req.driver_notes},
            'rider_feedback': {'S': ride_req.rider_feedback}
        }
    )

def add_to_rider_queue(ride_req):
    dynamodb = boto3.client('dynamodb')

    dynamodb.put_item(
        TableName='rider_queue',
        Item={
            'phone_number': {'N': str(ride_req.phone_number)},
            'request_time': {'N': str(ride_req.request_time)},
            'request_status': {'N': str(ride_req.request_status)},
            'pickup_location': {'S': ride_req.pickup_location},
            'dropoff_location': {'S': ride_req.dropoff_location},
            'pickup_time': {'N': str(ride_req.pickup_time)},
            'dropoff_time': {'N': str(ride_req.dropoff_time)},
            'cancellation_time': {'N': str(ride_req.cancellation_time)},
            'driver_notes': {'S': ride_req.driver_notes},
            'rider_feedback': {'S': ride_req.rider_feedback},
            'driver_id': {'S': ride_req.driver_id}
        }
    )
    

def update_driver_queue(ridereq, pickup, dropoff):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('driver_queue')
    
    driv = table.get_item(
        Key={
            'driver_id': ridereq.driver_id
        }
    )

    driv = driv['Item']
    ride_stops = driver.load(driv['queue'])
    ride_cur_pass = int(driv['num_passengers'])
    ride_stops.insert(pickup + 1, (ridereq.phone_number, ridereq.pickup_location, True, len(ridereq.student_ids)))
    ride_stops.insert(dropoff + 2, (ridereq.phone_number, ridereq.dropoff_location, False, len(ridereq.student_ids)))
    
    next_in_line = (int(ride_stops[0][0]) == int(ridereq.phone_number))
    
    table.update_item(
        Key={
            'driver_id': ridereq.driver_id
        },
        UpdateExpression="SET num_passengers=:p, queue=:q",
        ExpressionAttributeValues={
            ':p': (ride_cur_pass + len(ridereq.student_ids)),
            ':q': driver.stringify(ride_stops)
        },
        ReturnValues="UPDATED_NEW"
    )
    
    return next_in_line
    


    

def send_confirmation_text(phone_number, next_in_line):
    twilio_sid = 'AC5ccb2e64b0498a6d299fcdc60bf86d23'
    twilio_auth = '312d31c6b1b019a87710f310bb6ecaa3'
    twilio_url = 'https://api.twilio.com/2010-04-01/Accounts/' + twilio_sid + '/Messages'

    auth = HTTPBasicAuth(twilio_sid, twilio_auth)
    
    text_message_body = "Your saferide request has been submitted! Text OK to cancel your request."
    
    if next_in_line:
        text_message_body = "You're next in line. Get ready to be picked up!"
    
    values = {
        'Body': text_message_body,
        'From': '+16148086615',
        'To': '+1' + str(phone_number)
    }

    requests.post(twilio_url, data=values, auth=auth)

def pair_rider(ridereq):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('driver_queue')
    
    #scan table for drivers
    response = table.scan()
    d_list = []

    for driv in response['Items']:
        d_id = driv['driver_id']
        d_np = driv['num_passengers']
        d_queue = driver.load(driv['queue'])
        d_list.append(driver.Driver(d_id, d_np, d_queue))
    
    return engine.BetterEngine(d_list, [ridereq])

        

#checks against list of valid drop-off and pick-up points
def isValidLocation(location):
    return True

#in the future match the student id against a database. For now, just check to see if it meets a few criteria.
def isValidStudentID(student_id):
    return len(student_id) == 7 and student_id.isalnum() and student_id[0].isalpha()
