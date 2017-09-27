import tensorflow as tf
import computational_graph as cg
from akid.common import SEED


def depthwise_conv2d(input, filter, bias=None, strides=1, padding='VALID', name=None):
    strides = expand_kernel(strides)
    v = tf.nn.depthwise_conv2d(input, filter, strides, padding, name)

    if bias:
        v = tf.nn.bias_add(v, bias)

    return v


def max_pool(value, ksize, strides, padding, data_format="NHWC", name=None):
    ksize = expand_kernel(ksize)
    strides = expand_kernel(strides)
    return tf.nn.max_pool(value, ksize, strides, padding, data_format, name)


def max_pool_with_argmax(input, ksize, strides, padding, Targmax=None, name=None):
    ksize = expand_kernel(ksize)
    strides = expand_kernel(strides)
    return tf.nn.max_pool_with_argmax(input, ksize, strides, padding, Targmax=Targmax, name=name)


def _max_unpooling(X_in, mask, ksize=2, name="unpool"):
    """
    Args:
        X_in: Tensor
            Input to unpool.
        mask:
            Indices output by `tf.nn.max_pool_with_argmax.

    Adopted from: https://github.com/tensorflow/tensorflow/issues/2169
    """
    if isinstance(ksize, int):
        ksize = [1, ksize, ksize, 1]
    input_shape = X_in.get_shape().as_list()
    #  calculation new shape
    output_shape = [input_shape[1] * ksize[1], input_shape[2] * ksize[2], input_shape[3]]
    # calculation indices for batch, height, width and feature maps
    one_like_mask = tf.ones_like(mask)
    bsize = tf.to_int64(tf.shape(X_in)[0])
    batch_range = tf.reshape(tf.range(bsize, dtype=tf.int64),
                             shape=[-1, 1, 1, 1])
    b = one_like_mask * batch_range
    y = mask // (output_shape[1] * output_shape[2])
    x = mask % (output_shape[1] * output_shape[2]) // output_shape[2]
    feature_range = tf.range(output_shape[2], dtype=tf.int64)
    f = one_like_mask * feature_range
    # transpose indices & reshape update values to one dimension
    updates_size = tf.size(X_in)
    indices = tf.transpose(tf.reshape(tf.stack([b, y, x, f]), [4, updates_size]))
    values = tf.reshape(X_in, [updates_size])
    ret = tf.scatter_nd(indices, values, tf.concat(
        [[bsize], tf.to_int64(output_shape)], axis=0))
    return ret


def max_unpooling(X_in, mask, ksize=[1, 2, 2, 1]):
    """
    Does not support partially defined shape. For a tentative version that
    supports dynamic batch size, refer to `_max_pooling`.
    """
    ksize = expand_kernel(ksize)
    input_shape = X_in.get_shape().as_list()
    #  calculation new shape
    output_shape = (input_shape[0], input_shape[1] * ksize[1], input_shape[2] * ksize[2], input_shape[3])
    # calculation indices for batch, height, width and feature maps
    one_like_mask = tf.ones_like(mask)
    batch_range = tf.reshape(tf.range(output_shape[0], dtype=tf.int64), shape=[input_shape[0], 1, 1, 1])
    b = one_like_mask * batch_range
    y = mask // (output_shape[2] * output_shape[3])
    x = mask % (output_shape[2] * output_shape[3]) // output_shape[3]
    feature_range = tf.range(output_shape[3], dtype=tf.int64)
    f = one_like_mask * feature_range
    # transpose indices & reshape update values to one dimension
    updates_size = tf.size(X_in)
    indices = tf.transpose(tf.reshape(tf.stack([b, y, x, f]), [4, updates_size]))
    values = tf.reshape(X_in, [updates_size])
    X_out = tf.scatter_nd(indices, values, output_shape)

    return X_out


def relu(X_in, name=None):
    return tf.nn.relu(X_in, name)


def conv2d(input, filter, bias=None, strides=1, padding="VALID", name=None):
    strides = expand_kernel(strides)

    if bias is not None:
        v = tf.nn.conv2d(input, filter,
                         strides, padding,
                         use_cudnn_on_gpu=None, data_format=None)
        v = tf.nn.bias_add(v, bias, name=name)
    else:
        v = tf.nn.conv2d(input, filter,
                         strides, padding,
                         use_cudnn_on_gpu=None, data_format=None,
                         name=name)

    return v


def inner_product(input, W, bias=None, name=None):
    if bias is not None:
        ip = tf.matmul(input, W)
        ip = tf.nn.bias_add(ip, bias, name=name)
    else:
        ip = tf.matmul(input, W, name=name)

    return ip


def l2_loss(var):
    return tf.nn.l2_loss(var)


def l1_loss(var):
    return tf.reduce_sum(tf.abs(var))


def zero_fraction(data, name=None):
    return tf.nn.zero_fraction(data, name=name)


def mse_loss(data, labels, size_average=None, name=None):
    """
    size_average is of no use, to be compatible with PyTorch backend.
    """
    if size_average == False:
        reduction_type = tf.losses.Reduction.NONE
    else:
        reduction_type = tf.losses.Reduction.MEAN

    return tf.losses.mean_squared_error(labels, data, scope=name, reduction=reduction_type)


def cross_entropy_loss(logits, labels, name=None):
    label_shape_size = len(labels.get_shape().as_list())
    class_num = cg.get_shape(logits)[1]
    if label_shape_size is 1:
        # Set up loss graph.
        # Convert from sparse integer labels in the range [0, NUM_CLASSSES)
        # to 1-hot dense float vectors (that is we will have batch_size
        # vectors, each with NUM_CLASSES values, all of which are 0.0
        # except there will be a 1.0 in the entry corresponding to the
        # label).
        batch_size = tf.size(labels)
        _labels = tf.expand_dims(labels, 1)
        indices = tf.expand_dims(tf.range(0, batch_size, 1), 1)
        concated = tf.concat(axis=1, values=[indices, _labels])
        onehot_labels = tf.sparse_to_dense(
            concated, tf.stack([batch_size, class_num]), 1.0, 0.0)
    else:
        # The labels has already been expanded, no need to do it again.
        onehot_labels = labels

    cross_entropy \
        = tf.nn.softmax_cross_entropy_with_logits(logits=logits,
                                                    labels=onehot_labels,
                                                    name='xentropy')
    cross_entropy_mean = tf.reduce_mean(cross_entropy,
                                        name=name)

    return cross_entropy_mean


def class_acccuracy(predictions, labels, name=None):
    label_shape_size = len(cg.get_shape(labels))
    if label_shape_size is 1:
        # NOTE: this approach has a bug. If the classifier is so weak, it
        # gives all equal probability for all classes, then the final
        # accuracy would be 1, since obviously the desired class is in the
        # top k.
        correct = tf.nn.in_top_k(predictions, labels, 1)
        # Return the number of true entries.
    else:
        truth = tf.argmax(labels, axis=1)
        predictions = tf.argmax(predictions, axis=1)
        correct = tf.equal(truth, predictions)

    return tf.reduce_mean(tf.cast(correct, tf.float32),
                          name=name)


def dropout(v, keep_prob, val=False, in_place=False, name=None):
    if in_place:
        raise ValueError("In place is not supported in tensorflow backend.")

    if val:
        return tf.identity(v, name=name)
    else:
        return tf.nn.dropout(input, keep_prob, seed=SEED, name=name)


def expand_kernel(ksize):
    if type(ksize) == int:
        ksize = [1, ksize, ksize, 1]
    elif len(ksize) == 2:
        ksize = [1, ksize[0], ksize[1], 1]
    else:
        ksize = ksize

    return ksize
