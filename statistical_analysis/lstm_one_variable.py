import numpy as np
import pandas as pd
import datetime
from sqlalchemy import create_engine
# import matplotlib.pyplot as plt
import tensorflow as tf
import keras
from keras.models import Model, Sequential, load_model
from keras.layers import Input, Dense, LSTM
from sklearn.preprocessing import  StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split

table_name = 'grow_data_0a05p06e'
# table_name = 'grow_data_m65ex1jn' # flatline of light, and wonky sporadic soil_moisture readings ????
table_name = 'grow_data_1zh4hdzr' # flatline of soil moisture @ end
table_name = 'grow_data_4bcqg5xe' # flatline soil moisture @ end
table_name = 'grow_data_8gbfyzmp' # 2 flatline soil moistures 
table_name = 'grow_data_8em4zdze' # all flatline light&soil moisture, temp ok
table_name = 'grow_data_63egxgj1' # light highlines and goes funky then returns to normalcy
table_name = 'grow_data_566xkgq2' # light square peaking at end
table_name = 'grow_data_cyza0e03' # light & soil go funky, temp also weird

table_name = 'grow_data_9ggnsrj8' # all good
table_name = 'grow_data_5rfs4y7n' # all good

table_name = 'grow_data_5pga25ec' # all good
table_name = 'grow_data_5nrha8hq' # all good
table_name = 'grow_data_5kc81f8r' # all good
table_name = 'grow_data_02krq5q5' # all good
table_name = 'grow_data_0srkxe23' # all good
good_tables = ['grow_data_5pga25ec','grow_data_5pga25ec','grow_data_5kc81f8r','grow_data_02krq5q5','grow_data_0srkxe23']
# took 775.566321 Sec. (12min) to train above list of tables on 3 variables
# took 772.855652 Sec. (12min) to train above list of table on 1 variable (!!)

conn = create_engine('postgresql+psycopg2://')

######## FOR PREDICT TABLE ########
table_name = 'grow_data_4bcqg5xe' # flatline soil moisture @ end
table_name = 'grow_data_8em4zdze' # all flatline light&soil moisture, temp ok
table_name = 'grow_data_63egxgj1' # light highlines and goes funky then returns to normalcy
table_name = 'grow_data_566xkgq2' # light square peaking at end
table_name = 'grow_data_cyza0e03' # light & soil go funky

######## FOR SINGLE TABLE ########
sql = f"""SELECT * FROM {table_name}"""
df = pd.read_sql(sql, conn, parse_dates=['datetime'])
# Dataframe is not ordered, sort by datetime
df = df.sort_values(axis=0, by=['datetime'])
scaler = MinMaxScaler()
remainder = len(df) % 96
predict_df = df[remainder:] # df divisible by 96
##################################

######### PREDICT DFS ###########
predict_df_2 = predict_df.copy(deep=True)
predict_df_3 = predict_df.copy(deep=True)
predict_df_4 = predict_df.copy(deep=True)
# predict_dates = predict_df['datetime']
predict_dates_2 = predict_df_4.drop(['sensor_id'], axis=1).drop(['soil_moisture'], axis=1).drop(['light'], axis=1).drop(['air_temperature'], axis=1)
predict_df_soil = predict_df.drop(['sensor_id'], axis=1).drop(['datetime'], axis=1).drop(['light'], axis=1).drop(['air_temperature'], axis=1)
predict_df_light = predict_df_2.drop(['sensor_id'], axis=1).drop(['datetime'], axis=1).drop(['soil_moisture'], axis=1).drop(['air_temperature'], axis=1)
predict_df_air = predict_df_3.drop(['sensor_id'], axis=1).drop(['datetime'], axis=1).drop(['soil_moisture'], axis=1).drop(['light'], axis=1)
predict_df_soil_scaled = scaler.fit_transform(predict_df_soil)
predict_df_light_scaled = scaler.fit_transform(predict_df_light)
predict_df_air_scaled = scaler.fit_transform(predict_df_air)
timesteps = 96
dim = 1
samples = len(predict_df_soil_scaled)
predict_df_soil_scaled.shape = (int(samples/timesteps),timesteps,dim)
predict_df_light_scaled.shape = (int(samples/timesteps),timesteps,dim)
predict_df_air_scaled.shape = (int(samples/timesteps),timesteps,dim)
# samples = len(predict_dates)
predict_dates_array = predict_dates.values
predict_dates_array.shape = (int(samples/timesteps),timesteps,dim)

