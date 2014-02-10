from sklearn import datasets
from sklearn.ensemble import RandomForestClassifier
import numpy as np

import simpyl

sl = simpyl.Simpyl()


@sl._add_procedure('load', caches=['X.csv', 'y.csv'])
def load_data():
    # load the iris dataset
    iris = datasets.load_iris()
    X = iris['data']
    y = iris['target']
    return X, y


@sl._add_procedure('train', caches=['classifier.rf'])
def train_classifier(X_train, y_train, n_estimators=10, min_samples_split=2):
    clf = RandomForestClassifier(n_estimators=n_estimators,
                                 min_samples_split=min_samples_split)
    clf.fit(X_train, y_train)
    return clf


@sl._add_procedure('test')
def test_classifier(clf, X, y_true):
    y_pred = clf.predict(X)
    return np.sum(y_pred == y_true) / float(y_pred.size)


def manual_run():
    X, y = load_data()
    clf = train_classifier(X, y)
    # testing on the training set is bad practice, but serves as a demonstration
    score = test_classifier(clf, X, y)
    print("Overall accuracy: {}%".format(100.0*score))


if __name__ == '__main__':
    print("Manual run")
    manual_run()

    print("Data from simpyl")
    print(sl._procedures)
