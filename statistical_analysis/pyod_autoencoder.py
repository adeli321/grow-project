import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from pyod.models.auto_encoder import AutoEncoder
from sklearn.preprocessing import  StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split

table_name = 'grow_data_0a05p06e'
sql = f"""SELECT * FROM {table_name}"""
conn = create_engine('')
df = pd.read_sql(sql, conn, parse_dates=['datetime'])

RANDOM_SEED = 101
X_train, X_test = train_test_split(df, test_size=0.1, random_state=RANDOM_SEED)

X_train = X_train.drop(['sensor_id'], axis=1)
train_dates = X_train['datetime']
X_train = X_train.drop(['datetime'], axis=1)

X_test = X_test.drop(['sensor_id'], axis=1)
test_dates = X_test['datetime']
X_test = X_test.drop(['datetime'], axis=1)

X_train = X_train.values
X_test  = X_test.values

scaler = MinMaxScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.fit_transform(X_test)

clf = AutoEncoder(hidden_neurons=[2,1,2], verbose=0, contamination=0.05)
clf.fit(X_train_scaled)
df_history = pd.DataFrame(clf.history_)


