"""
@Authors: Tuomas Vanhala, use Keras tuner for the GRU and LSTM models
@Date: Dec 2022
"""

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, GRU, LSTM
from tensorflow.keras.optimizers import Adam
from config_utils import *

def build_tuning_model_gru(hp):
    """
    Use keras tuner for the GRU model
    """
    model = Sequential()
    for i in range(hp.Int('layers', 1, 3)):
        model.add(GRU(units=hp.Int('units_' + str(i), 32, 128, step=32),
                      return_sequences = True, 
                      input_shape = (MAX_PORTFOLIO_LIFETIME_MONTHS, NBR_FEATURES)))
    model.add(GRU(units=hp.Int('units_' + str(i), 32, 128, step=32),
                  input_shape = (MAX_PORTFOLIO_LIFETIME_MONTHS, NBR_FEATURES)))
    model.add(Dense(MAX_PORTFOLIO_LIFETIME_MONTHS))
    model.compile(optimizer=Adam(hp.Choice('learning_rate', values=[0.01, 0.001, 0.0001])), loss='mse')
    return model

def build_tuning_model_lstm(hp):
    """
    Use keras tuner for the LSTM model
    """
    model = Sequential()
    for i in range(hp.Int('layers', 1, 3)):
        model.add(LSTM(units=hp.Int('units_' + str(i), 32, 128, step=32),
                      return_sequences = True, 
                      input_shape = (MAX_PORTFOLIO_LIFETIME_MONTHS, NBR_FEATURES)))
    model.add(LSTM(units=hp.Int('units_' + str(i), 32, 128, step=32),
                  input_shape = (MAX_PORTFOLIO_LIFETIME_MONTHS, NBR_FEATURES)))
    model.add(Dense(MAX_PORTFOLIO_LIFETIME_MONTHS))
    model.compile(optimizer=Adam(hp.Choice('learning_rate', values=[0.01, 0.001, 0.0001])), loss='mse')
    return model
