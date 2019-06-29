#!/usr/bin/env python3

import requests

######## GROW Thingful API ########
# Grab data source variables
# entity/dataSourceVariables/get endpoint
url = 'https://grow.thingful.net/api/entity/dataSourceVariables/get'
header = {'Authorization': 'Bearer 8tze34c9qt-7320dcbe17138840d554e4b5fd0c6a0f'}
response = requests.post(url, headers=header)

# Grab all GROW sensor locations
# entity/locations/get endpoint
url2 = 'https://grow.thingful.net/api/entity/locations/get'
payload = {'DataSourceCodes': ['Thingful.Connectors.GROWSensors']}
response2 = requests.post(url2, headers=header, json=payload)

# Grab sensor observation
# timeSeries/get endpoint
url3 = 'https://grow.thingful.net/api/timeSeries/get'
payload2 = {'Readers': [{'DataSourceCode': 'Thingful.Connectors.GROWSensors',
                        'Settings': {'LocationCodes': ['02krq5q5'], 
                                    'VariableCodes': ['Thingful.Connectors.GROWSensors.light',
                                                        'Thingful.Connectors.GROWSensors.air_temperature',
                                                        'Thingful.Connectors.GROWSensors.calibrated_soil_moisture'],
                                    'StartDate': '20181028000000', 
                                    'EndDate': '20181106000000'
                                    }}]}
postman_body = {
                "Readers": [
                    {
                        "DataSourceCode": "Thingful.Connectors.GROWSensors",
                        "Settings": {
                            "LocationCodes": [
                                "02krq5q5" # h3artq9r 1r9k4xwm 6nncw98e 910gayxb
                                ],
                            "VariableCodes": [
                                "Thingful.Connectors.GROWSensors.light"
                                ],
                            "StartDate": "20181028000000",
                            "EndDate": "20181106000000",
                            "Order": "asc",
                            "StructureType": "TimeSeries",
                            "CalculationType": "None"
                            }
                        }
                    ]
                }
response3 = requests.post(url3, headers=header, json=payload2)

# Grab sensor uptime
# entity/timeSeriesInformations/get endpoint
url4 = 'https://grow.thingful.net/api/entity/timeSeriesInformations/get'
response4 = requests.post(url4, headers=header)
response4 = requests.post(url4, headers=header, stream=True)


######## MetOffice WOW API ########
# Grab all user groups
# /Groups endpoint
url5 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/Groups'
header2 = {'Ocp-Apim-Subscription-Key': 'cfcf626271be44f6ab25e52016a1afb7'}
response5 = requests.get(url5, headers=header2)

# Gets all sites registered to a group - doesn't seem to return valid site id's... 
# /groups/{id}/sites endpoint
# ABoM AGCD  1000007
# ABOMPrecipitationSystemGroup 999999
# AGCD 1000003
# AWS_WOW 1000011
# Capital_Cities 1000001
# Rainfall 1000012 - 1 site
# School 1 - 10 sites
    # [{'id': '938486001', 'name': 'Westgate School (Winchester)'},
    # {'id': '947126001', 'name': 'Newport Primary School'},
    # {'id': '948936001', 'name': 'Andrews Memorial Primary School'},
    # {'id': '951676001', 'name': 'Ainderby Steeple School'},
    # {'id': '962676001', 'name': 'Newton Poppleford Primary'},
    # {'id': '963586001', 'name': 'The Robert Fitzroy Academy'},
    # {'id': '964506001', 'name': 'Crosfields School'},
    # {'id': '966736001', 'name': 'West Town Primary Academy'},
    # {'id': '967926001', 'name': 'St Josephs School'},
    # {'id': '975726001', 'name': 'Ysgol Penglais'}]
# Test group 2 1000010 - 0 sites
# WOW test group 1000000 - 5 sites
    # [{'id': '2a317075-5639-e711-9400-0003ff59a8fb', 'name': 'Cranbrook'},
    #  {'id': '693476850', 'name': 'WOW TEST'},
    #  {'id': '964c5434-5839-e711-9400-0003ff59a8fb',
    #   'name': 'Watford, Hornets Nest'},
    #  {'id': 'c65aa3c7-5f39-e711-9400-000d3ab1c4d1', 'name': 'Cycle Path'},
    #  {'id': 'de06e4b9-dde3-e711-9405-0003ff59b2bd', 'name': 'Met Office Test'}]
url8 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/groups/1000012/sites'
response8 = requests.get(url8, headers=header2)

# Get all observation parameters
# /ObservationParameters endpoint
url6 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/ObservationParameters'
response6 = requests.get(url6, headers=header2)

# Search all sites
# /sites/search endpoint -  all calls to this endpoint seem to hang in 'buffering' stage
url7 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/sites/search'
header3 = {'Ocp-Apim-Subscription-Key': 'cfcf626271be44f6ab25e52016a1afb7',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
        }       
payload3 = {'longitudeStart': -8.33661, 
            'latitudeStart': 54.9422, 
            'longitudeEnd': 19.6495, 
            'latitudeEnd': 46.6583}
response7 = requests.get(url7, headers=header2, params=payload3)
url11 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/sites/search?longitudeStart=-4.33718&latitudeStart=56.0707&longitudeEnd=4.899431&latitudeEnd=52.379189' # - returns empty list 
url11 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/sites/search?longitudeStart=56.0707&latitudeStart=-4.33718&longitudeEnd=52.379189&latitudeEnd=4.899431' # reversed lat/long, empty list
response13 = requests.get(url11, headers=header2)
url12 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/sites/search?text=1d887b90-b873-e911-80e7-0003ff597316'
response14 = requests.get(url12, headers=header2)
# [{'description': 'Oregon scientific WRM200, Stevenson screen (height: 1,5m) on '
#                  'grass, some trees and hedges at distances between 3 and 20 m '
#                  'or more. Two garden houses at 8 &agrave; 10 m and a house at '
#                  'approx. 20 m.',
#   'id': '965656001',
#   'latitude': 52.11979,
#   'longitude': 5.161686,
#   'name': 'weergroenekan'}]
url13 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/sites/search?longitudeStart=5.161686&latitudeStart=52.11979'
response15 = requests.get(url13, headers=header2)
# returns Web server received an invalid response while acting as a gateway or proxy server.</h2>\r\n 
#  <h3>There is a problem with the page you are looking for, and it cannot be displayed. 
# When the Web server (while acting as a gateway or proxy) contacted the upstream content server, 
# it received an invalid response from the content server.

