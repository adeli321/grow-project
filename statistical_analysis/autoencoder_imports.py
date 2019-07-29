import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_row', None)
import matplotlib.pyplot as plt
plt.rcdefaults()
from pylab import rcParams
import seaborn as sns
import sqlalchemy
from sqlalchemy import create_engine
# %matplotlib inline
import datetime
#################
#######Ploltly
import plotly
import plotly.plotly as py
import plotly.offline as pyo
import plotly.figure_factory as ff
from   plotly.tools import FigureFactory as FF, make_subplots
import plotly.graph_objs as go
from   plotly.graph_objs import *
from   plotly import tools
from   plotly.offline import download_plotlyjs, init_notebook_mode, iplot
# import cufflinks as cf
init_notebook_mode(connected=True)
# cf.go_offline()
pyo.offline.init_notebook_mode()
####### Deep learning libraries
import tensorflow as tf
import keras
from keras.models import Model, load_model
from keras.layers import Input, Dense
from keras.callbacks import ModelCheckpoint, TensorBoard
from keras import regularizers
# from ann_visualizer.visualize import ann_viz
# 
from sklearn.preprocessing import  StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split



table_name = 'grow_data_0a05p06e'
sql = f"""SELECT * FROM {table_name}"""
conn = create_engine('')

df = pd.read_sql(sql, conn)
df = pd.read_sql(sql, conn, parse_dates=['datetime'])

RANDOM_SEED = 101

# Split the data into training (90%) and testing (10%)
X_train, X_test = train_test_split(df, test_size=0.1, random_state=RANDOM_SEED)

# Preprocessing need to customize to my data
# Only use data labeled as 0 (normal)
# X_train = X_train[X_train['Label'] == 0]
X_train = X_train.drop(['sensor_id'], axis=1)
train_dates = X_train['datetime']
X_train = X_train.drop(['datetime'], axis=1)

# y_test  = X_test['Label']
X_test = X_test.drop(['sensor_id'], axis=1)
test_dates = X_test['datetime']
X_test = X_test.drop(['datetime'], axis=1)
X_train = X_train.values
X_test  = X_test.values
print('Training data size   :', X_train.shape)
print('Validation data size :', X_test.shape)

scaler = MinMaxScaler()
# Fit = compute the minimum and maximum to be used for later scaling
# Fit_transform = fit to data, then transform it, return array
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.fit_transform(X_test)
# X_test_scaled  = scaler.transform(X_test)


# No of Neurons in each Layer [3,2,1,2,3]
input_dim = X_train.shape[1]
# encoding_dim = 2

input_layer = Input(shape=(input_dim, ))
encoder = Dense(2, activation="tanh",activity_regularizer=regularizers.l1(10e-5))(input_layer)
encoder = Dense(1, activation="tanh")(encoder)
decoder = Dense(2, activation='tanh')(encoder)
decoder = Dense(input_dim, activation='tanh')(decoder)
autoencoder = Model(inputs=input_layer, outputs=decoder)
autoencoder.summary()

# No of Neurons in each Layer [9,6,3,2,3,6,9]
# input_layer = Input(shape=(input_dim, ))
# encoder = Dense(encoding_dim, activation="tanh",activity_regularizer=regularizers.l1(10e-5))(input_layer)
# encoder = Dense(int(encoding_dim / 2), activation="tanh")(encoder)
# encoder = Dense(int(2), activation="tanh")(encoder)
# decoder = Dense(int(encoding_dim/ 2), activation='tanh')(encoder)
# decoder = Dense(int(encoding_dim), activation='tanh')(decoder)
# decoder = Dense(input_dim, activation='tanh')(decoder)
# autoencoder = Model(inputs=input_layer, outputs=decoder)
# autoencoder.summary()

# Use autoencoder NN model to identify outliers in new dataset
# The higher the RE (reconstruction error) for a data point, 
# the higher the chance that the data point is an outlier

nb_epoch = 100
batch_size = 50
autoencoder.compile(optimizer='adam', loss='mse' )
start_time = datetime.datetime.now()
history = autoencoder.fit(X_train_scaled, X_train_scaled,
                        epochs=nb_epoch,
                        batch_size=batch_size,
                        shuffle=True,
                        validation_split=0.1,
                        verbose=0
                        )
end_time = datetime.datetime.now()
print('Time to run the model: {} Sec.'.format((end_time - start_time).total_seconds()))
df_history = pd.DataFrame(history.history)

predictions = autoencoder.predict(X_test_scaled)
mse = np.mean(np.power(X_test_scaled - predictions, 2), axis=1)



