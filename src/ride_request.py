class Ride_Request:

    def __init__(self,
                phone_number,       #int
                student_ids,        #list of student ids in ride request
                request_status,     #status of request represented by int. 0: request in queue 1: request in progress 2: request completed 3: request cancelled
                pickup_location,    #stored as a string probably?? maybe an enum idk yet most likely a string tho
                dropoff_location,   #same as pickup location
                request_time,       #stored as a integer in the format YYYYMMDDHHMMSS
                pickup_time,        #same as request_time
                dropoff_time,       #same as request_time
                cancellation_time,  #same as request_time
                driver_notes,       #specific notes for driver stored as string
                rider_feedback,
                driver_id='EMPTY_STRING'):    #feedback from rider stored as string
        self.phone_number = phone_number
        self.student_ids = student_ids
        self.request_status = request_status
        self.pickup_location = pickup_location
        self.dropoff_location = dropoff_location
        self.request_time = request_time
        self.pickup_time = pickup_time
        self.dropoff_time = dropoff_time
        self.cancellation_time = cancellation_time
        self.driver_notes = driver_notes
        self.rider_feedback = rider_feedback
        self.driver_id = driver_id