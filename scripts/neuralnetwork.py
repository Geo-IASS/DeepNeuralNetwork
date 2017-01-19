#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# neuralnetwork.py
#

import numpy as np
import matplotlib.pyplot as plt
from enum import Enum
from collections import OrderedDict
from load_image_data import LoadImageData
from nnoperations import NNOperations
from layers import ReLULayer
from layers import SigmoidLayer
from layers import HiddenLayer
from layers import SoftmaxWithLossLayer
from layers import ConvolutionLayer
from layers import PoolingLayer
from layers import DropoutLayer
from optimizers import Optimizer
from optimizers import OptimizationMethod


class NeuralNetwork(NNOperations):
    __activation_type__ = None
    PARAMS_KEYS = ('W1', 'b1', 'W2', 'b2')

    def __init__(
            self, input_size, hidden_size, output_size, init_weight=0.01):
        self.input_size = input_size
        self.params = {}
        self.params['W1'] = init_weight * np.random.randn(
            input_size, hidden_size)
        self.params['b1'] = np.zeros(hidden_size)
        self.params['W2'] = init_weight * np.random.randn(
            hidden_size, output_size)
        self.params['b2'] = np.zeros(output_size)

        # setup layers
        self.layers = OrderedDict()
        self.layers['Hidden1'] = HiddenLayer(
            self.params['W1'], self.params['b1'])
        self.layers['ReLU1'] = ReLULayer()
        self.layers['Hidden2'] = HiddenLayer(
            self.params['W2'], self.params['b2'])
        self.lastLayer = SoftmaxWithLossLayer()

    def forward(self, x):
        """Forward propagation.

        x: input data
        """
        for key, layer in self.layers.items():
            x = layer.forward(x)
        return x

    def computeCost(self, y, t):
        """Compute Cost.

        y: output result
        t: labeled data
        """
        return self.lastLayer.forward(y, t)

    def computeAccuracy(self, x, labels):
        """Compute Accuracy.
        """
        x = self.forward(x)
        ans = np.argmax(x, axis=1)
        if labels.ndim != 1:
            label = np.argmax(labels, axis=1)
        accuracy = np.sum(ans == label) / float(x.shape[0])
        return accuracy

    def computeGradientWithBackPropagation(self, x, t):
        """Compute Gradient with Back Propagation.

        x: input data
        t: labeled data
        """

        # forward
        self.computeCost(self.forward(x), t)

        # backward
        layers = list(self.layers.values())
        layers.append(self.lastLayer)
        layers.reverse()
        dout = 1
        for layer in layers:
            dout = layer.backward(dout)

        grads = {}
        grads['W1'] = self.layers['Hidden1'].dW
        grads['b1'] = self.layers['Hidden1'].db
        grads['W2'] = self.layers['Hidden2'].dW
        grads['b2'] = self.layers['Hidden2'].db

        return grads

    def fit(
            self,
            train_images,
            train_labels,
            test_images,
            test_labels,
            optimization_method=OptimizationMethod.Adam,
            optimization_params={
                'learning_rate': 0.01,
                'momentum': 0.9,
                'beta1': 0.9,
                'beta2': 0.999},
            iters_num=10000,
            mini_batch_size=100,
            samples_num_evaluated_per_epoc=100):
        """Fits weight paramters by using optimization algorithm.
        """

        costs = []
        train_accuracies = []
        test_accuracies = []

        ITERS_NUM = iters_num
        MINI_BATCH_SIZE = mini_batch_size
        TRAIN_IMAGES_NUM = train_images.shape[0]
        ITER_PER_EPOC = max(TRAIN_IMAGES_NUM/MINI_BATCH_SIZE, 1)

        optimizer = Optimizer().optimizer(
            optimization_method=optimization_method,
            learning_rate=optimization_params.get('learning_rate'),
            momentum=optimization_params.get('momentum'),
            beta1=optimization_params.get('beta1'),
            beta2=optimization_params.get('beta2'),
            )

        for i in range(ITERS_NUM):
            batch_mask = np.random.choice(TRAIN_IMAGES_NUM, MINI_BATCH_SIZE)
            x_batch = train_images[batch_mask]
            t_batch = train_labels[batch_mask]

            grads = nn.computeGradientWithBackPropagation(x_batch, t_batch)
            optimizer.update(nn.params, grads)

            costs.append(nn.computeCost(nn.forward(x_batch), t_batch))
            print('cost {}'.format(costs[-1]))

            # check accuracy
            if i % ITER_PER_EPOC == 0:
                print('=========ITERATION {}=========='.format(i))
                if samples_num_evaluated_per_epoc is None:
                    samples_num_evaluated_per_epoc = -1
                train_accuracies.append(
                    nn.computeAccuracy(
                        train_images[:samples_num_evaluated_per_epoc],
                        train_labels[:samples_num_evaluated_per_epoc]))
                test_accuracies.append(
                    nn.computeAccuracy(
                        test_images[:samples_num_evaluated_per_epoc],
                        test_labels[:samples_num_evaluated_per_epoc]))
                print("train accuracy {}, test accuracy {}".format(
                    train_accuracies[-1], test_accuracies[-1]))

        return costs, train_accuracies, test_accuracies

