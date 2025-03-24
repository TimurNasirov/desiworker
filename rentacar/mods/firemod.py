"""Mod that helps work with firebase"""

from firebase_admin.credentials import Certificate
from firebase_admin.firestore import client
from firebase_admin import initialize_app
from firebase_admin.storage import bucket
from google.cloud import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot as document
from config import FIREBASE_STORAGE

def init_db():
    """Initialize the database

    Returns:
        client: database
    """
    cred = Certificate('key.json')
    initialize_app(cred, {'storageBucket': FIREBASE_STORAGE})
    return client()

def has_key(data: dict, key: str):
    """Returns True if the given key is present in the dictionary

    Args:
        data (dict): dictionary
        key (str): key

    Returns:
        bool: return data
    """
    return key in data.keys()

def to_dict_all(data: list[document]):
    """Converts all documents in a list to a dict

    Args:
        data (list[document]): data from db

    Returns:
        list[dict]: converted data
    """
    dict_data: list[dict] = []
    for i in data:
        i_data: dict = i.to_dict()
        i_data['_firebase_document_id'] = i.id
        dict_data.append(i_data)
    return dict_data

def get_contract(db: client, data: str, by: str = 'nickname', check_active: bool = True):
    """Get contract by name

    Args:
        db (client): database
        data (str): file value
        by (str, optional): field name. Defaults to 'nickname'.

    Returns:
        dict: contract
    """
    contracts: list[dict] = to_dict_all(db.collection('Contract').order_by('begin_time', direction=firestore.Query.DESCENDING).get())
    for contract in contracts:
        if contract[by] == data and (contract['Active'] or not check_active):
            return contract
    return {'ContractName': None}

def get_car(db: client, data: str, by: str = 'nickname'):
    """Get a specific car by name

    Args:
        db (client): database
        data (str): file value
        by (str, optional): field name. Defaults to 'nickname'.

    Returns:
        dict: car
    """
    cars: list[dict] = to_dict_all(db.collection('cars').get())
    for car in cars:
        if has_key(car, by):
            if car[by] == data:
                return car
    return {'nickname': None, 'odometer': 0}