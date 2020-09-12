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
    return round(np.sum(y_pred == y_true) / float(y_pred.size), 3)

@sl.add_procedure('trainer')
def main_trainer(n_estimators, min_samples_split):
    X, y = load_data()
    trained_classifier = train_classifier(X, y, n_estimators, min_samples_split)
    # testing on the training set is bad practice, but serves as a demonstration
    score = test_classifier(trained_classifier, X, y)
    sl.log("Overall accuracy: {}%".format(100.0 * score))
    sl.write_cache(trained_classifier, "classifier.rf")
    return score


@sl.add_procedure('plots')
def feature_importance():
    trained_classifier = sl.read_cache("classifier.rf")
    # plot the classification probabilities for the first example
    n_features = trained_classifier.feature_importances_.shape[0]
    plt.bar(np.arange(n_features), trained_classifier.feature_importances_)
    # 0.4 is half the default width
    plt.xticks(
        np.arange(n_features)+0.4,
        ["Feature {}".format(i+1) for i in range(n_features)]
    )
    sl.savefig("Feature Importances")
    return(trained_classifier)


if __name__ == '__main__':
    # run the reset to setup the database the first time
    db.reset_database(os.path.join('simpyl', 'tests', 'test_ml.db'))

    # use the test database
    db.use_database(os.path.join('simpyl', 'tests', 'test_ml.db'))

    # a run can be initated from the webserver or in code
    sl.run(
        [('trainer', {'n_estimators': 3, 'min_samples_split': 10}),
         ('plots', {})],
        description="Run from code"
    )
    sl.run(
        [('trainer', {'n_estimators': 10, 'min_samples_split': 10}),
         ('plots', {})],
        description="Run from code with more estimators"
    )

    # start the webserver
    sl.start()
