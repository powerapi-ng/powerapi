# SmartWatts

SmartWatts is a self-adaptive software-defined power meter for containerized environments.

# Usage

## Without docker

requirement : [`poetry`](https://github.com/sdispater/poetry)

- run unit tests : `poetry run pytest smartwatts/test/`
- install dependency : `poetry install`
- run smartwatts as command line interface : `poetry run main`

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


