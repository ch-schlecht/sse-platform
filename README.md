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


## Contributing a module

In order to build a module there are certain rules and steps to do to ensure your module is working properly:

1. Every module is a tornado Application (i.e it implements tornado.web.Application)

2. You need to have a config.json somewhere inside your project. This is the only way of getting parameters from outside into your application. Create it even if you don't need any config. Just leave it empty then.

3. this application has to be built inside a main.py file (only this file will be explored by the platform at first glance)

4. your module's current working dir is not automatically added to the sys path.
    It is at the developers responsibility to ensure imports are working.

    Easiest way to achieve that is to prepend the following code to your main.py (before any other imports):
    ```python
    import os
    import sys
    sys.path.append(os.path.dirname(__file__))
    ```
    By doing that, your current working directory will be added to the sys path, which means that imports will work as per normal.

5. there are a couple of functions that need to be implemented inside your main.py file. The platform will call these functions and might throw an error if they are not present.

    ```python
    def make_app():
        # returns your tornado.web.Application

    def apply_config(config):
        # the platform will call this function before it is started.
        # You do not need to know the config path from within your module,
        # the platform will search for it, load the file into a Python Object and
        # pass it as a parameter to this function

        # Do whatever you need to do with your config.
        # This is your only way of getting parameters from outside (no argparser or
        # stuff like that available)

    def stop_signal():
        # this function is called by the platform when decided to stop your module
        # for whatever reason

        # Save anything you need to save and be sure to clean up all temporary files
        # created by this module.
        # BUT MOST IMPORTANTLY: close all your open connections (especially
        # WebSockets)
        # because they would keep on going even though the module is stopped which
        # may cause undefined behaviour
        # RequestHandlers do not need to be closed as there are no
        # keep-alive connections allowed
    ```
6. If you plan to also be able to use your module in a standalone way, be sure to protect setup code from being executed when imported by the platform; meaning: wrap it in a
    ```python
    if __name__ == '__main__':

    ```

Once your module is ready for use, commit and create a pull request to [this](https://github.com/Smunfr/sse-platform-modules) repository. Please consider only pushing production-ready code to this repository, do not use it for development.
