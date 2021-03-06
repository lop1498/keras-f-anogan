from keras.layers import Conv2D, Conv2DTranspose, MaxPool2D, Flatten, Dense, LeakyReLU, BatchNormalization, Reshape, Input
from keras.models import Sequential
import keras
from keras.initializers import RandomNormal
import keras.backend as K
from keras.models import load_model


def wasserstein_loss(y_true, y_pred):
    return -K.mean(y_true * y_pred)


def custom_activation(x):
    return K.tanh(x)/2


class Encoder:
    def __init__(self, image_shape=(32, 32, 1), n_filters=64, z_size=(1, 1, 100),
                 alpha=0.2, lr=0.0003):

        assert image_shape[0] % 8 == 0, "Image shape must be divisible by 8."
        #lr=3.5e-5):
        self.discriminator = load_model('disc.h5', custom_objects={'wasserstein_loss': wasserstein_loss})
        self.generator = load_model('gen.h5', custom_objects={'wasserstein_loss': wasserstein_loss})
        self.image_shape = image_shape
        self.n_filters = n_filters
        self.z_size = z_size
        self.alpha = alpha
        self.lr = lr
        self.weight_init = RandomNormal(mean=0., stddev=0.02)

    def encoder(self):
        model = Sequential()
        model.add(Conv2D(filters=self.n_filters,
                    kernel_size=(4, 4),
                    strides=2,
                    padding='same',
                    use_bias=False,
                    input_shape=self.image_shape,
                    kernel_initializer=self.weight_init))
        model.add(LeakyReLU(self.alpha))
        model.add(BatchNormalization())

        model.add(Conv2D(filters=2 * self.n_filters,
                         kernel_size=(4, 4),
                         strides=2,
                         padding='same',
                         use_bias=False,
                         kernel_initializer=self.weight_init))
        model.add(LeakyReLU(self.alpha))
        model.add(BatchNormalization())

        model.add(Conv2D(filters=2 * self.n_filters,
                         kernel_size=(3, 3),
                         strides=2,
                         padding='same',
                         use_bias=False,
                         kernel_initializer=self.weight_init))
        model.add(LeakyReLU(self.alpha))
        model.add(BatchNormalization())

        model.add(Conv2D(filters=4*self.n_filters,
                    kernel_size=(4, 4),
                    strides=2,
                    padding='same',
                    use_bias=False,
                    kernel_initializer=self.weight_init))
        model.add(LeakyReLU(self.alpha))
        model.add(BatchNormalization())

        model.add(Flatten())
        model.add(Dense(100, activation=custom_activation))
        model.add(Reshape((1,1,100)))

        return model

    def encoder_gen(self, encoder, generator):
        model = Sequential()
        model.add(encoder)
        print(encoder.summary())
        print(generator.summary())
        model.add(generator)

        return model

    def encoder_loss(self):
        intermediate_layer_model = keras.Model(inputs=self.discriminator.input,
                                               outputs=self.discriminator.get_layer("feature_extractor").output)

        def loss(y_true, y_pred):
            l1 = K.mean(K.square(y_pred - y_true))
            l2 = K.mean(K.square(intermediate_layer_model(y_pred) - intermediate_layer_model(y_true)))
            return l1 + l2
        return loss