predictions_soil = model_soil.predict(predict_df_soil_scaled)
mse_soil = np.mean(np.power(predict_df_soil_scaled - predictions_soil, 2), axis=1)

predictions_light = model_light.predict(predict_df_light_scaled)
mse_light = np.mean(np.power(predict_df_light_scaled - predictions_light, 2), axis=1)

predictions_air = model_air.predict(predict_df_air_scaled)
mse_air = np.mean(np.power(predict_df_air_scaled - predictions_air, 2), axis=1)

######## FOR LIST OF TABLES ########
big_df = pd.DataFrame()
for table in good_tables:
    df = pd.read_sql(f"SELECT * FROM {table}", conn, parse_dates=['datetime'])
    df = df.sort_values(axis=0, by=['datetime'])
    big_df = pd.concat([big_df, df])

# Make big_df divisible by 96, 96 observations per day
scaler = MinMaxScaler()
remainder = len(big_df) % 96
new_df = big_df[remainder:] 
####################################

# Copy 2 new dfs for light and air temp GROW variables
new_df_2 = new_df.copy(deep=True)
new_df_3 = new_df.copy(deep=True)

# Drop extra columns so each df has one column each
new_dates = new_df['datetime']
new_df_soil = new_df.drop(['sensor_id'], axis=1).drop(['datetime'], axis=1).drop(['light'], axis=1).drop(['air_temperature'], axis=1)
new_df_light = new_df_2.drop(['sensor_id'], axis=1).drop(['datetime'], axis=1).drop(['soil_moisture'], axis=1).drop(['air_temperature'], axis=1)
new_df_air = new_df_3.drop(['sensor_id'], axis=1).drop(['datetime'], axis=1).drop(['soil_moisture'], axis=1).drop(['light'], axis=1)
# new_df_soil.columns
# Index(['soil_moisture'], dtype='object')
new_df_soil_scaled = scaler.fit_transform(new_df_soil)
new_df_light_scaled = scaler.fit_transform(new_df_light)
new_df_air_scaled = scaler.fit_transform(new_df_air)
timesteps = 96
dim = 1
samples = len(new_df_soil_scaled)
new_df_soil_scaled.shape = (int(samples/timesteps),timesteps,dim)
new_df_light_scaled.shape = (int(samples/timesteps),timesteps,dim)
new_df_air_scaled.shape = (int(samples/timesteps),timesteps,dim)



predictions5 = model.predict(new_df_soil_scaled)
mse5 = np.mean(np.power(new_df_soil_scaled - predictions5, 2), axis=1)



# Plot the 3 variables to visualize
size = len(df)
fig, ax = plt.subplots(num=None, figsize=(14, 6), dpi=80, facecolor='w', edgecolor='k')
ax.plot(range(0,size), df['soil_moisture'], 'o', color='blue', linewidth=1, label='soil_moisture')
ax.plot(range(0,size), df['light'], 'o', color='red', linewidth=1, label='light')
ax.plot(range(0,size), df['air_temperature'], 'o', color='green', linewidth=1, label='air_temperature')
legend = ax.legend(loc='upper center', shadow=True, fontsize='x-large')


model_soil = Sequential()
model_soil.add(LSTM(50,batch_input_shape=(batch_size,timesteps,dim),return_sequences=True,stateful=True))
model_soil.add(LSTM(50,batch_input_shape=(batch_size,timesteps,dim),return_sequences=True,stateful=True))
model_soil.add(LSTM(50,batch_input_shape=(batch_size,timesteps,dim),return_sequences=True,stateful=True))
model_soil.add(LSTM(50,batch_input_shape=(batch_size,timesteps,dim),return_sequences=True,stateful=True))
model_soil.add(Dense(1))
model_soil.compile(loss='mse', optimizer='adam')


