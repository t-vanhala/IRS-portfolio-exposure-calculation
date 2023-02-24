"""
@Authors: Tuomas Vanhala, declarations for machine learning models initialization and usage.
Based on https://github.com/frodiie/Credit-Exposure-Prediction-GRU
@Date: Dec 2022
"""

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.utils import Sequence
from tensorflow.keras.layers import Dense, GRU, LSTM
from tensorflow.keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint
from sklearn.ensemble import RandomForestRegressor
from accelerated_model import *

def get_random_forest():
    """
    Returns the random forest model.
    """
    return RandomForestRegressor(n_estimators=100, max_depth=None, n_jobs=-1, random_state=37, warm_start=True)

def do_build(model):
    """
    Can be used for tensorflow models when there is a need to build the model before loading it with custom
    function implementations.
    """
    model.build((None, MAX_PORTFOLIO_LIFETIME_MONTHS, NBR_FEATURES))
    return model

def compile_model_gru(layers: int, units: list, learning_rate: float):
    """
    Returns GRU network architecture. Support cuDNN implementation in GRU layers.
    ARGS:
        layers (int):                     nbr of layers.
        units (list):                     nbr of units/layer.
        learning_rate (float):            Adam learning rate
    """
    input_seq_len = MAX_PORTFOLIO_LIFETIME_MONTHS
    output_seq_len = MAX_PORTFOLIO_LIFETIME_MONTHS
    nbr_features = NBR_FEATURES

    model = Sequential()
    for layer in range(0, layers - 2):
        model.add(GRU(units[layer],
                      return_sequences = True,
                      input_shape = (input_seq_len, nbr_features)))
    model.add(GRU(units[layer + 1], input_shape = (input_seq_len, nbr_features)))
    model.add(Dense(output_seq_len))

    model = AcceleratedModel(model)
    opt = Adam(learning_rate=learning_rate)
    model.compile(optimizer=opt, loss='mse', metrics=[tf.keras.metrics.MeanAbsoluteError()])
    return model

def compile_model_lstm(layers: int, units: list, learning_rate: float):
    """
    Returns LSTM network architecture. Support cuDNN implementation in LSTM layers.
    ARGS:
        layers (int):                     nbr of layers.
        units (list):                     nbr of units/layer.
        learning_rate (float):            Adam learning rate
    """
    input_seq_len = MAX_PORTFOLIO_LIFETIME_MONTHS
    output_seq_len = MAX_PORTFOLIO_LIFETIME_MONTHS
    nbr_features = NBR_FEATURES

    model = Sequential()
    for layer in range(0, layers - 2):
        model.add(LSTM(units[layer],
                      return_sequences = True,
                      input_shape = (input_seq_len, nbr_features)))
    model.add(LSTM(units[layer + 1], input_shape = (input_seq_len, nbr_features)))
    model.add(Dense(output_seq_len))

    model = AcceleratedModel(model)
    opt = Adam(learning_rate=learning_rate)
    model.compile(optimizer=opt, loss='mse', metrics=[tf.keras.metrics.MeanAbsoluteError()])
    return model

def train_model(train_batch_gen: Sequence, val_batch_gen: Sequence,
                epochs: int, model_filepath, model):
    """
    Returns trained model and training history.

    ARGS:
        train_batch_gen (keras.utils.Sequence): training data generator.
        val_batch_gen (keras.utils.Sequence):   validation data generator.
        epochs (int):                           nbr of epochs
        model:                                  custom model architecture.
    """
    if val_batch_gen is not None and model_filepath is not None:
        checkpoint = ModelCheckpoint(model_filepath,
                                    monitor='val_loss',
                                    verbose=1,
                                    save_best_only=True,
                                    mode='auto',
                                    save_weights_only=True,
                                    period=1)

        history = model.fit(train_batch_gen,
                            epochs = epochs,
                            validation_data = val_batch_gen,
                            verbose = 1,
                            callbacks = [checkpoint],
                            use_multiprocessing = True)
    else:
        # Used in the k-fold cross validation
        history = model.fit(train_batch_gen,
                            epochs = epochs,
                            verbose = 1,
                            use_multiprocessing = True)
    return model, history
