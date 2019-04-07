class Driver:

    def __init__(self,
                driver_id,
                num_riders,
                route=list()
                ):
        self.driver_id = driver_id #string
        self.num_riders = num_riders #riders is a list of ride_request objects
        self.route = route #route is a list of locations that the driver needs to visit. Each location should have an event associated with it e.g. dropoff, pickup, dropoff & pickup
        #example of adding to route list: self.route.append('Judge Hall', 'pickup') Should also have boolean about whether it's a pick up or start location

#loads a string and outputs a list of riders
def load(riders):
    if riders == 'EMPTY_STRING':
        return list()

    list_strs = riders.split(';')
    
    events = list()
    for list_str in list_strs:
        event_strs = list_str.split('&')
        phone_num = int(event_strs[0])
        location = event_strs[1]
        is_pickup = False
        if event_strs[2].lower() == 'true':
            is_pickup = True
        num_riders = int(event_strs[3])
        events.append((phone_num, location, is_pickup, num_riders))

    return events
        

def stringify(events):
    stringified = ''
    for event in events:
        stringified += str(event[0]) + '&' + str(event[1]) + '&' + str(event[2]) + '&' + str(event[3]) + ';'
    
    if len(stringified) == 0:
        return 'EMPTY_STRING'

    return stringified[:-1]