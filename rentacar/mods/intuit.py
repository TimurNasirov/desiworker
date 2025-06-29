from sys import path
from os.path import dirname, abspath
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from mods.timemod import dt, texas_tz, sleep
from config import INTUIT_REALM
from mods.firemod import document
from requests import get, post
from mods.intuit_refresh import get_auth_client, load_tokens, is_token_expired, refresh_token
from log import Log

intuit_base_url = f'https://quickbooks.api.intuit.com/v3/company/{INTUIT_REALM}/'
intuit_version = '?minorversion=75'
# logdata = Log('rentacar/mods/intuit.py')
# print = logdata.print

auth_client = get_auth_client()
load_tokens(auth_client)

if is_token_expired():
    refresh_token(auth_client)

def create_customer(name: str, email: str, phone: str):
    response = post(f'{intuit_base_url}customer{intuit_version}', json={
        'DisplayName': name,
        'GivenName': name,
        'PrimaryEmailAddr': {
            'Address': email
        },
        'PrimaryPhone': {
            'FreeFormNumber': phone
        }
    }, headers={
        "Authorization": f"Bearer {auth_client.access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }).json()
    return response['Customer']['Id']


def find_customer_by_email(email: str):
    response = get(f'{intuit_base_url}query{intuit_version}&query=select * from Customer Where PrimaryEmailAddr = \'{email}\'', headers={
        "Authorization": f"Bearer {auth_client.access_token}",
        "Content-Type": "text/plain",
        "Accept": "application/json"
    }).json()
    return response['QueryResponse']['Customer'][0]['Id'] if response['QueryResponse']['Customer'] else None

def send_invoice(name: str, email: str, phone: str, rent: int | float | None = None, toll: int | float | None = None, extra: int | float |\
        None = None, other: int | float | None = None):
    line = []
    if rent is not None:
        line.append({
            'DetailType': 'SalesItemLineDetail',
            'Amount': rent,
            'SalesItemLineDetail': {
                'ItemRef': {
                    'value': '5'
                }
            }
        })
    else:
        rent = 0
    if toll is not None:
        line.append({
            'DetailType': 'SalesItemLineDetail',
            'Amount': toll,
            'SalesItemLineDetail': {
                'ItemRef': {
                    'value': '7'
                }
            }
        })
    else:
        toll = 0
    if extra is not None:
        line.append({
            'DetailType': 'SalesItemLineDetail',
            'Amount': extra,
            'SalesItemLineDetail': {
                'ItemRef': {
                    'value': '8'
                }
            }
        })
    else:
        extra = 0
    if other is not None:
        line.append({
            'DetailType': 'SalesItemLineDetail',
            'Amount': other,
            'SalesItemLineDetail': {
                'ItemRef': {
                    'value': '9'
                }
            }
        })
    else:
        other = 0

    line.append({
        "DetailType": "SalesItemLineDetail",
        "Amount": (rent + toll + extra + other) * 0.04,
        "SalesItemLineDetail": {
            "ItemRef": {
                "value": "6" #fee
            }
        }
    })


    customer_id = find_customer_by_email(email)
    if customer_id is None:
        customer_id = create_customer(name, email, phone)
        print(f"created customer with ID: {customer_id}")

    invoice = post(f'{intuit_base_url}invoice{intuit_version}', json={
        'Line': line,
        'CustomerRef': {
            'value': customer_id
        }
    }, headers={
        "Authorization": f"Bearer {auth_client.access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }).json()
    print(f"Invoice created. ID: {invoice['Invoice']['Id']}")
    sleep(2)

    post(f'{intuit_base_url}invoice/{invoice['Invoice']['Id']}/send{intuit_version}&sendTo={email}', headers={
        "Authorization": f"Bearer {auth_client.access_token}",
        "Content-Type": "application/octet-stream",
        "Accept": "application/json"
    })
    print("Invoice sent.")
    return [customer_id, rent, toll, extra, other, (rent + toll + extra + other) * 0.04, rent + toll + extra + other, invoice['Invoice']['Id'],\
        invoice.InvoiceLink]


def add_intuit(contract: document, data: list):
    contract.reference.update({'intuit_id': data[0]})
    contract.reference.collection('invoices').add({
        'date': dt.now(texas_tz),
        'sum': data[6],
        'rent': data[1],
        'toll': data[2],
        'extra': data[3],
        'other': data[4],
        'fee': data[5],
        'status': 'sent',
        'id': int(data[7]),
        'link': data[8]
    })