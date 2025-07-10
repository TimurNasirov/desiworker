"""Mod that helps work with firebase
read exploit: fixed
linting: 9.73 (fixed)
"""

from firebase_admin.credentials import Certificate
from firebase_admin.firestore import client
from firebase_admin import initialize_app
from firebase_admin.storage import bucket
from google.cloud import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot as document
from google.cloud.firestore_v1.base_query import FieldFilter

def init_db() -> firestore.Client:
    """Initialize the database"""
    cred = Certificate('key.json')
    initialize_app(cred)
    return client()

def has_key(data: dict, key: str) -> bool:
    """Returns True if the given key is present in the dictionary"""
    return key in data.keys()

def to_dict_all(data: list[document]) -> list[dict]:
    """Converts all documents in a list to a dict"""
    dict_data: list[dict] = []
    for i in data:
        i_data = i.to_dict()
        if not i_data:
            raise ValueError('i.to_dict() is null')
        i_data['_firebase_document_id'] = i.id
        dict_data.append(i_data)
    return dict_data

def get_contract(db, data: str, by: str = 'nickname', check_active: bool = True) -> dict:
    """get contract data"""
    query = db.collection('Contract').where(filter=FieldFilter(by, '==', data))

    if check_active:
        query = query.where(filter=FieldFilter('Active', '==', True))

    query = query.order_by('begin_time', direction=firestore.Query.DESCENDING).limit(1)
    results = query.get()

    if results:
        return to_dict_all(results)[0]
    return {'ContractName': None}

def get_car(db, data: str, by: str = 'nickname') -> dict:
    """get сar data"""
    car = db.collection('cars').where(filter=FieldFilter(by, '==', data)).limit(1).get()
    if car:
        return car.to_dict()
    return {'nickname': None, 'odometer': 0}
