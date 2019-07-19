#! /usr/bin/env python3

import requests
import json
import datetime
import psycopg2
import pandas as pd
from psycopg2 import sql 
from typing import List, Tuple
from use_postgres import UseDatabase

db_creds = {'host': '',
            'user': '',
            'database': ''}

aurora_creds = {
    'host': '',
    'port': 5432,
    'user': '',
    'password': ''
}

def grab_grow_sensor_uptimes() -> List:
    """Fetch and return all GROW sensor id's and their start and end datetimes"""
    url = 'https://grow.thingful.net/api/entity/timeSeriesInformations/get'
    header = {'Authorization': ''}
    response = requests.post(url, headers=header)
    json_object = response.json()
    current_sensors = []
    sensor_uptime_list = []
    for i in json_object['TimeSeriesInformations']:
        sensor_id = json_object['TimeSeriesInformations'][i]['LocationIdentifier'][-8:]
        if sensor_id not in current_sensors:
            current_sensors.append(sensor_id)
            sensor_details = []
            sensor_details.append(sensor_id)
            sensor_details.append(json_object['TimeSeriesInformations'][i]['StartDate'])
            sensor_details.append(json_object['TimeSeriesInformations'][i]['EndDate'])
            sensor_uptime_list.append(sensor_details)
    return sensor_uptime_list

#  [['6dngspdq', '20181017130825', '20181229090408'], ['5tjrqt1c', '20181017131407', '20181017135907'], 
# ['fqzb9jsq', '20181017133111', '20181229094049'], ['mqe06kvv', '20181017132233', '20181017140733'], 
# ['xw97j79a', '20181017130255', '20181017143255'], ['fzja2fbn', '20181017131122', '20181017135622']]

def check_most_recent_grow_data(sensor_id: str, start_date: str, end_date: str) -> Tuple[str, List]:
    """Check to see if the most recent sensor reading is already stored in AWS Aurora.
    If it is not already stored, calculate the delta time interval between last 
    stored reading and last recorded reading, and calculate 10 day intervals 
    that add up to the delta interval. This is done because the GROW API
    only allows query ranges to be 10 days maximum.
    """
    with UseDatabase(aurora_creds) as cursor:
        table_name = f"grow_data_{sensor_id}"
        try:
            # Get the most recent sensor recording datetime
            cursor.execute(sql.SQL("SELECT MAX(datetime) FROM {}").format(sql.Identifier(table_name)))
            stored_end_date = cursor.fetchone()[0]
            if stored_end_date == None:
                stored_end_date = datetime.datetime.strptime(start_date, '%Y%m%d%H%M%S')
        except psycopg2.ProgrammingError: 
            # If table does not exist
            stored_end_date = datetime.datetime.strptime(start_date, '%Y%m%d%H%M%S')
    end_dt = datetime.datetime.strptime(end_date, '%Y%m%d%H%M%S')
    delta = end_dt - stored_end_date
    print('delta', delta, 'stored_end_date', stored_end_date, 'sensor', sensor_id)
    if delta == datetime.timedelta(0):
        # If the stored end date and most recent end date are the same, no updates need to be made
        sensor_start_end_intervals = []
    else:
        # Do I need to offset the start/end datetimes? No. Or can the end date be the same as the next start date? Yes.
        sensor_start_end_intervals = []
        start = stored_end_date
        while delta > datetime.timedelta(0):
            if delta < datetime.timedelta(days=9):
                interval = []
                end = end_dt 
                interval.append(start.strftime('%Y%m%d%H%M%S'))
                interval.append(end.strftime('%Y%m%d%H%M%S'))
                sensor_start_end_intervals.append(interval)
                break
            else:
                interval = []
                end = start + datetime.timedelta(days=9)
                interval.append(start.strftime('%Y%m%d%H%M%S'))
                interval.append(end.strftime('%Y%m%d%H%M%S'))
                sensor_start_end_intervals.append(interval)
                delta -= datetime.timedelta(days=9)
                start = end 
        # while delta > datetime.timedelta(0):
        #     interval = []
        #     end = start + datetime.timedelta(days=10)
        #     interval.append(start.strftime('%Y%m%d%H%M%S'))
        #     interval.append(end.strftime('%Y%m%d%H%M%S'))
        #     sensor_start_end_intervals.append(interval)
        #     delta = delta - datetime.timedelta(days=10)
        #     if delta > datetime.timedelta(days=10):
        #         start = end
        #     else:
        #         interval = []
        #         start = end
        #         end = end_dt 
        #         interval.append(start.strftime('%Y%m%d%H%M%S'))
        #         interval.append(end.strftime('%Y%m%d%H%M%S'))
        #         sensor_start_end_intervals.append(interval)
        #         break
    # edit_start_date = start_date[:8] + 'T' + start_date[8:] # add T for later insert to Postgres/Aurora
    # edit_end_date = end_date[:8] + 'T' + end_date[8:]
    return sensor_id, sensor_start_end_intervals

