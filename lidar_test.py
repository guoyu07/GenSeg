import atexit
import numpy as np
import sys
import matplotlib.pyplot as plt
import os.path


from model import GenSeg
from util import DataReader, original_to_label
from scipy.io import savemat
from mpl_toolkits.mplot3d import Axes3D
from sklearn.cluster import DBSCAN

num_classes = 6
input_shape = [None, 96, 96, 96, 1]
datareader_params = ('data/', (352, 1216, 3), np.array([0, -32, -16]), np.array([64, 32, 16]), np.array([96, 96, 96]), 11)


def main():
    name = 'saved/lidar.ckpt'
    number = int(sys.argv[1])
    if number is 2: test2(name)
    elif number is 3: test3(name)
    elif number is 4: test4()
    elif number is 5: test5(name)
    elif number is 6: test6(name)
    else: test1(name)


def test6(name):
    dr = DataReader(*datareader_params)
    x = dr.get_velodyne_data()
    y = dr.get_velodyne_labels()
    func = np.vectorize(original_to_label)
    y = func(y)
    n, _, _, _, _ = x.shape
    batch_size = 1

    model = GenSeg(input_shape=input_shape, num_classes=num_classes, load_model=name)

    average = 0
    count = 0
    for i in range(0, n, batch_size):
        batch_data = x[i:i + batch_size, ...]
        batch_labels = y[i:i + batch_size, ...]
        results = model.apply(batch_data)
        results = np.argmax(results, axis=-1)
        results = np.equal(results, batch_labels)
        results = np.average(results.astype(dtype=np.float32))
        average += results
        count += 1
        print(i)
    print(average / count)


def test5(name):
    image_segmenter = GenSeg(input_shape=[None, 176, 608, 3], num_classes=num_classes, load_model='saved/Long7-Lab-Fixed.ckpt')
    velo_segmenter = GenSeg(input_shape=[None, 96, 96, 96, 1], num_classes=num_classes, load_model='saved/lidar.ckpt')
    dr = DataReader(*datareader_params)

    images = dr.get_image_data()[:1, :, :, :]
    image_preds = image_segmenter.apply(images)
    image_pred = image_preds[0, :, :, :]
    image_candidates = []
    for i in range(3, 6):
        class_hits = np.argmax(image_pred, axis=-1) == i
        class_hits = np.argwhere(class_hits)
        if len(class_hits) > 0:
            confidences = image_pred[class_hits[:, 0], class_hits[:, 1], :]
            dbscan = DBSCAN(eps=50, min_samples=1)
            dbscan.fit(class_hits)
            labels = dbscan.labels_
            for j in range(np.max(labels) + 1):
                idxs = labels == j
                idxs = np.argwhere(idxs)
                avg_conf = confidences[idxs, :]
                avg_conf = np.mean(avg_conf, 0)
                com = np.mean(class_hits[idxs, :], 0)
                image_candidates.append((i, avg_conf, com))

    velos = dr.get_velodyne_data()[:1, :, :, :, :]
    velo_preds = velo_segmenter.apply(velos)
    velo_pred = velo_preds[0, :, :, :, :]
    velo_candidates = []
    for i in range(3, 6):
        class_hits = np.argmax(velo_pred, axis=-1) == i
        class_hits = np.argwhere(class_hits)
        if len(class_hits) > 0:
            confidences = velo_pred[class_hits[:, 0], class_hits[:, 1], class_hits[:, 2], :]
            dbscan = DBSCAN(eps=50, min_samples=1)
            dbscan.fit(class_hits)
            labels = dbscan.labels_
            for j in range(np.max(labels) + 1):
                idxs = labels == j
                idxs = np.argwhere(idxs)
                avg_conf = confidences[idxs, :]
                avg_conf = np.mean(avg_conf, 0)
                com = np.mean(class_hits[idxs, :], 0)
                velo_candidates.append((i, avg_conf, com))

    print('IMAGE CANDIDATES')
    for (class_number, avg_conf, com) in image_candidates:
        print('Class number:', class_number)
        print('Average confidence:')
        for conf in avg_conf: print(conf)
        print('Center of mass:')
        for coord in com: print(coord)
        print('')

    print('VELODYNE CANDIDATES')
    for (class_number, avg_conf, com) in velo_candidates:
        print('Class number:', class_number)
        print('Average confidence:')
        for conf in avg_conf: print(conf)
        print('Center of mass:')
        for coord in com: print(coord)
        print('')

