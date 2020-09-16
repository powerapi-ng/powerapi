sed -i 's/ *-> *[[:alnum:]]*Report//g' $(find powerapi/ -name "*.py")
sed -i 's/from __future__ import annotations//g' $(find powerapi/ -name "*.py")
sed -i 's/python_requires = >= 3\.[0-9]/python_requires = >= 3.6/g' setup.cfg
					 
