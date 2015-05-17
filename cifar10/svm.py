__author__ = 'artanis'

import os
import sys
import leveldb
import commands
import numpy as np
from sklearn.linear_model import LogisticRegression

caffe_root = os.path.join(__file__, "..", "..", "caffe", "python")
sys.path.append(os.path.abspath(caffe_root))
import caffe
from caffe.io import datum_to_array, blobproto_to_array, caffe_pb2

data_dir = "data"
train_db = os.path.join(data_dir, "cifar10_train_leveldb")
test_db = os.path.join(data_dir, "cifar10_test_leveldb")

conf_dir = "conf"
proto_file = os.path.join(conf_dir, "cifar10_quick_deploy.prototxt")
model_file = os.path.join(conf_dir, "cifar10_quick_iter_5000.caffemodel")
mean_file = os.path.join(conf_dir, "mean.binaryproto")

model = caffe.Classifier(proto_file, model_file)

if commands.getstatusoutput("nvidia-smi")[0] == 0:
    caffe.set_mode_gpu()
    print >> sys.stderr, "Use GPU for training / testing."
else:
    caffe.set_mode_cpu()
    print >> sys.stderr, "Cannot find GPU, use CPU instead."

blob = caffe_pb2.BlobProto()
blob.ParseFromString(open(mean_file).read())
mean = blobproto_to_array(blob)[0]

tform = caffe.io.Transformer({"data": model.blobs["data"].data.shape})
tform.set_mean("data", mean)
tform.set_transpose("data", (2, 0, 1))


def convert_db_to_arr(db_path):
    db = leveldb.LevelDB(db_path)
    data, labels = [], []

    for item in db.RangeIter():
        datum = caffe_pb2.Datum()
        datum.ParseFromString(item[1])
        data.append(datum_to_array(datum))
        labels.append(datum.label)

    data, labels = np.asarray(data), np.asarray(labels)
    return np.rollaxis(data, 1, 4), labels


def extract_feature(imgs):
    with open(proto_file) as f:
        lines = f.readlines()
        batch = int(lines[2].split(':')[-1])

    n_img = imgs.shape[0]
    x = np.zeros((n_img, 64), dtype=np.float32)

    for i in xrange(0, n_img, batch):
        j = min(i + batch, n_img)

        data = np.asarray([tform.preprocess("data", img)
                           for img in imgs[i: j]])
        if j - i < batch:
            append = np.zeros((batch - j + i,) + data.shape[1],
                              dtype=data.dtype)
            data = np.vstack((data, append))

        model.forward(data=data)
        x[i: j] = model.blobs["ip1"].data[:j - i]

        sys.stdout.write("Processing Image: %d/%d\r" % (j, n_img))
        sys.stdout.flush()
    print

    return x

if __name__ == "__main__":
    train_x, train_y = convert_db_to_arr(train_db)
    test_x, test_y = convert_db_to_arr(test_db)

    print "Generating Training Samples..."
    train_x = extract_feature(train_x)

    print "Generating Testing Samples..."
    test_x = extract_feature(test_x)

    svc = LogisticRegression()
    svc.fit(train_x, train_y)
    print "Test Accuracy: %f" % np.mean(svc.predict(test_x) == test_y)
