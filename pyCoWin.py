from botocore.vendored import requests
import json
import smtplib
from email.mime.text import MIMEText

def lambda_handler(event, context):
    # TODO implement
    run_cowin()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }




def fetch_necessary_info(center_info):
    condensed_center_info =  "Name: " + center_info['name'] + "\n" +"pincode: " + str(center_info['pincode']) + "\n"
    for session in center_info['sessions']:
        condensed_center_info = condensed_center_info + "Date: "+ str(session['date']) +" Capacity: "+ str(session['available_capacity']) + " Age Limit: "+ str(session['min_age_limit'])+"\n"
    return condensed_center_info    

def shoot_emails(compiled_center_info, receivers):
    # creates SMTP session 
    email = smtplib.SMTP('smtp.gmail.com', 587) 

    # TLS for security 
    email.starttls() 


    sender = 'sathu.sathvik@gmail.com'
    receivers = ['sathu.sathvik@gmail.com']


    port = 1025
    msg = MIMEText('The following centers are now open for the mentioned minimum age limit, please find the information below:' + "\n\n" + compiled_center_info)

    msg['Subject'] = 'Covid vaccine now available for people below 45 years Age'
    msg['From'] = 'sathu.sathvik@gmail.com'

    # authentication
    # compiler gives an error for wrong credential. 
    email.login("sathu.sathvik@gmail.com", "9980891626") 


    # sending the mail 
    email.sendmail(sender, receivers, msg.as_string()) 

    print("email sent successfully!!")
    # terminating the session 
    email.quit()
        
def run_cowin():


    url = "http://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id=265&date=02-05-2021"
    res = requests.get(url)
    print("got response!")

    if res.status_code == 200:
        print("response is successfull!")
        pretty_json = json.loads(res.text)
        centers_list = list(pretty_json["centers"])
        centers_less_than_45 = []
        centers_more_than_45 = []
        for center in centers_list:
            for session in center['sessions']:
                if session['min_age_limit'] < 45:
                    centers_less_than_45.append(center)
                else :
                    centers_more_than_45.append(center)
        personal_msg = "Centers providing vaccine for below 45 years age group: "+str(len(centers_less_than_45))
        shoot_emails(personal_msg,["sathu.sathvik@gmail.com"])
        if len(centers_less_than_45) > 0:          
            compiled_center_info = []
            for center in centers_less_than_45:
                compiled_center_info.append(fetch_necessary_info(center))
            compiled_center_info = "\n".join(compiled_center_info)
            print("compiled center info, shooting emails!!")
            receivers = ["sathu.sathvik@gmail.com", "susmitha.m20@gmail.com"]
            shoot_emails(compiled_center_info, receivers)