#    def showActivationsDistribution(self, X):
#
#        activation_layer = self.activationLayer()
#
#        activations = []
#        # calculate activations
#        for i, init_weight in enumerate(self.init_weights):
#            print('{} {}'.format(i, init_weight.shape))
#            # TODO: X, w のshapeを合わせるには通過信号を記録する必要がある
#            activations.append(
#                activation_layer.forward(
#                    np.dot(X, init_weight)))
#
#        # plot histgram
#        for i, activation in enumerate(activations):
#            plt.subplot(1, len(activations), i+1)
#            plt.title("layer {}".format(i+1))
#            if i != 0:
#                plt.yticks([], [])
#                plt.xlim(0.1, 1)
#                plt.ylim(0, 7000)
#            plt.hist(
#                init_weight.flatten(),
#                30,
#                range=(0, 1))
#        plt.show()

    def activationLayerFromType(self, activation_type):
        """Return activation layer from ActivationType.

        Returns an instance of
        - ReLULayer
        - SigmoidLayer
        """
        if activation_type == ActivationType.ReLU:
            return ReLULayer()
        elif activation_type == ActivationType.Sigmoid:
            return SigmoidLayer()

    def activationLayer(self):
        """Returns activation layer of the NN instance.
        """
        return self.activationLayerFromType(self.__activation_type__)

    def activationNameFromType(self, activation_type) -> str:
        """Returns activation name from ActivationType.

        Returns
        - 'ReLU'
        - 'Sigmoid;
        """
        if activation_type == ActivationType.ReLU:
            return 'ReLU'
        elif activation_type == ActivationType.Sigmoid:
            return 'Sigmoid'

    def activationName(self):
        """Returns activation layer of the NN instance.
        """
        return self.activationNameFromType(self.__activation_type__)


class ActivationType(Enum):
    ReLU = 1
    Sigmoid = 2


class ConvolutionNetwork(NeuralNetwork):
    PARAMS_KEYS = ('W1', 'b1', 'W2', 'b2', 'W3', 'b3')

    def __init__(
            self,
            input_size=(1, 28, 28),
            activation_type=ActivationType.ReLU,
            filter_num=30,
            filter_size=5,
            filter_padding=0,
            filter_stride=1,
            hidden_size=100,
            output_size=10,
            init_weight=0.01):

        self.__activation_type__ = activation_type

        convolution_output_size =\
            (input_size[1] - filter_size + 2*filter_padding) /\
            filter_stride + 1
        pooling_output_size =\
            int(filter_num *
                (convolution_output_size / 2) * (convolution_output_size / 2))

        convolution_layer_1 = ConvolutionLayer(
            init_std=self.initialWeightStd(
                filter_num*input_size[0]*filter_size*filter_size),
            filter_num=filter_num,
            channel_num=input_size[0],
            filter_size=filter_size)

        # set params
        self.params = {}
        self.params['W1'] = convolution_layer_1.W
        self.params['b1'] = convolution_layer_1.b
        self.params['W2'] =\
            self.initialWeightStd(
                pooling_output_size*hidden_size) *\
            np.random.randn(
                pooling_output_size, hidden_size)
        self.params['b2'] = np.zeros(hidden_size)
        self.params['W3'] =\
            self.initialWeightStd(
                hidden_size*output_size) *\
            np.random.randn(
                hidden_size, output_size)
        self.params['b3'] = np.zeros(output_size)

        # save init weights
        self.init_weights = []
        self.init_weights.append(self.params['W1'])
        self.init_weights.append(self.params['W2'])
        self.init_weights.append(self.params['W3'])

        # set layers
        self.layers = OrderedDict()
        self.layers['Convolution1'] = convolution_layer_1
        self.layers['ReLU1'] = self.activationLayer()
        self.layers['Pooling1'] = PoolingLayer(pool_h=2, pool_w=2, stride=2)
        self.layers['Hidden1'] = HiddenLayer(
            self.params['W2'], self.params['b2'])
        self.layers['ReLU2'] = self.activationLayer()
        self.layers['Hidden2'] = HiddenLayer(
            self.params['W3'], self.params['b3'])
        self.lastLayer = SoftmaxWithLossLayer()

    def initialWeightStd(self, node_num: int):
        """Returns initial weight std.

        node_num: The number of nodes connected with the weights.

        When the activation type is ..
        ReLU -> He
        Sigmoid -> Xavier
        """
        if self.__activation_type__ == ActivationType.ReLU:
            return np.sqrt(2.0 / node_num)
        elif self.__activation_type__ == ActivationType.Sigmoid:
            return np.sqrt(1.0 / node_num)

    def computeGradientWithBackPropagation(self, x, t):
        """Compute Gradient with Back Propagation.

        x: input data
        t: labeled data
        """

        # forward
        self.computeCost(self.forward(x), t)

        # backward
        layers = list(self.layers.values())
        layers.append(self.lastLayer)
        layers.reverse()
        dout = 1
        for layer in layers:
            dout = layer.backward(dout)

        grads = {}
        grads['W1'] = self.layers['Convolution1'].dW
        grads['b1'] = self.layers['Convolution1'].db
        grads['W2'] = self.layers['Hidden1'].dW
        grads['b2'] = self.layers['Hidden1'].db
        grads['W3'] = self.layers['Hidden2'].dW
        grads['b3'] = self.layers['Hidden2'].db

        return grads


