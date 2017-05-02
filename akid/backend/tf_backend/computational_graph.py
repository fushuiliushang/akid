"""
Tensorflow backend for akid.

 Usage
================================================================================
To use tensorflow backend to execute/evaluate any graph built, run `init`
beforehand.
"""


import tensorflow as tf


# Build a global session to use
# TODO: think how to offer a way to close the session.
# A bug in tensorflow: Exception AttributeError: "'NoneType' object has no attribute 'TF_DeleteStatus'" in <bound method Session.__del__ of <tensorflow.python.client.session.Session object at 0x7f43105e9dd0>> ignored
# Should be fixed by now: https://github.com/tensorflow/tensorflow/issues/3388
sess = None

float32 = tf.float32


def init():
    global sess
    sess = tf.Session()
    init  = tf.group(tf.global_variables_initializer(),
              tf.local_variables_initializer())
    sess.run(init)


def close():
    sess.close()
    tf.reset_default_graph()


def get_variable(name, shape=None,
                 initializer=None, trainable=True,
                 shared=True):
    if not callable(initializer):
        shape = None

    if shared:
        return tf.get_variable(name, shape,
                               initializer=initializer, trainable=trainable)
    else:
        raise NotImplementedError("Normal Variable creation has not been implemented yet.")


def Tensor(X_in):
    """
    Get a tensor from a constant (array).
    """
    return tf.constant(X_in)


def eval(V):
    """
    Convert variable to numpy array.
    """
    return sess.run(V)


def split(split_dim, num_split, value, name="split"):
    return tf.split(split_dim, num_split, value, name="split")


def reshape(tensor, shape, name=None):
    return tf.reshape(tensor, shape, name)


def reduce_sum(input_tensor, axis=None, keep_dims=False, name=None, reduction_indices=None):
    tf.reduce_sum(input_tensor, axis, keep_dims, name, reduction_indices)


def cast(x, dtype, name=None):
    return tf.cast(x, dtype, name)


def concat(concat_dim, values, name="concat"):
    return tf.concat(concat_dim, values, name=name)


def stack(values, axis=0, name="pack"):
    return tf.stack(values, axis=axis, name=name)


def unstack(values, axis=0, name="unstack"):
    return tf.unstack(values, num=None, axis=axis, name=name)


def pack(values, axis=0, name="pack"):
    return tf.stack(values, axis=axis, name=name)


def expand_dims(input, axis=None, name=None):
    return tf.expand_dims(input, axis=axis, name=name)


def reduce_max(input_tensor, axis=None, keep_dims=False, name=None):
    return tf.reduce_max(input_tensor, axis=axis, keep_dims=keep_dims, name=name, reduction_indices=None)


def is_tensor(T):
    return type(T) is tf.Tensor
