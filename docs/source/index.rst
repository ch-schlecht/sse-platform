.. sse-platform documentation master file, created by
   sphinx-quickstart on Sat Nov 30 10:00:44 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

API Documentation
*****************

Frontend
========

.. http:get:: /

    The main Page

    :resheader Content-Type: text/html

    :statuscode 200: no error

Modules
=======

.. http:get:: /modules/list_available

    List all modules that are available in the remote module repository

    **Example request**:

    .. sourcecode:: http

        GET /modules/list_available HTTP/1.1
        Host: example.com
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "type": "list_available_modules",
            "modules": ["module1", "module2"]
        }

    :resheader Content-Type: application/json

    :statuscode 200: no error

.. http:get:: /modules/list_installed

    List all modules that are currently installed

      **Example request**:

    .. sourcecode:: http

        GET /modules/list_installed HTTP/1.1
        Host: example.com
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "type": "list_installed_modules",
            "modules": ["module1", "module2"]
        }

    :resheader Content-Type: application/json

    :statuscode 200: no error

.. http:get:: /modules/download

    Download a module

    **Example request**:

    .. sourcecode:: http

        GET /modules/download?module_name="module1" HTTP/1.1
        Host: example.com
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "type": "installation_response",
            "module": "module1",
            "success": true
        }

    :query module_name: name of the module to download

    :resheader Content-Type: application/json

    :statuscode 200: no error

.. http:get:: /modules/uninstall

    Uninstall a module, If currently running, stop it

    **Example request**:

    .. sourcecode:: http

        GET /modules/uninstall?module_name="module1" HTTP/1.1
        Host: example.com
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "type": "uninstallation_response",
            "module": "module1",
            "success": true
        }

    :query module_name: name of the module to uninstall

    :resheader Content-Type: application/json

    :statuscode 200: no error

Configs
=======

.. http:get:: /configs/view

    Get the config of a module (in JSON)

    **Example request**:

    .. sourcecode:: http

        GET /configs/view?module_name="module1" HTTP/1.1
        Host: example.com
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "type": "view_config",
            "module": "module1",
            "config": <config>
        }


    :query module_name: name of the module to view the config of

    :resheader Content-Type: application/json

    :statuscode 200: no error

.. http:post:: /configs/update

    Change the config of a module

    **Example request**:

    .. sourcecode:: http

        POST /configs/update?module_name="module1" HTTP/1.1
        Host: example.com
        Content-Type: application/json
        Accept: application/json

        {
            "key1": "value1",
            "key2": "value2",
        }

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK

    :query module_name: name of the module to view the config of

    :resheader Content-Type: application/json

    :statuscode 200: no error

Module Execution
================

.. http:get:: /execution/start

    start a module

    **Example request**:

    .. sourcecode:: http

        GET /execution/start?module_name="module1" HTTP/1.1
        Host: example.com
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "type": "starting_response",
            "module": "module1",
            "success": true,
            "port": 123456
            "reason": <string> # omitted if success is true, else a reason for failure
        }

    :query module_name: name of the module to start

    :resheader Content-Type: application/json

    :statuscode 200: no error

.. http:get:: /execution/stop

    stop a module

    **Example request**:

    .. sourcecode:: http

        GET /execution/stop?module_name="module1" HTTP/1.1
        Host: example.com
        Accept: application/json

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK

    :query module_name: name of the module to stop

    :resheader Content-Type: application/json

    :statuscode 200: no error


Code Documentation
******************

github_access.py
================
.. automodule:: github_access
    :members:

util.py
=======
.. automodule:: util
    :members:

main.py
=======
.. automodule:: main
    :members:




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
