mkdir powerapi_pypy
cp -R powerapi powerapi_pypy/
cp setup.cfg setup.py powerapi_pypy/
cp pypy/to_3.6.sh pypy/Dockerfile powerapi_pypy/

cd powerapi_pypy
sh to_3.6.sh
version=$(python3 -c "import powerapi; print(powerapi.__version__)")
docker build . --tag powerapi/powerapi:$version-pypy
