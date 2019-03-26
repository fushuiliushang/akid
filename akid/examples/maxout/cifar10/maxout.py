from __future__ import absolute_import
from akid import AKID_DATA_PATH
from akid.core import kids, kongfus
from akid import Cifar10TFSource
from akid import IntegratedSensor
from akid import WhitenJoker
from akid import Brain
from akid.layers import (
    ConvolutionLayer,
    PoolingLayer,
    ReLULayer,
    InnerProductLayer,
    SoftmaxWithLossLayer,
    BatchNormalizationLayer,
    DropoutLayer,
    MaxoutLayer
)

# Set up brain
# #########################################################################
brain = Brain(moving_average_decay=0.99, name='maxout-relu-cifar10')

brain.attach(ConvolutionLayer([8, 8],
                              [1, 1, 1, 1],
                              'SAME',
                              stddev=0.005,
                              weight_decay=0.0005,
                              out_channel_num=192,
                              name='conv1'))
brain.attach(PoolingLayer([1, 4, 4, 1],
                          [1, 2, 2, 1],
                          'SAME',
                          name='pool1'))
brain.attach(MaxoutLayer(name='maxout1'))
brain.attach(DropoutLayer(keep_prob=0.8, name='dropout1'))

brain.attach(ConvolutionLayer([8, 8],
                              [1, 1, 1, 1],
                              'SAME',
                              stddev=0.005,
                              weight_decay=0.0005,
                              out_channel_num=384,
                              name='conv2'))
brain.attach(PoolingLayer([1, 4, 4, 1],
                          [1, 2, 2, 1],
                          'SAME',
                          name='pool2'))
brain.attach(MaxoutLayer(name='maxout2'))
brain.attach(DropoutLayer(keep_prob=0.5, name='dropout2'))

brain.attach(ConvolutionLayer([5, 5],
                              [1, 1, 1, 1],
                              'SAME',
                              stddev=0.005,
                              weight_decay=0.0005,
                              out_channel_num=384,
                              name='conv3'))
brain.attach(PoolingLayer([1, 2, 2, 1],
                          [1, 2, 2, 1],
                          'SAME',
                          name='pool3'))
brain.attach(MaxoutLayer(name='maxout3'))
brain.attach(DropoutLayer(keep_prob=0.5, name='dropout3'))

brain.attach(InnerProductLayer(stddev=0.005,
                               weight_decay=0.004,
                               out_channel_num=500,
                               name='ip1'))
brain.attach(MaxoutLayer(group_size=5, name='maxout4'))
brain.attach(DropoutLayer(keep_prob=0.3, name='dropout3'))

brain.attach(InnerProductLayer(stddev=1/500.0,
                               weight_decay=0,
                               out_channel_num=10,
                               name='softmax_linear'))

brain.attach(SoftmaxWithLossLayer(class_num=10, name='loss'))

# Set up a sensor.
# #########################################################################
cifar_source = Cifar10TFSource(
    name="CIFAR10",
    url='http://www.cs.toronto.edu/~kriz/cifar-10-binary.tar.gz',
    work_dir=AKID_DATA_PATH + '/cifar10',
    num_train=50000,
    num_val=10000)


sensor = IntegratedSensor(source_in=cifar_source,
                          batch_size=128,
                          name='data')
sensor.attach(WhitenJoker(name="per_image_whitening"), to_val=True)
sensor.attach(WhitenJoker(name="per_image_whitening"))

# Summon a survivor.
# #########################################################################
survivor = kids.Kid(
    sensor,
    brain,
    kongfus.MomentumKongFu(base_lr=0.01,
                           momentum=0.5,
                           decay_rate=0.1,
                           decay_epoch_num=50),
    max_steps=510000)

# Start training
# #######################################################################
survivor.practice(continue_from_chk_point=False)
