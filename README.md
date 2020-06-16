# sse-platform
[![Build Status](https://travis-ci.com/Smunfr/sse-platform.svg?branch=master)](https://travis-ci.com/Smunfr/sse-platform)
[![Documentation Status](https://readthedocs.org/projects/sse-platform/badge/?version=latest)](https://sse-platform.readthedocs.io/en/latest/?badge=latest)

Platform to handle various modules of SoServ research project


## Installation

In order to be able to run this software, some modules are required to be installed, which are specified in requirements.txt. Install the dependencies by executing:

```sh
$ pip install -r requirements.txt
```

Furthermore you will need PostgreSQL to store users. Please refer to any of their installation guides for you OS.
Once PostgreSQL is installed, you will need to create a user and database. Open a Postgres Shell as postgres user:
```sh
$ sudo -u postgres psql
```
Next, create the following user and database:
```sh
$ CREATE DATABASE sse;
CREATE USER admin WITH PASSWORD 'admin_password_goes_here';
GRANT ALL ON DATABASE sse TO admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO admin;
```
The tables will be created automatically on server startup. However, if you wish to generate them manually, execute the following command:
```sh
$ sudo -u postgres psql -U postgres -d sse < create_tables.sql
```


## Running the platform

To run this API, you will need an SSL Certificate and the corrensponding SSL key. Those artifacts need to be supplied via config (in JSON format). An example config is present in the repo.

If you do not already have SSL credentials, you can generate a self-signed certificate by executing:

```sh
$ openssl req -x509 -newkey rsa:4096 -keyout key.key -out cert.crt -days 365
```

The config also needs to specify the connection details for your database. Please see the example config for the neccessary keys.

To run the platform, execute the following command:

```sh
$ python3 main.py -c path/to/config.json [--dev] [--create_admin]
```

Mandatory arguments:
- -c : the path to the json config file

Optional arguments:
- --dev : developer mode, no authentication is required to access the api endpoints
- --create_admin : automatically create an admin account on the platform. Credentials will be read from the config. See the example config for the required keys


## Documentation

The documentation is built with [Sphinx](http://www.sphinx-doc.org/en/master/) and can be found [here](https://sse-platform.readthedocs.io).

#### Building the Docs yourself

If you require to build the docs yourself, you need to install Sphinx. Please refer to their [Installation guide](http://www.sphinx-doc.org/en/master/usage/installation.html) for instructions.
Secondly, you need to install the HTTP templates for Sphinx as well as JSDoc to ensure building the documentation of the frontend:

```sh
$ pip install sphinxcontrib-httpdomain
$ npm install -g jsdoc
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


## Contributing a module

In order to build a module there are certain rules and steps to do to ensure your module is working properly. (As this platform is in alpha state, please not that this information is subject to change):

1. Your only way of communication with the platform is via a websocket connection.
  Our modules all use the same client class. Feel free to also use this websocket client in your module. you can find it in socket_client.py

Once your module is ready for use, commit and create a pull request to [this](https://github.com/Smunfr/sse-platform-modules) repository. Please consider only pushing production-ready code to this repository, do not use it for development.
