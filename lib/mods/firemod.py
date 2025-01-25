from firebase_admin.credentials import Certificate
from firebase_admin.firestore import client
from firebase_admin import initialize_app
from google.cloud.firestore_v1.base_document import DocumentSnapshot as document

def init_db():
    cred = Certificate('key.json')
    initialize_app(cred)
    return client()

def has_key(data: dict, key: str):
    return key in data.keys()

def to_dict_all(data: list):
    dict_data: list[dict] = []
    for i in data:
        dict_data.append(i.to_dict())
    return dict_data

def get_contract(db: client, nickname: str):
    contracts: list[dict] = to_dict_all(db.collection('Contract').get())
    for contract in contracts:
        if contract['nickname'] == nickname and contract['Active'] == True:
            return contract
    return {'ContractName': None}

def get_car(db: client, nickname: str):
    cars: list[dict] = to_dict_all(db.collection('cars').get())
    for car in cars:
        if car['nickname'] == nickname:
            return car
    return {'nickname': None, 'odometer': 0}
