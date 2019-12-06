# sse-platform

Platform to handle various modules of SoServ research project


## Installation

In order to be able to run this software, some modules are required to be installed:

- Tornado:
```sh
$ pip install tornado
```

- PyGithub:
```sh
$ pip install pygithub
```

## Running the platform

To run this API, simply execute the following command:

```sh
$ python3 main.py
```

## Documentation

The documentation is built with [Sphinx](http://www.sphinx-doc.org/en/master/) and can be found inside the docs/build/html directory.

#### Building the Docs yourself

If you require to build the docs yourself, you need the install Sphinx. Please refer to their [Installation guide](http://www.sphinx-doc.org/en/master/usage/installation.html) for instructions.
Secondly, you need to install the HTTP templates for Sphinx:

```sh
$ pip install sphinxcontrib-httpdomain
```

To now build the docs, navigate into the docs/ directory and execute:

```sh
$ make html
```

The freshly built docs will be in docs/build/html.


## Tests

Tests are implemented with [Pytest](http://doc.pytest.org/en/latest/index.html). Please refer to their [guide](http://doc.pytest.org/en/latest/getting-started.html) for installation.

Once you installed Pytest, you also need to install the tornado plugin:
```sh
$ pip install pytest-tornado
```

to run the tests, simply execute:
```sh
$ pytest
```
