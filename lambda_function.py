###################################################
#  --------------------pyCoWin--------------------
# pyCoWin is a simple automation script which processes
# the response from URL endpoint and trigger email whenever 
# something necessary is available to the registered users
# via email using AWS SES service.
# --------------------------------------------------
#####################################################
from botocore.vendored import requests
import json
import datetime
import logging
import dateutil.tz
import smtplib
from email.mime.text import MIMEText
from dict_repo import SEARCH_DICT
from aws_ses_client import aws_ses_client_send_mail

## Few important constants
STATUS_OK = 200
STATUS_NO = 400
MAIN_URL = "http://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?"
headers_dict = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"}


## setting logging level
logging.basicConfig(format='Time : %(asctime)s : Line: %(lineno)d - %(message)s', \
                    level = logging.DEBUG)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    # TODO implement
    run_cowin()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from pyCoWin!')
    }

def construct_url(district_id, date):
    """
    :param district_id = id of the district which forms "district_id" query param
    :param date = current date which forms "date" query param
    :return: The entire URL with all query params in place
    """
    return MAIN_URL + "district_id="+str(district_id)+"&date="+date
    
def fetch_necessary_info(centers):
    """
    :param centers: The centers as a json object, which is obtained as response from cowin api
    :return: The compiled info about the center having all the fields we are interested in
    """
    compiled_center_info = []
    for center in centers:
        condensed_center_info =  "Name: " + center['name'] + "\n" +"pincode: " + str(center['pincode']) + "\n"
        for session in center['sessions']:
            condensed_center_info = condensed_center_info + "Date: "+ str(session['date']) +" Capacity: "+ str(session['available_capacity']) + " Age Limit: "+ str(session['min_age_limit'])+"\n"
        compiled_center_info.append(condensed_center_info)
    return compiled_center_info    

def prepare_emails(stauts, center_name, center_info):
    """
    :param status: status of whether the response was success and has required centers' info
    :param name: name of the vaccine center
    :param center_info: compiled center info prepared from response
    :return The subject and body of the email to be sent
    """
    if stauts == 200:
        subject = "Covid vaccine now available in "+center_name+" for age group below 45 years"
        intro_msg = "The following centers are now open for the mentioned minimum age limit, please find the information below: "
        body_msg = intro_msg + "\n\n" + center_info
        return subject, body_msg
    else:
        subject = "No Covid vaccine centers available in " + center_name
        personal_msg = "Currently, no centers in "+center_name+" are available for booking vaccine for below 45 years age group."
        return subject, personal_msg     

def shoot_emails(msg, mails, subject):
    """
    :param msg: body of the mail as plain text
    :param mails: list containing email ids to which email has to be sent
    :param subject: subject of the mail to be sent
    """
    aws_ses_client_send_mail(msg, mails, subject)

def get_date():
    """
    return: Get today's date in DDMMYYYY format of IST timezone
    """
    print("getting date!!")
    # it will get the time zone 
    # of the specified location
    indian = dateutil.tz.gettz('Asia/Kolkata')
    x = datetime.datetime.now(tz=indian)
    reversed_date = (str(x).split(' ')[0].split('-'))
    reversed_date.reverse()
    date = ("-".join(reversed_date))
    print("time now: "+str(x))
    return str(date)
    
def get_centers_list(centers_list):
    """
    :param centers_list: List of centers as extracted from json response
    :return The list of filtered centers based on our criteria
    """
    centers_less_than_45= []
    for center in centers_list:
            for session in center['sessions']:
                if session['min_age_limit'] < 45:
                    if(session['available_capacity'] > 0):
                        centers_less_than_45.append(center)
    return centers_less_than_45
    
def run_cowin():
    """
    Main driver function, which hits url, processes response and shoots emails.
    """
    date = get_date()
    for district in SEARCH_DICT:
        district_info = SEARCH_DICT[district]
        url = construct_url(district_info['district'], date)
        logging.debug("Hitting URL: "+url)
        res = requests.get(url, headers=headers_dict)
        logging.info("Response received with status: {res.status_code}")
        if res.status_code == 200:
            logging.info("Processing the response further..")
            json_str = json.loads(res.text)
            centers_list = list(json_str["centers"])
            available_centers = get_centers_list(centers_list)
            if len(available_centers) > 0:
                logging.info("Required centers are available")
                compiled_center_info = fetch_necessary_info(available_centers)
                logging.debug("Compiled necessary center info")
                subject, msg = prepare_emails(STATUS_OK, district_info['name'], compiled_center_info)
            else:
                subject, msg = prepare_emails(STATUS_NO, district_info['name'], None)
            shoot_emails(msg, district_info['emails'], subject)
        else:
            logging.error("No response from the cowin servers..")
            logging.debug("Aborting..")

