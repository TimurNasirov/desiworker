from sys import path
from os.path import dirname, abspath, exists
from datetime import datetime as dt
from time import sleep
from config import INTUIT_REALM
from requests import get, post
from intuit_refresh import get_auth_client, load_tokens, is_token_expired, refresh_token

intuit_base_url = f'https://quickbooks.api.intuit.com/v3/company/{INTUIT_REALM}/'
intuit_version = '?minorversion=75'

auth_client = get_auth_client()
load_tokens(auth_client)

if is_token_expired():
    refresh_token(auth_client)

def create_customer(name: str, email: str, phone: str):
    json = {
        'DisplayName': name,
        'GivenName': name,
        'PrimaryPhone': {
            'FreeFormNumber': phone
        }
    }
    if email:
        json['PrimaryEmailAddr'] = {'Address': email}
    response = post(f'{intuit_base_url}customer{intuit_version}', json=json, headers={
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
    return response['QueryResponse']['Customer'][0]['Id'] if 'Customer' in response['QueryResponse'].keys() else None

def find_customer_by_name(name: str):
    response = get(f'{intuit_base_url}query{intuit_version}&query=select * from Customer Where DisplayName = \'{name}\'', headers={
        "Authorization": f"Bearer {auth_client.access_token}",
        "Content-Type": "text/plain",
        "Accept": "application/json"
    }).json()
    return response['QueryResponse']['Customer'][0]['Id'] if 'Customer' in response['QueryResponse'].keys() else None

def send_invoice(name: str, email: str, phone: str, rent: float, toll: float, extra: float, other: float):
    if email == '0':
        email = None
    line = [
        {
            'DetailType': 'SalesItemLineDetail',
            'Amount': rent,
            'SalesItemLineDetail': {
                'ItemRef': {
                    'value': '5'
                }
            }
        },
        {
            'DetailType': 'SalesItemLineDetail',
            'Amount': toll,
            'SalesItemLineDetail': {
                'ItemRef': {
                    'value': '7'
                }
            }
        },
        {
            'DetailType': 'SalesItemLineDetail',
            'Amount': extra,
            'SalesItemLineDetail': {
                'ItemRef': {
                    'value': '8'
                }
            }
        },
        {
            'DetailType': 'SalesItemLineDetail',
            'Amount': other,
            'SalesItemLineDetail': {
                'ItemRef': {
                    'value': '9'
                }
            }
        },
        {
            "DetailType": "SalesItemLineDetail",
            "Amount": (rent + toll + extra + other) * 0.04,
            "SalesItemLineDetail": {
                "ItemRef": {
                    "value": "6" #fee
                }
            }
        }
    ]

    if email:
        customer_id = find_customer_by_email(email)
    else:
        customer_id = find_customer_by_name(name)
    if customer_id is None:
        customer_id = create_customer(name, email, phone)
        print(f"created customer with ID: {customer_id}")

    invoice = post(f'{intuit_base_url}invoice{intuit_version}&include=InvoiceLink', json={
        'Line': line,
        'CustomerRef': {
            'value': customer_id
        },
        'AllowOnlineCreditCardPayment': True,
        'AllowOnlineACHPayment': True,
        'BillEmail': {
            'Address': email if email else 'default@example.com'
        }
    }, headers={
        "Authorization": f"Bearer {auth_client.access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }).json()
    print(f"Invoice created. ID: {invoice['Invoice']['Id']}")
    sleep(2)

    if email:
        post(f'{intuit_base_url}invoice/{invoice["Invoice"]["Id"]}/send{intuit_version}&sendTo={email}', headers={
            "Authorization": f"Bearer {auth_client.access_token}",
            "Content-Type": "application/octet-stream",
            "Accept": "application/json"
        })
        print("Invoice sent.")
    print(invoice)
    return [customer_id, rent, toll, extra, other, (rent + toll + extra + other) * 0.04, rent + toll + extra + other, invoice['Invoice']['Id'],\
        invoice['Invoice']['InvoiceLink']]


def add_intuit(db, contract_name: str, data: list):
    contracts = db.collection('Contract').get()
    for i in contracts:
        if i.to_dict()['ContractName'] == contract_name:
            contract = i
            break
    else:
        print('cant find contract', contract_name)
        return

    contract.reference.update({'intuit_id': data[0]})
    contract.reference.collection('invoices').add({
        'date': dt.now(),
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
