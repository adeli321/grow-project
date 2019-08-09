#!/usr/bin/env python3

import pandas as pd
import numpy as np
from use_postgres import UseDatabase
from typing import List, Tuple
from psycopg2 import sql
from sqlalchemy import create_engine
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

def get_all_grow_tables(conn) -> np.ndarray:
    """Return all GROW table names from AWS Aurora DB"""
    sql_all = """SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name 
                LIKE 'grow_data_%%';"""
    all_tables_df = pd.read_sql(sql_all, conn)
    all_tables_array = all_tables_df.values
    return all_tables_array

def get_keras_models() -> '3 Keras Models':
    """Retrieve previously trained Keras models for anomaly detection"""
    soil_model = load_model('saved_models/soil_model.h5')
    light_model = load_model('saved_models/light_model.h5')
    air_model = load_model('saved_models/air_model.h5')
    return soil_model, light_model, air_model

def construct_predict_dfs(table_name: str, conn) -> '3 DataFrames, 1 np.array':
    """Construct 3 DataFrames and one Numpy array from the contents of 
    a GROW table stored in AWS Aurora. These DataFrames will be 
    analysed against the Keras models previously built to 
    detect anomalies/anomalous data.
    """
    sql = f"""SELECT * FROM {table_name}"""
    df = pd.read_sql(sql, conn, parse_dates=['datetime'])
    # Dataframe is not ordered, sort by datetime
    df = df.sort_values(axis=0, by=['datetime'])
    # Chop off beginning of df to make it divisible by 96
    # 96 observations equal one day of observations
    remainder = len(df) % 96
    predict_df = df[remainder:]
    predict_df_2 = predict_df.copy(deep=True)
    predict_df_3 = predict_df.copy(deep=True)
    predict_df_4 = predict_df.copy(deep=True)
    # Drop all columns except for one for each df
    predict_df_soil = predict_df.drop(['sensor_id'], axis=1).drop(['datetime'], axis=1) \
                                .drop(['light'], axis=1).drop(['air_temperature'], axis=1) \
                                .drop(['battery_level'], axis=1)
    predict_df_light = predict_df_2.drop(['sensor_id'], axis=1).drop(['datetime'], axis=1) \
                                    .drop(['soil_moisture'], axis=1).drop(['air_temperature'], axis=1) \
                                    .drop(['battery_level'], axis=1)
    predict_df_air = predict_df_3.drop(['sensor_id'], axis=1).drop(['datetime'], axis=1) \
                                .drop(['soil_moisture'], axis=1).drop(['light'], axis=1) \
                                .drop(['battery_level'], axis=1)
    predict_dates = predict_df_4.drop(['sensor_id'], axis=1).drop(['soil_moisture'], axis=1) \
                                .drop(['light'], axis=1).drop(['air_temperature'], axis=1) \
                                .drop(['battery_level'], axis=1)
    # Normalize data to fall between [0,1]
    scaler = MinMaxScaler()
    predict_df_soil_scaled = scaler.fit_transform(predict_df_soil)
    predict_df_light_scaled = scaler.fit_transform(predict_df_light)
    predict_df_air_scaled = scaler.fit_transform(predict_df_air)
    # Reshape data into chunks of 96 -> ie: (472, 96, 1)
    timesteps = 96
    dim = 1
    samples = len(predict_df_soil_scaled)
    predict_df_soil_scaled.shape = (int(samples/timesteps),timesteps,dim)
    predict_df_light_scaled.shape = (int(samples/timesteps),timesteps,dim)
    predict_df_air_scaled.shape = (int(samples/timesteps),timesteps,dim)
    predict_dates_array = predict_dates.values
    predict_dates_array.shape = (int(samples/timesteps),timesteps,dim)
    return predict_df_soil_scaled, predict_df_light_scaled, predict_df_air_scaled, predict_dates_array

def predict_on_keras_models(predict_soil_df: pd.DataFrame, predict_light_df: pd.DataFrame, 
                            predict_air_df: pd.DataFrame, soil_model, 
                            light_model, air_model) -> Tuple[np.ndarray,np.ndarray,np.ndarray]:
    """Uses the provided DataFrames to predict on the previously built Keras models.
    Calculates and returns their reconstruction error to later detect anomalous data.
    """
    predictions_soil = soil_model.predict(predict_soil_df)
    # Mean-squared error: Reconstruction error
    mse_soil = np.mean(np.power(predict_soil_df - predictions_soil, 2), axis=1)
    predictions_light = light_model.predict(predict_light_df)
    mse_light = np.mean(np.power(predict_light_df - predictions_light, 2), axis=1)
    predictions_air = air_model.predict(predict_air_df)
    mse_air = np.mean(np.power(predict_air_df - predictions_air, 2), axis=1)
    return mse_soil, mse_light, mse_air

