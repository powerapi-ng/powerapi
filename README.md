# PowerAPI

PowerAPI is a self-adaptive software-defined power meter for containerized environments.

# Quick start

## Installation without docker

requirement : python 3, [`pip`](https://pypi.org/project/pip/)

- install dependencies : python3 -m pip install --no-cache-dir -r requirements.txt
- run unit tests : `python -m pytest test/unit/`
- run integration tests : `python -m pytest test/integration/`

## Launch powerapi

Start command : 

	$ docker run powerapi input_hostname  input_port  input_database_name\
		                  input_collection_name output_hostname output_port\
						  output_database_name output_collection_name SOCKET
						
with : 

- hostname: Mongo server address. (localhost, IP address, ...)
- port: Mongo server port. (usually 27017)
- database_name: Database name.
- collection_name: Collection name.

# Contribution guideline

## Naming convention

We work with the current python linters for normalize our code: **pylint**, **flake8** and **mypy**.

When an actor is defined (class herited by the Actor main abstract class), try to respect this rules:
 - The package name have to follow this pattern: "xxxx_yyyy_actor.py"
 - The class name have to follow this pattern: "XxxxYyyyActor"

## Commit convention

- feat (feature)
- fix (bug fix)
- docs (documentation)
- style (formatting, missing semi colons, …)
- refactor
- test (when adding missing tests)
- chore (maintain)


