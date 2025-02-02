from requests import post
from config import *
from lib.mods.firemod import client, has_key, document
from lib.mods.timemod import dt
from sys import argv
from lib.log import Log

logdata = Log('mods/sms.py')
print = logdata.print

PAYDAY_TEXT = "DESICARS: Hi. It's time to pay for the rental car. Please send a confirmation via TG t.me/Desi_rental_cars after making \
the payment. Thank you!"
CHANGE_OIL_TEXT = "DESICARS: Hi. It's time to change the oil in the car. Please come to the office to take care of this. Thank you!"
INSURANCE_TEXT = "DESICARS: Hi. It's time to renew the car insurance. Please send me the new policy via TG t.me/Desi_rental_cars once \
it's ready. Thank you!"
LATEPAYMENT_TEXT = "DESICARS: Hi! Payment was due 3 days ago. Confirm via TG: t.me/Desi_rental_cars after payment. Debt: ${debt}. Late \
fee in 2 days."
REGISTRATION_TEXT = "DESICARS: Hi. It's time to renew the car registration. Please visit the office to complete this. Thank you!"

def send_sms(phone: str, text: str):
    if '--no-sms' not in argv:
        # post(
        #     INFOBIP_URL, # use https://######.api.infobip.com/sms/2/text/advanced
        #     json={
        #         'messages':
        #             [
        #                 {
        #                     'destinations': [{'to': phone}],
        #                     'from': INFOBIP_PHONE,
        #                     'text': text
        #                 }
        #             ]
        #         },
        #     headers={
        #         'Authorization': INFOBIP_TOKEN,
        #         'Accept': 'application/json',
        #         'Content-Type': 'application/json'
        #     }
        # )
        print(f'send SMS to phone {phone}.')
    else:
        print('SMS not sent because of "--no-sms" flag.')
    

def add_inbox(db: client, phone: str, text: str, contract_name: str, renter: str):
    phone = phone.replace('(', '').replace('+', '').replace(')', '').replace('-', '')
    now = dt.now()
    
    if '--no-sms' not in argv:
        inboxes: list[document] = db.collection('InboxSMS').get()
        for inbox in inboxes:
            inbox_dict: dict = inbox.to_dict()
            if has_key(inbox_dict, 'ContractName'):
                if inbox_dict['ContractName'] == contract_name:
                    db.collection('InboxSMS').document(inbox.id).update({'changed_time': now})
                    db.collection('InboxSMS').document(inbox.id).collection('messages').add({
                        'created_time': now,
                        'is_our': True,
                        'readed': True,
                        'message': text,
                        'user': 'python'
                    })
                    print('SMS added to Inbox: add to exist document')
                    break
        else:
            inbox = []
            if renter != None:
                inbox = db.collection('InboxSMS').add({
                    'phone': phone,
                    'ContractName': contract_name,
                    'renter': renter,
                    'created_time': now,
                    'changed_time': now
                })
                print('Add new Inbox: create new document with renter')
            else:
                inbox = db.collection('InboxSMS').add({
                    'phone': phone,
                    'ContractName': contract_name,
                    'created_time': now,
                    'changed_time': now
                })
                print('Add new Inbox: create new document without renter')

            inbox[1].collection('messages').add({
                'created_time': now,
                'is_our': True,
                'readed': False,
                'message': text,
                'user': 'python'
            })
            print('SMS added to Inbox: add to new document (see logs above)')
    else:
        print('SMS not added to Inbox because of "--no-sms" flag.')