def grab_grow_data(sensor_id: str, sensor_start_end_intervals: List) -> Tuple[str, List, List, List]:
    """Query specific GROW sensor for each interval in sensor_start_end_intervals list.
    Store data in a separate list for each GROW variable.
    """
    header = {'Authorization': ''}
    url = 'https://grow.thingful.net/api/timeSeries/get'
    soil_moisture = []
    light = []
    air_temperature = []
    for datetime_interval in sensor_start_end_intervals:
        payload = {'Readers': [{'DataSourceCode': 'Thingful.Connectors.GROWSensors',
                                'Settings': 
                                    {'LocationCodes': [sensor_id], # 02krq5q5
                                    'VariableCodes': ['Thingful.Connectors.GROWSensors.light',
                                                    'Thingful.Connectors.GROWSensors.air_temperature',
                                                    'Thingful.Connectors.GROWSensors.calibrated_soil_moisture'],
                                    'StartDate': datetime_interval[0], # 20181028200000
                                    'EndDate': datetime_interval[1]
                                }}]}
        while True:
            response = requests.post(url, headers=header, json=payload)
            if 'json' in response.headers.get('Content-Type'):
                json_object = response.json()
            else:
                continue
            try:
                for i in json_object['Data']:
                    if i['VariableCode'].endswith('soil_moisture'):
                        for reading in i['Data']:
                            indiv_reading = []
                            datetime = reading['DateTime']
                            edit_datetime = datetime[:8] + 'T' + datetime[8:]
                            indiv_reading.append(edit_datetime)
                            indiv_reading.append(reading['Value'])
                            soil_moisture.append(indiv_reading)
                    elif i['VariableCode'].endswith('light'):
                        for reading in i['Data']:
                            indiv_reading = []
                            datetime = reading['DateTime']
                            edit_datetime = datetime[:8] + 'T' + datetime[8:]
                            indiv_reading.append(edit_datetime)
                            indiv_reading.append(reading['Value'])
                            light.append(indiv_reading)
                    elif i['VariableCode'].endswith('temperature'):
                        for reading in i['Data']:
                            indiv_reading = []
                            datetime = reading['DateTime']
                            edit_datetime = datetime[:8] + 'T' + datetime[8:]
                            indiv_reading.append(edit_datetime)
                            indiv_reading.append(reading['Value'])
                            air_temperature.append(indiv_reading)
                print('Success')
            except Exception as error:
                print(json_object, "Error: ", error, "Sensor_id: ", sensor_id)
                continue
            break
    return sensor_id, soil_moisture, light, air_temperature

def convert_lists_to_dataframe(sensor_id: str, soil_moisture: List,
                                light: List, air_temperature: List) -> 'DataFrame':
    df = pd.DataFrame(soil_moisture, columns=['datetime', 'soil_moisture'])
    df['light'] = [x[1] for x in light]
    df['air_temperature'] = [x[1] for x in air_temperature]
    df['sensor_id'] = sensor_id
    df.to_csv(f'temp_csvs/grow_data_{sensor_id}.csv', index=False)

