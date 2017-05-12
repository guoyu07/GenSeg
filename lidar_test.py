import atexit
import numpy as np
import sys
import cv2

from model import GenSeg
from util import DataReader, original_to_label

num_classes = 6
datareader_params = ('data/', (352, 1216, 3), np.array([0, -32, -16]), np.array([64, 32, 16]), np.array([32, 32, 32]), num_classes)


def main():
    name = 'saved/lidar.ckpt'
    number = sys.argv[1]
    if number is 2: pass
    else: test1(name)


def test1(name):
    input_shape = [None, 32, 32, 32, 1]

    dr = DataReader(*datareader_params)
    x = dr.get_velodyne_data()
    y = dr.get_velodyne_labels()
    func = np.vectorize(original_to_label)
    y = func(y)
    n, _, _, _, _ = x.shape
    batch_size = 30
    iterations = sys.maxsize

    model = GenSeg(input_shape=input_shape, num_classes=num_classes)
    atexit.register(model.save_model, name)  # In case of ctrl-C
    for iteration in range(iterations):
        idxs = np.random.permutation(n)[:batch_size]
        batch_data = x[idxs, :, :, :, :]
        batch_labels = y[idxs, :, :, :]
        print('GON TRAIN RIGHT NAO')
        print(iteration, model.train(
            x_train=batch_data, y_train=batch_labels,
            num_epochs=1, start_stop_info=False, progress_info=False
        ))


if __name__ == "__main__":
    main()


