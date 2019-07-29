import numpy as np
import pandas as pd
import datetime
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import tensorflow as tf
import keras
from keras.models import Model, Sequential, load_model
from keras.layers import Input, Dense, LSTM
from sklearn.preprocessing import  StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split

table_name = 'grow_data_0a05p06e'
sql = f"""SELECT * FROM {table_name}"""
conn = create_engine('')
df = pd.read_sql(sql, conn, parse_dates=['datetime'])
# Dataframe is not ordered, sort by datetime
df = df.sort_values(axis=0, by=['datetime'])

# Calculate 90th percentile of df divisible by 96 observations
# to be the training data subset
# Remainder of df is the test data subset
ninety_percentile = int((len(df)/96)*0.90)
ninety_index = ninety_percentile * 96
X_train = df[:ninety_index]
X_test = df[ninety_index:]
# Remove trailing observations to make sure test subset
# of data is divisible by 96
tenth_remainder = len(X_test) % 96
X_test = X_test[:len(X_test)-tenth_remainder]

# Split the data into training (90%) and testing (10%)
# RANDOM_SEED = 101
# X_train, X_test = train_test_split(df, test_size=0.1, random_state=RANDOM_SEED)

# Plot the 3 variables to visualize
size = len(df)
fig, ax = plt.subplots(num=None, figsize=(14, 6), dpi=80, facecolor='w', edgecolor='k')
ax.plot(range(0,size), df['soil_moisture'], 'o', color='blue', linewidth=1, label='soil_moisture')
ax.plot(range(0,size), df['light'], 'o', color='red', linewidth=1, label='light')
ax.plot(range(0,size), df['air_temperature'], 'o', color='green', linewidth=1, label='air_temperature')
legend = ax.legend(loc='upper center', shadow=True, fontsize='x-large')

# Drop sensor_id & datetime columns, store datetimes in separate array
train_dates = X_train['datetime']
X_train = X_train.drop(['sensor_id'], axis=1)
X_train = X_train.drop(['datetime'], axis=1)
test_dates = X_test['datetime']
X_test = X_test.drop(['sensor_id'], axis=1)
X_test = X_test.drop(['datetime'], axis=1)
X_train = X_train.values
X_test = X_test.values

# Normalize data to lie between (0,1)
scaler = MinMaxScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.fit_transform(X_test)

# Calculate remainder of a full day's worth observations (96)
# X_train_remainder = len(X_train_scaled) % 96
# X_test_remainder = len(X_test_scaled) % 96

# Remove the remainder observations from array
# to ensure each observation window is exactly one day of observations
# X_train_scaled = X_train_scaled[:len(X_train_scaled)-X_train_remainder]
# X_test_scaled = X_test_scaled[:len(X_test_scaled)-X_test_remainder]

# Divy up observations into one day windows of time
# X_train_scaled.shape = (7104, 3)
timesteps = 96
dim = 3
samples = len(X_train_scaled)
X_train_scaled.shape = (int(samples/timesteps),timesteps,dim)
# X_train_scaled.shape = (74, 96, 3)

samples = len(X_test_scaled)
X_test_scaled.shape = (int(samples/timesteps),timesteps,dim)

model = Sequential()
model.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model.add(Dense(3))
model.compile(loss='mse', optimizer='adam') # starts and finishes with less val_loss & loss
# model.compile(loss='mae', optimizer='adam') # compared to mae loss parameter
# prediction mse is slightly less with 'mse' loss parameter
########
# model & predictions performed MUCH better when the train&test datasets were
# divisible by 96 and there was no observation gap between them

nb_epoch = 100
batch_size = 32
# Conclusion after 2 sets of runs 32 versus 96 batch size:
# 32 takes twice as long, but model performs better and predicts better

# batch_size = 32 (5 96/2/2 LSTM layers) took 81.720021 Sec.
#                                             80.21589 Sec.
# batch_size = 32 (5 50 LSTM layers) took 85.752646 Sec.
# batch_size = 32 (4 50 LSTM layers) took 63.534043 Sec.
#                                         66.289958 Sec.
# batch_size = 96 (4 50 LSTM layers) took 30.50511 Sec.
#                                         33.106675 Sec.

# df_history - 5 96/2/2 LSTM layers
# 32 val_loss      loss
# 0   0.068745  0.126029
# 99  0.002147  0.003971
# mse is a bit bigger than that of 4 50 LSTM layers

# df_history - 5 96/2/2 LSTM layers
# 32 val_loss      loss
# 0   0.061319  0.122805
# 99  0.001662  0.003950

# df_history - 5 50 LSTM layers
# 32 val_loss      loss
# 0   0.064096  0.124795
# 99  0.001596  0.004357

# df_history3 - 4 50 LSTM layers
# 32 val_loss      loss
# 0   0.065078  0.125813
# 99  0.001556  0.004012
# mse generally less for soil_moisture, air_temp, about equal for light

# df_history5 - 4 50 LSTM layers
# 32 val_loss      loss
# 0   0.062452  0.128161
# 99  0.001678  0.004139
# mse6-mse5 : mse5 generally less for soil_moisture, air_temp, equal for light

# df_history4 - 4 50 LSTM layers
# 96 val_loss      loss
# 0   0.083342  0.131676
# 99  0.003545  0.007538

# df_history6 - 4 50 LSTM layers
# 96 val_loss      loss
# 0   0.078225  0.129254
# 99  0.003618  0.007467

start_time = datetime.datetime.now()
history = model.fit(X_train_scaled, X_train_scaled,
                        epochs=nb_epoch,
                        batch_size=batch_size,
                        shuffle=True,
                        validation_split=0.1,
                        verbose=0
                        )
end_time = datetime.datetime.now()
print('Time to run the model: {} Sec.'.format((end_time - start_time).total_seconds()))
df_history = pd.DataFrame(history.history)

predictions = model.predict(X_train_scaled)
mse3 = np.mean(np.power(X_train_scaled - predictions, 2), axis=1)

predictions = model.predict(X_test_scaled)
mse4 = np.mean(np.power(X_test_scaled - predictions, 2), axis=1)




