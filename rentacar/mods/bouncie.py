"""Mod that get data from bouncie"""
from json import loads
from requests import post, get
from rentacar.log import Log
from config import BOUCNIE_HEADERS, BOUNCIE_API_URL, BOUNCIE_VEHICLES_URL, BOUNCIE_TRIP_URL
from rentacar.mods.firemod import has_key
from rentacar.mods.timemod import dt, timedelta, texas_tz

logdata = Log('rentacar/mods/bouncie.py')
print = logdata.print

def get_apikey(code: str):
    """get apikey access token from the given code

    Args:
        code (str): code

    Returns:
        str: token
    """
    print('get apikey from bouncie.')
    json_data = BOUCNIE_HEADERS
    json_data['code'] = code
    return loads(post(BOUNCIE_API_URL, json=json_data).text)['access_token']

def get_odometer(key, imei):
    """Get odometer from IMEI

    Args:
        key (str): api key
        imei (str): device imei

    Returns:
        int: odometer
    """
    #print(f'get odometer from {imei} imei.')
    try:
        starts = dt.now(texas_tz).strftime('%Y-%m-%d 23:59:59')
        ends = (dt.now(texas_tz) - timedelta(days=6)).strftime('%Y-%m-%d 23:59:59')
        data = loads(get(BOUNCIE_TRIP_URL, headers={
            'Authorization': key
        }, params={
            'imei': imei,
            'starts_after': starts,
            'ends_before': ends,
            'gps-format': 'polyline'
        }).text)
        try:
            if has_key(data[0], 'endOdometer'):
                return data[0]['endOdometer'] if data[0]['endOdometer'] is not None else data[0]['startOdometer']\
                    if data[0]['startOdometer'] is not None else 'keep'
            return data[0]['startOdometer'] if data[0]['startOdometer'] is not None else 'keep'
        except IndexError:
            return 'keep'
    except Exception as e:
        print(f'Raised {e} when getting odometer from {imei}. Odometer of this car will not updated.')
        return 'keep'

def get_imei(key):
    print('get imei data from bouncie.')
    return loads(get(BOUNCIE_VEHICLES_URL, headers={
        'Authorization': key
    }).text)