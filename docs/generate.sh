#!/bin/bash

rm -Rf build/
rm -Rf ./source/_doc/
sphinx-apidoc -f -o ./source/_doc/ ../powerapi
sphinx-build source/ build/