model_soil = Sequential()
model_soil.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model_soil.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model_soil.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model_soil.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model_soil.add(Dense(1))
model_soil.compile(loss='mse', optimizer='adam') # starts and finishes with less val_loss & loss
# model.compile(loss='mae', optimizer='adam') # compared to mae loss parameter
# prediction mse is slightly less with 'mse' loss parameter
########
# model & predictions performed MUCH better when the train&test datasets were
# divisible by 96 and there was no observation gap between them

model_light = Sequential()
model_light.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model_light.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model_light.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model_light.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model_light.add(Dense(1))
model_light.compile(loss='mse', optimizer='adam')

model_air = Sequential()
model_air.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model_air.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model_air.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model_air.add(LSTM(50,input_shape=(timesteps,dim),return_sequences=True))
model_air.add(Dense(1))
model_air.compile(loss='mse', optimizer='adam')

nb_epoch = 100
batch_size = 32

nb_epoch = 100
batch_size = 1

# Model trained on soil moisture data
start_time = datetime.datetime.now()
history_soil = model_soil.fit(new_df_soil_scaled, new_df_soil_scaled,
                        epochs=nb_epoch,
                        batch_size=batch_size,
                        shuffle=True,
                        validation_split=0.1,
                        verbose=0
                        )
end_time = datetime.datetime.now()
print('Time to run the model: {} Sec.'.format((end_time - start_time).total_seconds()))
df_history_soil = pd.DataFrame(history_soil.history)

# Model trained on light data
start_time = datetime.datetime.now()
history_light = model_light.fit(new_df_light_scaled, new_df_light_scaled,
                        epochs=nb_epoch,
                        batch_size=batch_size,
                        shuffle=True,
                        validation_split=0.1,
                        verbose=0
                        )
end_time = datetime.datetime.now()
print('Time to run the model: {} Sec.'.format((end_time - start_time).total_seconds()))
df_history_light = pd.DataFrame(history_light.history)

# Model trained on air temperature data
start_time = datetime.datetime.now()
history_air = model_air.fit(new_df_air_scaled, new_df_air_scaled,
                        epochs=nb_epoch,
                        batch_size=batch_size,
                        shuffle=True,
                        validation_split=0.1,
                        verbose=0
                        )
end_time = datetime.datetime.now()
print('Time to run the model: {} Sec.'.format((end_time - start_time).total_seconds()))
df_history_air = pd.DataFrame(history_air.history)







predictions = model.predict(new_df_soil_scaled)
mse = np.mean(np.power(new_df_soil_scaled - predictions, 2), axis=1)

# Plot training and validation loss to check for over/underfitting
loss = df_history_air['loss']
val_loss = df_history_air['val_loss']
epochs = range(nb_epoch)
plt.figure()
plt.plot(epochs, loss, 'b', label='Training loss')
plt.plot(epochs, val_loss, 'r', label='Validation loss')
plt.title('Training and validation loss')
plt.legend()
plt.show()

predictions = model.predict(X_train_scaled)
# Reconstruction Error
mse = np.mean(np.power(X_train_scaled - predictions, 2), axis=1)

predictions2 = model.predict(X_test_scaled)
prediction2_diff = X_test_scaled - predictions2
mse2 = np.mean(np.power(X_test_scaled - predictions2, 2), axis=1)


# Conclusion after 2 sets of runs 32 versus 96 batch size:
# 32 takes twice as long, but model performs better and predicts better

# batch_size = 32 (5 96/2/2 LSTM layers) took 81.720021 Sec.
#                                             80.21589 Sec.
# batch_size = 32 (5 50 LSTM layers) took 85.752646 Sec.
# batch_size = 32 (5 50 LSTM layers) 55k df took 363.238711 Sec.
# batch_size = 32 (4 50 LSTM layers) took 63.534043 Sec.
#                                         66.289958 Sec.
#                                         62.486536 Sec.
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

# df_history - 4 50 LSTM layers
# 32 val_loss      loss
# 0   0.055516  0.115401
# 99  0.001224  0.003543

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