# Get observations by version - returns latest version of observations based on the criteria given - 404 resource not found
# /observations/byversion endpoint
# provide datetime parameters as RFC3339 format -> 2019-05-11T19:41:57
url9 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/observations/byversion'
payload4 = {'site_id': '965656001',
            'start_time': '2019-05-10T19:41:57',
            'end_time': '2019-05-12T19:41:57'}
response11 = requests.get(url9, headers=header2, params=payload4) # 200
url10 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/observations/byversion?start_time=2019-05-11T19:41:57&end_time=2019-05-12T19:41:57' - 200
response12 = requests.get(url10, headers=header2) # wow_sample_observations.json
payload4 = {'start_time': '2019-05-11T19:41:57',
            'end_time': '2019-05-12T19:41:57',
            'top_left_long': -8.33661, 
            'top_left_lat': 54.9422, 
            'bottom_right_long': 19.6495, 
            'bottom_right_lat': 46.6583}
response17 = requests.get(url9, headers=header2, params=payload4) # 200 wow_observations_by_version.json

# capture all Europe observation stations
payload5 = {'start_time': '2019-05-11T19:41:57',
            'end_time': '2019-05-11T20:00:00',
            'top_left_long': -14.835302, 
            'top_left_lat': 58.607303, 
            'bottom_right_long': 26.136293, 
            'bottom_right_lat': 30.978883}
response18 = requests.get(url9, headers=header2, params=payload5)

# capture specific observations from site
payload6 = {'start_time': '2019-05-11T19:41:57',
            'end_time': '2019-05-24T20:00:00',
            'site_id': '2ce01a20-fc29-e911-9461-0003ff596eab'}   
response19 = requests.get(url9, headers=header2, params=payload6)

# shot in the dark
url = 'https://apimgmt.www.wow.metoffice.gov.uk/api/sites/search'
# ?lastModifiedStart=2019-05-10T19:41:57&lastModifiedEnd=2019-05-11T19:41:57
response10 = requests.get(url, headers=header3, timeout=600) # 200 response but contains 500 internal server error json response

url = 'https://apimgmt.www.wow.metoffice.gov.uk/api/sites/search?lastModifiedStart=2019-05-28T19:41:57&lastModifiedEnd=2019-05-29T19:41:57'
response16 = requests.get(url, headers=header3, timeout=600) # 200 returns sites 


# Grabs details about an observation site
# /sites/ObservationSite endpoint
url = 'https://apimgmt.www.wow.metoffice.gov.uk/api/sites/ObservationSite'
payload = {'id': '2ce01a20-fc29-e911-9461-0003ff596eab'}
response = requests.get(url, headers=header2, params=payload)

# Returns the measured parameter list for the site. 
# /sites/ObservationSiteDataMeasurement endpoint
url10 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/sites/ObservationSiteDataMeasurement'
payload7 = {'id': '2ce01a20-fc29-e911-9461-0003ff596eab'}
response20 = requests.get(url10, headers=header2, params=payload7)
# [{'name': 'DryBulbTemperature', 'value': 2},
#  {'name': 'WetBulbTemperature', 'value': 2},
#  {'name': 'AirTemperatureMax', 'value': 2},
#  {'name': 'AirTemperatureMin', 'value': 2},
#  {'name': 'GrassTemperatureMin', 'value': 2},
#  {'name': 'ConcreteTemperatureMin', 'value': 2}]

# Returns the specified site information.
# /Sites endpoint
url11 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/Sites'
payload8 = {'id': '2ce01a20-fc29-e911-9461-0003ff596eab'}
response21 = requests.get(url11, headers=header2, params=payload8) # 404 resource not found


# Returns the observations of a given site in a given time range
# /observations/bysite endpoint 
url12 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/observations/bysite'
payload9 = {'start_time': '2019-05-11T19:41:57',
            'end_time': '2019-05-24T20:00:00',
            'site_id': '2ce01a20-fc29-e911-9461-0003ff596eab'} # 200
payload9 = {'start_time': '2019-05-11T19:41:57',
            'end_time': '2019-05-24T20:00:00',
            'site_id': '965656001'} # 200
response22 = requests.get(url12, headers=header2, params=payload9)

# Returns the observations of a group of sites in a given time range
# /observations/bysites endpoint
url13 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/observations/bysites'
payload10 = {'start_time': '2019-05-11T19:41:57',
            'end_time': '2019-05-24T20:00:00',
            'site_ids': ['2ce01a20-fc29-e911-9461-0003ff596eab', '965656001']} 
response23 = requests.get(url13, headers=header2, params=payload10) # 200 but returns EMPTY LIST

# Returns the observations in GeoJSON format
# /observations/geojson endpoint
url14 = 'https://apimgmt.www.wow.metoffice.gov.uk/api/observations/geojson'
payload11 = {'start_time': '2019-05-11T19:41:57', 
            'end_time': '2019-05-12T20:00:00', 
            'siteId': '2ce01a20-fc29-e911-9461-0003ff596eab'}
response24 = requests.get(url14, headers=header2, params=payload11)


