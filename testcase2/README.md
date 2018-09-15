BOPTEST Test Case 2
===================

1) To build: ``$ make build`` (takes a few minutes)

2) To deploy: ``$ make run`` (takes a few seconds)

3) To interact, send RESTful requests to: ``http://127.0.0.1:5000/<request>``

4) To shutdown: ``Ctrl+C`` to close port, ``Ctrl+D`` to exit docker container.

Example RESTful interaction:

- Advance simulation with new heating and cooling temperature setpoints: ``$ curl http://127.0.0.1:5000/advance -d '{"TSetRooHea":293.15,"TSetRooCoo":298.15}' -H "Content-Type: application/json"``
- Receive a list of measurements: ``$ curl http://127.0.0.1:5000/measurements``

RESTful API
-----------

| Interaction                                                    | Request                                                   |
|----------------------------------------------------------------|-----------------------------------------------------------|
| Advance simulation with control input and receive measurements |  POST ``advance`` with json data "{<input_name>:<value>}" |
| Reset simulation                                               |  PUT ``reset`` with no data                               |
| Receive simulation step                                        |  GET ``step``                                             |
| Set simulation step                                            |  PUT ``step`` with data ``step=<value>``                  |
| Receive measurement names (y)                                  |  GET ``measurements``                                     |
| Receive input names (u)                                        |  GET ``inputs``                                           |
| Receive test result data                                       |  GET ``results``                                          |
| Receive test KPIs                                              |  GET ``kpi``                                              |
| Receive test case name                                         |  GET ``name``                                             |


Structure
---------

- ``doc/`` contains documentation of the test case.
- ``interface/`` contains the RESTful API of test case.
- ``models/`` contains the emulation model files for the test case.
- ``process/`` contains functions for interacting with the test case.
- ``Dockerfile`` is a script that builds the test case docker image.
- ``makefile`` contains functions to build and deploy the test case image.