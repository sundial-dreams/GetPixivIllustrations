import pathlib
from typing import List

import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np

dataset_url = "file:///Users/dengpengfei/Documents/Project/Python/GetPixivImage/datasets/test.tgz"

data_dir = keras.utils.get_file('test', origin=dataset_url, untar=True)
data_dir = pathlib.Path(data_dir)
EPSILON = 1.001e-5
EPOCHS = 15

image_count = len(list(data_dir.glob("*/*.jpg")))
img_height, img_width = (256, 256)
batch_size = 10

train_ds = keras.preprocessing.image_dataset_from_directory(
    data_dir,
    validation_split=0.5,
    subset='training',
    seed=123,
    image_size=(img_height, img_width),
    batch_size=batch_size
)

print(train_ds)

val_ds = keras.preprocessing.image_dataset_from_directory(
    data_dir,
    validation_split=0.5,
    subset='validation',
    seed=123,
    image_size=(img_height, img_width),
    batch_size=batch_size
)

class_names = train_ds.class_names

train_ds = train_ds.cache().shuffle(10).prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
val_ds = val_ds.cache().shuffle(2).prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
num_class = 2

data_augmentation = keras.Sequential([
    layers.experimental.preprocessing.RandomFlip('horizontal', input_shape=(img_height, img_width, 3)),
    layers.experimental.preprocessing.RandomRotation(0.1),
    layers.experimental.preprocessing.RandomZoom(0.1)
])


# plt.figure(figsize=(10, 10))
# for images, _ in train_ds.take(3):
#     for i in range(9):
#         augmented_images = data_augmentation(images)
#         ax = plt.subplot(3, 3, i + 1),
#         plt.imshow(augmented_images[0].numpy().astype('uint8'))
#         plt.axis('off')
# plt.show()

# 实现DenseNet 根据blocks不同而产生不同的DenseNet（DenseNet161、DenseNet121）
def DenseNet(blocks: List, shape: tuple) -> keras.Model:
    img_input = layers.Input(shape=shape)
    x = data_augmentation(img_input)
    x = layers.experimental.preprocessing.Rescaling(1. / 22, input_shape=(img_height, img_width, 3))(x)
    x = layers.ZeroPadding2D(padding=((3, 3), (3, 3)))(x)  # padding-top, bottom, left, right
    x = layers.Conv2D(64, 7, strides=2, use_bias=False)(x)
    x = layers.BatchNormalization(axis=3, epsilon=EPSILON)(x)
    x = layers.Activation('relu')(x)
    x = layers.ZeroPadding2D(padding=((1, 1), (1, 1)))(x)
    x = layers.MaxPooling2D(3, strides=2)(x)

    x = dense_block(x, blocks[0])
    x = transition_block(x, 0.5)
    x = dense_block(x, blocks[1])
    x = transition_block(x, 0.5)
    x = dense_block(x, blocks[2])
    x = transition_block(x, 0.5)
    x = dense_block(x, blocks[3])

    x = layers.BatchNormalization(axis=3, epsilon=EPSILON)(x)
    x = layers.Activation('relu')(x)

    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(2, activation='softmax')(x)

    return keras.Model(img_input, x)


def conv_block(x: tf.Tensor, growth_rate) -> tf.Tensor:
    x1 = layers.BatchNormalization(axis=3, epsilon=EPSILON)(x)
    x1 = layers.Activation('relu')(x1)
    x1 = layers.Conv2D(4 * growth_rate, 1, use_bias=False)(x1)
    x1 = layers.BatchNormalization(axis=3, epsilon=EPSILON)(x1)
    x1 = layers.Activation('relu')(x1)
    x1 = layers.Conv2D(growth_rate, 3, padding="same", use_bias=False)(x1)
    x = layers.Concatenate(axis=3)([x, x1])
    return x


def dense_block(x: tf.Tensor, blocks_len: int) -> tf.Tensor:
    for i in range(blocks_len):
        x = conv_block(x, 32)
    return x


def transition_block(x: tf.Tensor, reduction: float):
    x = layers.BatchNormalization(axis=3, epsilon=EPSILON)(x)
    x = layers.Activation('relu')(x)
    x = layers.Conv2D(int(keras.backend.int_shape(x)[3] * reduction), 1, use_bias=False)(x)
    x = layers.AveragePooling2D(2, strides=2)(x)
    return x


def DenseNet169(shape: tuple) -> keras.Model:
    return DenseNet([6, 12, 32, 32], shape)


def DenseNet121(shape: tuple) -> keras.Model:
    return DenseNet([6, 12, 24, 16], shape)


def train_model(model: keras.Model) -> None:
    # 模型编译
    model.compile(
        optimizer=keras.optimizers.Adam(),
        loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=['accuracy']
    )

    # 训练模型
    history = model.fit(train_ds, epochs=EPOCHS, validation_data=val_ds)

    # 绘制准确度与误差曲线
    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    loss = history.history['loss']
    val_loss = history.history['val_loss']

    plt.figure(figsize=(8, 8))
    plt.subplot(1, 2, 1)
    plt.plot(range(EPOCHS), acc, label="training accuracy")
    plt.plot(range(EPOCHS), val_acc, label="validation accuracy")
    plt.legend()
    plt.title("training and validation accuracy")

    plt.subplot(1, 2, 2)
    plt.plot(range(EPOCHS), loss, label="training loss")
    plt.plot(range(EPOCHS), val_loss, label="validation loss")
    plt.legend()
    plt.title("training and validation loss")
    plt.show()

    print(
        "training accuracy: {}, training loss: {}, validation accuracy: {}, validation loss: {}"
            .format(acc[-1], loss[-1], val_acc[-1], val_loss[-1])
    )


def evaluate_model(model: keras.Model) -> None:
    # 评估模型
    test_loss, test_acc = model.evaluate(train_ds, verbose=2)

    print("test loss: {}, test accuracy: {}".format(test_loss, test_acc))


def predict(model: keras.Model) -> None:
    url = "file:///Users/dengpengfei/Documents/Project/Python/tensorflow/datasets/anime/kaiten/AFB3A9FF-B184-4D61-9BEE-8603B1863EE3_1_105_c.jpeg"
    path = keras.utils.get_file("kaiten", origin=url)
    img = keras.preprocessing.image.load_img(
        path, target_size=(img_height, img_width)
    )

    img_arr = keras.preprocessing.image.img_to_array(img)
    img_arr = tf.expand_dims(img_arr, 0)
    p = model.predict(img_arr)
    score = tf.nn.softmax(p[0])
    print(class_names[np.argmax(score)], 100 * np.argmax(score))


if __name__ == "__main__":
    model_121 = DenseNet121(shape=(img_width, img_height, 3))
    train_model(model_121)
    evaluate_model(model_121)
