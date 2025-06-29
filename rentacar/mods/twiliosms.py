from twilio.rest import Client
from config import TWILIO_TOKEN, TWILIO_SID, TWILIO_PHONE
from sys import argv
from rentacar.mods.firemod import client as fclient, has_key, document
from rentacar.mods.timemod import dt
from rentacar.log import Log

logdata = Log('rentacar/mods/twilio.py')
print = logdata.print

PAYDAY_TEXT = "DESICARS: Hi. It's time to pay for the rental car. Please send a confirmation via TG t.me/Desi_rental_cars after making the paym\
ent. Thank you!"
CHANGE_OIL_TEXT = "DESICARS: Hi. It's time to change the oil in the car. Please come to the office to take care of this. Thank you!"
INSURANCE_TEXT = "DESICARS: Hi. It's time to renew the car insurance. Please send me the new policy via TG t.me/Desi_rental_cars once it's read\
y. Thank you!"
LATEPAYMENT_TEXT = "DESICARS: Hi! Payment was due 3 days ago. Confirm via TG: t.me/Desi_rental_cars after payment. Late fee in 2 days."
REGISTRATION_TEXT = "DESICARS: Hi. It's time to renew the car registration. Please visit the office to complete this. Thank you!"

client = Client(TWILIO_SID, TWILIO_TOKEN)

def send(phone: str, text: str):
    if '--no-sms' in argv:
        print('SMS not sent because of "--no-sms" flag.')
        return
    client.messages.create(phone, body=text, from_=TWILIO_PHONE)
    print(f'send SMS - phone: {phone}')

def add_inbox(db: fclient, phone: str, text: str, contract_name: str, renter: str):
    """Add a message to the database

    Args:
        db (client): database
        phone (str): renter number
        text (str): text of sms
        contract_name (str): contact name
        renter (str): renter
    """
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
                    # print('SMS added to Inbox: add to exist document')
                    break
        else:
            inbox = []
            if renter is not None:
                inbox = db.collection('InboxSMS').add({
                    'phone': phone,
                    'ContractName': contract_name,
                    'renter': renter,
                    'created_time': now,
                    'changed_time': now
                })
                # print('Add new Inbox: create new document with renter')
            else:
                inbox = db.collection('InboxSMS').add({
                    'phone': phone,
                    'ContractName': contract_name,
                    'created_time': now,
                    'changed_time': now
                })
                # print('Add new Inbox: create new document without renter')

            inbox[1].collection('messages').add({
                'created_time': now,
                'is_our': True,
                'readed': True,
                'message': text,
                'user': 'python'
            })
            # print('SMS added to Inbox: add to new document (see logs above)')
    else:
        print('SMS not added to Inbox because of "--no-sms" flag.')

def sms_block_check(contract: dict):
    accept = True
    if has_key(contract, 'sms_blocked'):
        accept = not contract['sms_blocked']
    if not accept:
        print('sms sending canceled: renter declined subscription')
    return accept

send('+12172105897')