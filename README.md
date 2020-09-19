# simpyl

Track and log computational simulations and machine learning runs with a
handful of Python decorators - via a web or code interface.

## A Simple Example

`examle.py` shows how Simpyl can be used with a basic Random Forest classifier
and the Iris dataset.

Import the library, create a Simply object, and point it to an SQLite database.
```python
from simpyl import Simpyl
import simpyl.database as db

sl = Simpyl()
db.use_database('example.db')
```

Register a function to be controlled by Simpyl. The function arguments are automatically
picked up.
```python
@sl.add_procedure('trainer')
def main_trainer(n_estimators, min_samples_split):
    X, y = load_data()
    trained_classifier = train_classifier(X, y, n_estimators, min_samples_split)
    ...
```

Inside this function we can log information, and cache the trained estimator.
```python
    ...
    sl.log("Overall accuracy: {}%".format(100.0 * score))
    sl.write_cache(trained_classifier, "classifier.rf")
    ...
```

Plots can also be saved. `sl.savefig()` will save any active Matplotlib plot.
```python
@sl.add_procedure('plots')
def feature_importance():
    trained_classifier = sl.read_cache("classifier.rf")
    ...
    # Plot a figure with matplotlib
    ...
    sl.savefig("Feature Importances")
```

Start the webserver with `sl.start()`. This gives us a web interface
to build runs with our registered functions.

![Add procedure](/docs/add_procedure.png)

![Add procedure](/docs/setup_run.png)

A page with arguments, results and saved plots is automatically created.

![Add procedure](/docs/run_details1.png)
![Add procedure](/docs/run_details2.png)

Runs can be built an initiated via normal Python code as well.
```python
sl.run(
    [
        ('trainer', {'n_estimators': 3, 'min_samples_split': 10}),
        ('plots', {})
    ],
    description="Run from code"
)
```

These will still be visible in the web interface.
![Add procedure](/docs/run_list.png)