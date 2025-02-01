from firebase_admin.credentials import Certificate
from firebase_admin.firestore import client
from firebase_admin import initialize_app
from firebase_admin.storage import bucket
from google.cloud.firestore_v1.base_document import DocumentSnapshot as document
from config import FIREBASE_STORAGE

def init_db():
    cred = Certificate('key.json')
    initialize_app(cred, {'storageBucket': FIREBASE_STORAGE})
    return client()

def has_key(data: dict, key: str):
    return key in data.keys()

def to_dict_all(data: list[document]):
    dict_data: list[dict] = []
    for i in data:
        i_data: dict = i.to_dict()
        i_data['_firebase_document_id'] = i.id
        dict_data.append(i_data)
    return dict_data

def get_contract(db: client, date: str, by: str = 'nickname'):
    contracts: list[dict] = to_dict_all(db.collection('Contract').get())
    for contract in contracts:
        if contract[by] == date and contract['Active'] == True:
            return contract
    return {'ContractName': None}

def get_car(db: client, data: str, by: str = 'nickname'):
    cars: list[dict] = to_dict_all(db.collection('cars').get())
    for car in cars:
        if car[by] == data:
            return car
    return {'nickname': None, 'odometer': 0}
