# sse-platform

Platform to handle various modules of SoServ research project


## Installation

In order to be able to run this software, some modules are required to be installed, which are specified in requirements.txt. Install the dependencies by executing:

```sh
$ pip install -r requirements.txt
```

Furthermore, you will need an instance of Keycloak Authentication Service, where have access to the administration console.
Please Consult the [Guides](https://www.keycloak.org/guides) for installation procedures.

There are some crucial configurations of the Keycloak Server needed to work with this platform, which are loosly described in ```keycloak_config.md``` (at this point only in German).

## Running the platform

You will need a config.json file to store your parameters. You may consult the example_config.json for details on the keys.

To run the platform, execute the following command:

```sh
$ python3 main.py [--config path/to/config.json]
```
Optional arguments:
- --config to specify the path to the config file. It defaults to ./config.json

## Tests

Tests are done using Tornados testing submodule which relies on the standard unittest module itself.
Therefore no extra dependencies need to be installed.

Run the tests using the following command:

```sh
$ python3 -m tornado.testing api_test.py
```

There are plenty more available arguments in the [docs](https://www.tornadoweb.org/en/stable/testing.html#tornado.testing.main).


## Contributing a module

In order to build a module there are certain rules and steps to take to ensure your module is working properly. (As this platform is in alpha state, please note that this information is subject to change):

1. Your only way of communication with the platform is via a websocket connection.
  Our modules all use the same client class. Feel free to also use this websocket client in your module. you can find it in ```client_examples/socket_client.py```. Please note: You have to change the names of your module in the placeholders (lines 30, 98, 132, 141). Keep in mind to use the exact same name everywhere (also when communicating with the platform (later steps)).

2. To establish a connection and to communicate with the platform your messages have to be digitally signed. There is a script (```client_examples/signing.py```) that provides the generation of a sign and verify key. Execute this script, and you will receive two files: ```signing_key.key``` and ```verify_key.key``` . Keep those in your module's directory. Keep the signing key secret at all cost. Copy the verify key from the file into the ```verify_keys.json``` at the platform. Remember to use the same name as in step 1.
3. If you need Authentication, you will need to access the Keycloak API. If your backend uses the Tornado framework in Python, your best bet is to copy our ```BaseHandler``` along with the ```auth_needed```-decorator, subclass your handlers from it and decorate your handler functions. It will request Keycloak to validate the session, and if no such valid session exists, redirects you to Keycloak to perform the login.
4. You should be good to go. To initiate a WebSocket connection with the platform and make the platform recognize your module, use the following code snippet:

    ```python3
    client = await get_socket_instance()
    response = await client.write({"type": "module_start",
                                  "module_name": "<your_module_name_here>",
                                  "port": 12345})
    # if response["status"] == "recognized":
          # you now have an established connection with the platform
    ```
    Again, use the same name as in steps 1 and 2.

    Optimally, do this recognization step on your module's initialization.

    Any form of communication is done via this same code snippet, but by changing the supplied message dictionary.
