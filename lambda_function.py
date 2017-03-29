from __future__ import print_function
import urllib2
import json

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
        "card": {
            "type": "Simple",
            "title": title,
            "content": output
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Alexa Capital Bikeshare skill. " \
                    "You can ask me how many bikes are at station 31,000" 
    reprompt_text = "Please ask me for a station update."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Have a nice day and thank you for using Capital Bike share! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))
        
def get_system_status():
    session_attributes = {}
    card_title = "Capital Bikeshare System Status"
    reprompt_text = ""
    should_end_session = False

    url = "https://gbfs.capitalbikeshare.com/gbfs/en/system_information.json"
    response = urllib2.urlopen(url)
    cabi_system_status = json.load(response)
    cabi_system_status = cabi_system_status["data"]

    speech_output = ("Capital City Bikeshare is operated by " + cabi_system_status["operator"] +
                     " Customer service can be reached by email at " + cabi_system_status["email"] +
                     " or by telephone at " + cabi_system_status["phone_number"] )

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_bikes(intent):
    session_attributes = {}
    card_title = "Capital Bikeshare Station Status"
    speech_output = "I'm sorry, that station does not exist. Please try again"
    reprompt_text = "You can ask how many bikes are at station 31,000"
    should_end_session = False
    
    station_name1 = intent["slots"]["Station"]["value"]
    station_code = int(station_name1)
    
    url = "https://gbfs.capitalbikeshare.com/gbfs/en/station_information.json"
    url2 = "https://gbfs.capitalbikeshare.com/gbfs/en/station_status.json"
    response = urllib2.urlopen(url)
    response2 = urllib2.urlopen(url2)
    station_name = json.load(response)
    cabi_station_status = json.load(response2)

    cabi_station_status = cabi_station_status["data"]
    station_information = station_name["data"]

    valid_stations = []

    for valid in station_information['stations']:
        valid_stations.append(int(valid["short_name"]))

    if station_code in valid_stations:
        for names in station_information['stations']:
            if names['short_name'] == '{}'.format(station_code):
                get_station_name = names["name"]
                get_station_id = names["station_id"]
                lat = names["lat"]
                lon = names["lon"]
                region = names["region_id"]
                capacity = names["capacity"]
                short_name = names["short_name"]

        for station in cabi_station_status['stations']:
            if station['station_id'] == '{}'.format(get_station_id):
                bikes = (station['num_bikes_available'])
                docks = (station['num_docks_available'])
                total = ((station['num_bikes_available']) +
                    (station['num_bikes_disabled']) +
                    (station["num_docks_available"]))
                disabled = (station['num_bikes_disabled'])
        
        speech_output = ("There are {} bikes available and {} empty docks to check in a bike".format(bikes, 
        docks)) 
        reprompt_text = ""
       
    return build_response(session_attributes, build_speechlet_response(
           card_title, speech_output, reprompt_text, should_end_session))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])

def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()

def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]
    
    if intent_name == "GetInformation":
        return get_system_status()
    elif intent_name == "GetBikes":
        return get_bikes(intent)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Main handler ------------------

def lambda_handler(event, context):
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

 
    if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.XXX-XXX-XXX-XXX-XXX"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