class DeepNeuralNetwork(ConvolutionNetwork):
    """Deep Convolution Neural Network

    *Network Structure

    (Convolution1|filter num x 16, size 3 x 3, padding 1 stride 1)
    (ReLU1)
    (Convolution2|filter num x 16, size 3 x 3, padding 1 stride 1)
    (ReLU2)
    (Pooling1)
    (Convolution3|filter num x 32, size 3 x 3, padding 1 stride 1)
    (ReLU3)
    (Convolution4|filter num x 32, size 3 x 3, padding 2 stride 1)
    (ReLU4)
    (Pooling|H:2, W:2, stride:2)

    (Convolution5|filter num x 64, size 3 x 3, padding 1 stride 1)
    (ReLU5)
    (Convolution6|filter num x 64, size 3 x 3, padding 1 stride 1)
    (ReLU6)
    (Pooling|H:2, W:2, stride:2)

    (Hidden1|hidden size:50)
    (ReLU7)
    (Dropout1)
    (Hidden2|hidden size:50)
    (Dropout2)

    (Softmax)
    """
    def __init__(
            self,
            input_size=(1, 28, 28),
            activation_type=ActivationType.ReLU,
            hidden_size=50,
            output_size=10):

        pass



if __name__ == '__main__':

    # settings
    IMAGE_SIZE = 784
    ITERS_NUM = 100
    MINI_BATCH_SIZE = 100

    # load training and test data
    loader = LoadImageData('mnist')
    train_images, train_labels, test_images, test_labels = loader.load(
        image_size=IMAGE_SIZE,
        should_normalize=True,
        should_flatten=False,
        should_label_be_one_hot=True)

    # create neural network with 784 input dimentions

    # nn = NeuralNetwork(
    #     input_size=IMAGE_SIZE, hidden_size=50, output_size=10)

    nn = ConvolutionNetwork(
        input_size=(1, 28, 28),
        filter_num=30,
        filter_size=5,
        filter_padding=0,
        filter_stride=1,
        hidden_size=100,
        output_size=10,
        init_weight=0.01)

    # learn & update weights
    costs, train_accuracies, test_accuracies = nn.fit(
        train_images=train_images,
        train_labels=train_labels,
        test_images=test_images,
        test_labels=test_labels,
        optimization_method=OptimizationMethod.Adam,
        optimization_params={
            'learning_rate': 0.01,
            'momentum': 0.9,
            'beta1': 0.9,
            'beta2': 0.999},
        iters_num=ITERS_NUM,
        mini_batch_size=MINI_BATCH_SIZE,
        samples_num_evaluated_per_epoc=100)

    plt.plot(np.arange(ITERS_NUM), costs)
    plt.axis([0, ITERS_NUM, 0, np.max(costs)])
    plt.show()

    # check activations distibution

    # nn.showActivationsDistribution(train_images)
