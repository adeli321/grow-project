#!/usr/bin/env python3

import argparse
import requests
from typing import List

def get_address(latlng: str, api_key: str) -> List:
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    payload = {'latlng': latlng, 'key': api_key}
    response = requests.get(url, params=payload)
    json_object = response.json()

    full_address = []
    for i in json_object['results'][0]['address_components']:
        full_address.append(i['long_name'])
    return ' '.join(full_address)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('latlng')
    parser.add_argument('api_key')
    args = parser.parse_args()

    get_address(args.latlng, args.api_key)


