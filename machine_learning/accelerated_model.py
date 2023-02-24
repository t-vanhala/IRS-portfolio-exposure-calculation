"""
@Authors: Tuomas Vanhala, to speed up neural networks training.
@Date: Jan 2023
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow import GradientTape
from config_utils import *

class AcceleratedModel(keras.Model):
    """
    Builds given sequential model with support for cuDNN implementation. Includes tf.function
    declarations for train_step and test_step.
    """
    def __init__(self, model):
        super(AcceleratedModel, self).__init__()

        self.model = model
        print(self.model.summary())

    # Speedup with tf.function declaration
    @tf.function
    def train_step(self, data):
        x, y = data # unpack data
        with GradientTape() as tape:
            y_pred = self(x, training=True) # Forward pass
            # Compute the loss value
            loss = self.compiled_loss(y, y_pred, regularization_losses=self.losses)

        # Compute gradients
        trainable_vars = self.trainable_variables
        gradients = tape.gradient(loss, trainable_vars)
        # Updates
        self.optimizer.apply_gradients(zip(gradients, trainable_vars))
        self.compiled_metrics.update_state(y, y_pred)
        return {m.name: m.result() for m in self.metrics}

    # Speedup with tf.function declaration
    @tf.function
    def test_step(self, data):
        x, y = data # unpack data
        y_pred = self(x, training=False)
        # Updates
        self.compiled_loss(y, y_pred, regularization_losses=self.losses)
        self.compiled_metrics.update_state(y, y_pred)
        return {m.name: m.result() for m in self.metrics}

    def call(self, inputs):
        return self.model(inputs)