def insert_df_to_aurora(sensor_id: str) -> None:
    """Create table in AWS Aurora and insert GROW data"""
    with UseDatabase(aurora_creds) as cursor:
        table_name = f"grow_data_{sensor_id}"
        sql_create = sql.SQL("""CREATE TABLE IF NOT EXISTS {}(
                        sensor_id varchar(8),
                        datetime timestamp, 
                        soil_moisture numeric, 
                        light numeric, 
                        air_temperature numeric
                        )""").format(sql.Identifier(table_name))
        cursor.execute(sql_create)
        with open(f'temp_csvs/grow_data_{sensor_id}.csv') as csv:
            next(csv)
            cursor.copy_from(csv, table_name, columns=('datetime','soil_moisture','light','air_temperature','sensor_id'), sep=',')

    # engine = create_engine('postgresql+psycopg2://awsuser:Lovesaws22@my-aurora-test.cynbkpreeybn.eu-west-1.rds.amazonaws.com:5432/awsuser')
    # dataframe.to_sql(table_name, con=engine, if_exists='append', index=False, chunksize=1000)

# def insert_to_aurora(sensor_id: str, soil_moisture: List, 
#                     light: List, air_temperature: List) -> None:
#     """Create table in AWS Aurora and insert GROW data"""
#     with UseDatabase(aurora_creds) as cursor:
#         table_name = f"grow_data_{sensor_id}"
#         sql_create = sql.SQL("""CREATE TABLE IF NOT EXISTS {}(
#                         sensor_id varchar(8),
#                         datetime timestamp, 
#                         soil_moisture numeric, 
#                         light numeric, 
#                         air_temperature numeric
#                         )""").format(sql.Identifier(table_name))
#         cursor.execute(sql_create)

#     engine = create_engine('postgresql+psycopg2://awsuser:Lovesaws22@my-aurora-test.cynbkpreeybn.eu-west-1.rds.amazonaws.com:5432/my-aurora-test')
#     df.to_sql(table_name, con, if_exists='append')

#         sql_state = "INSERT INTO {} (sensor_id, datetime, soil_moisture) VALUES(%s)".format(sql.Identifier(table_name))
#         psycopg2.extras.execute_values(cursor, sql_state, soil_moisture, page_size=100)


#         data = [(1,'x'), (2,'y')]
#         insert_query = 'insert into t (a, b) values %s'
#         psycopg2.extras.execute_values (
#             cursor, insert_query, data, template=None, page_size=100
#         )

#         for a, b, c in zip(soil_moisture, light, air_temperature):
#             cursor.execute(sql.SQL("""INSERT INTO {}
#                             VALUES(%s, %s, %s, %s, %s)""")
#                             .format(sql.Identifier(table_name)), 
#                             (sensor_id, a[0], a[1], b[1], c[1]))

if __name__ == '__main__':
    sensor_uptime_list = grab_grow_sensor_uptimes()
    for i in sensor_uptime_list:
        sensor_id, sensor_start_end_intervals = check_most_recent_grow_data(i[0], i[1], i[2])
        if sensor_start_end_intervals == []:
            continue
        sensor_id, soil_moisture, light, air_temperature = grab_grow_data(sensor_id, sensor_start_end_intervals)
        convert_lists_to_dataframe(sensor_id, soil_moisture, light, air_temperature)
        insert_df_to_aurora(sensor_id)

        # insert_to_aurora(sensor_id, soil_moisture, light, air_temperature)

# TO DELETE ALL TABLES MADE
# cursor.execute("SELECT tablename FROM pg_tables WHERE tablename LIKE 'grow_data_%'")
# results = cursor.fetchall()
# for i in results:
#     cursor.execute(sql.SQL("DROP TABLE {}").format(sql.Identifier(i[0])))



        #  From line 60 on in check_most_recent_grow_data()
        # sql = "SELECT MAX(datetime) FROM grow_data WHERE sensor_id = %s"
        # cursor.execute(sql, (sensor_id,))
        # try:
        #     stored_end_date = cursor.fetchone()[0]
        #     if stored_end_date == None:
        #         stored_end_date = datetime.datetime.strptime(start_date, '%Y%m%d%H%M%S')
        # except TypeError:
        #     # If there is no end date already stored, use the grow sensor start date 
        #     stored_end_date = datetime.datetime.strptime(start_date, '%Y%m%d%H%M%S')



        