def analyse_soil_error(mse_soil: np.ndarray, predict_dates: np.ndarray) -> List:
    """Loop through soil reconsruction error array. If error is 
    identical twice in a row, flag as anomaly. Record error and 
    its respective datetime in result array.
    """
    anomalous_results = []
    for index, mse in enumerate(mse_soil[:-1]):
        if mse[0] == mse_soil[index + 1]:
            anomalous_results.append([mse[0], predict_dates[index][0][0]])
    return anomalous_results

    # anomalous_results = []
    # for index, mse in enumerate(mse_soil):
    #     if mse[0] > 1.00e-04:
    #         anomalous_results.append([mse[0], predict_dates[index][0][0]])
    # return anomalous_results

def analyse_light_error(mse_light: np.ndarray, predict_dates: np.ndarray) -> List:
    """Loop through light reconsruction error array. If error is 
    identical twice in a row, flag as anomaly. Record error and 
    its respective datetime in result array.
    """
    anomalous_results = []
    for index, mse in enumerate(mse_light[:-1]):
        if mse[0] == mse_light[index + 1]:
            anomalous_results.append([mse[0], predict_dates[index][0][0]])
    return anomalous_results

def analyse_air_error(mse_air: np.ndarray, predict_dates: np.ndarray) -> List:
    """Loop through air reconsruction error array. If error is 
    identical for more than 3 times, flag as anomaly. Record error and 
    its respective datetime in result array.
    """
    anomalous_results = []
    for index, mse in enumerate(mse_air[:-1]):
        if mse[0] == mse_air[index + 1]:
            anomalous_results.append([mse[0], predict_dates[index][0][0]])
    return anomalous_results

def create_anomaly_table(conn) -> None:
    """Create table to store anomalous information in 
    AWS Aurora instance (Postgresql compatible)
    """
    sql = """CREATE TABLE IF NOT EXISTS grow_anomalies(
            grow_table varchar(18),
            soil_date timestamp, 
            light_date timestamp, 
            air_date timestamp
            )"""
    conn.execute(sql)

def insert_anomalies(soil_anomalies: List, light_anomalies: List,
                    air_anomalies: List, table_name: str) -> None:
    aurora_creds = {
        'host': '',
        'port': 5432,
        'dbname': '',
        'user': '',
        'password': ''
    }
    with UseDatabase(aurora_creds) as cursor:
        for anom in soil_anomalies:
            sql_insert = sql.SQL("""INSERT INTO grow_anomalies
                            (grow_table, soil_date)
                            VALUES({},{})""") \
                            .format(sql.Literal(table_name),
                                    sql.Literal(str(anom[1])))
            cursor.execute(sql_insert)
        for anom in light_anomalies:
            sql_insert = sql.SQL("""INSERT INTO grow_anomalies
                            (grow_table, light_date)
                            VALUES({},{})""") \
                            .format(sql.Literal(table_name),
                                    sql.Literal(str(anom[1])))
            cursor.execute(sql_insert)
        for anom in air_anomalies:
            sql_insert = sql.SQL("""INSERT INTO grow_anomalies
                            (grow_table, air_date)
                            VALUES({},{})""") \
                            .format(sql.Literal(table_name),
                                    sql.Literal(str(anom[1])))
            cursor.execute(sql_insert)



def main():
    """Scans through all GROW data to find anomalies. 
    Stores anomalous findings (datetimes of anomalies)
    in AWS Aurora 'grow_anomalies' table.
    """
    conn = create_engine('postgresql+psycopg2://')
    all_tables_array = get_all_grow_tables(conn)
    soil_model, light_model, air_model = get_keras_models()
    for table in all_tables_array:
        predict_soil, predict_light, predict_air, predict_dates = construct_predict_dfs(table[0], conn)
        mse_soil, mse_light, mse_air = predict_on_keras_models(predict_soil, predict_light, predict_air,
                                                                soil_model, light_model, air_model)
        anomalous_soil = analyse_soil_error(mse_soil, predict_dates)
        anomalous_light = analyse_light_error(mse_soil, predict_dates)
        anomalous_air = analyse_air_error(mse_soil, predict_dates)
        create_anomaly_table(conn)
        insert_anomalies(anomalous_soil, anomalous_light, anomalous_air)

if __name__ == '__main__':
    main()