def test4():
    dr = DataReader(*datareader_params)
    image_segmenter = GenSeg(input_shape=[None, 176, 608, 3], num_classes=num_classes, load_model='saved/Long7-Lab-Fixed.ckpt')
    velo_segmenter = GenSeg(input_shape=[None, 96, 96, 96, 1], num_classes=num_classes, load_model='saved/lidar.ckpt')

    x_image = dr.get_image_data()
    y_image_true = dr.get_image_labels()
    n, _, _, = y_image_true.shape
    image_hits = np.empty((3, 1))
    image_totals = np.empty((3, 1))
    for i in range(n):
        print(i,'image')
        image_pred = np.argmax(image_segmenter.apply(x_image[i:i+1, :, :, :]), axis=-1)
        image_true = y_image_true[i:i+1, :, :]
        for j in range(3, 6):
            hit_pred = image_pred == j
            hit_true = image_true == j
            image_hits += np.sum(hit_true)
            image_totals += np.sum(np.logical_and(hit_pred, hit_true))

    x_velo = dr.get_velodyne_data()
    y_velo_true = dr.get_velodyne_labels()
    n, _, _, _ = y_velo_true.shape
    velo_hits = np.empty((3, 1))
    velo_totals = np.empty((3, 1))
    for i in range(n):
        print(i,'velo')
        velo_pred = np.argmax(velo_segmenter.apply(x_velo[i:i+1, :, :, :, :]), axis=-1)
        velo_true = y_velo_true[i:i+1, :, :, :]
        for j in range(3, 6):
            hit_pred = velo_pred == j
            hit_true = velo_true == j
            velo_hits += np.sum(hit_true)
            velo_totals += np.sum(np.logical_and(hit_pred, hit_true))

    for total in image_totals: print(total)
    for hit in image_hits: print(hit)
    for total in velo_totals: print(total)
    for hit in velo_hits: print(hit)


def test3(name):
    dr = DataReader(*datareader_params)
    x = dr.get_velodyne_data()
    model = GenSeg(input_shape=input_shape, num_classes=num_classes, load_model=name)
    datapoint = model.apply(x[:1, :, :, :, :])
    datapoint = np.argwhere(datapoint==3)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(datapoint[:, 0], datapoint[:, 1], datapoint[:, 2])
    plt.show()


def test2(name):
    dr = DataReader(*datareader_params)
    x = dr.get_velodyne_data()
    y = dr.get_velodyne_labels()
    func = np.vectorize(original_to_label)
    y = func(y)
    datapoint = y[0, :, :, :]
    datapoint = np.argwhere(datapoint==1)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    #ax.set_autoscale_on(False)
    #ax.autoscale(False)
    #plt.axis('equal')
    ax.scatter(datapoint[:, 0], datapoint[:, 1], datapoint[:, 2])
    plt.show()


def test1(name):
    dr = DataReader(*datareader_params)
    x = dr.get_velodyne_data()
    y = dr.get_velodyne_labels()
    func = np.vectorize(original_to_label)
    y = func(y)
    n, _, _, _, _ = x.shape
    batch_size = 1
    iterations = sys.maxsize

    model = GenSeg(input_shape=input_shape, num_classes=num_classes, load_model=name)
    atexit.register(model.save_model, name)  # In case of ctrl-C
    for iteration in range(iterations):
        idxs = np.random.permutation(n)[:batch_size]
        batch_data = x[idxs, :, :, :, :]
        batch_labels = y[idxs, :, :, :]
        print(iteration, model.train(
            x_train=batch_data, y_train=batch_labels,
            num_epochs=1, start_stop_info=False, progress_info=False
        ))

        if iteration % 500 == 0:
            print("Saving checkpoint")
            model.save_model(name)
            

if __name__ == "__main__":
    main()
