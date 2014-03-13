from sklearn import datasets
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import matplotlib.pyplot as plt
import os

from simpyl import Simpyl
import simpyl.database as db

sl = Simpyl()

SEED = 12345


def load_data():
    # load the iris dataset
    iris = datasets.load_iris()
    X = iris['data']
    y = iris['target']
    return X, y


def train_classifier(X_train, y_train, n_estimators=10, min_samples_split=2):
    clf = RandomForestClassifier(n_estimators=n_estimators,
                                 min_samples_split=min_samples_split,
                                 random_state=SEED)
    clf.fit(X_train, y_train)
    return clf


def test_classifier(clf, X, y_true):
    y_pred = clf.predict(X)
    return np.sum(y_pred == y_true) / float(y_pred.size)


@sl.add_procedure('trainer')
def main_trainer(n_estimators, min_samples_split):
    X, y = load_data()
    clf = train_classifier(X, y, n_estimators, min_samples_split)

    # testing on the training set is bad practice, but serves as a demonstration
    score = test_classifier(clf, X, y)
    sl.log("Overall accuracy: {}%".format(100.0 * score))
    sl.write_cache(clf, "classifier.rf")
    return score

@sl.add_procedure('plots')
def feature_importance():
    clf = sl.read_cache("classifier.rf")
    # plot the classification probabilities for the first example
    n_features = clf.feature_importances_.shape[0]
    plt.bar(np.arange(n_features), clf.feature_importances_)
    # 0.4 is half the default width
    plt.xticks(np.arange(n_features)+0.4, ["Feature {}".format(i+1) for i in xrange(n_features)])
    sl.savefig("Feature Importances")
    return(clf)


if __name__ == '__main__':
    # use the test database
    db.reset_database(os.path.join('simpyl', 'tests', 'test.db'))
    sl.start()