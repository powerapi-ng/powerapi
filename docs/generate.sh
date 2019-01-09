#!/bin/bash

rm -Rf build/
rm -Rf ./source/_doc/
sphinx-apidoc -f -o ./source/_doc/ ../smartwatts
sphinx-build source/ build/
