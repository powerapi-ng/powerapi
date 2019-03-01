from setuptools import setup, find_packages
import powerapi

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name='powerapi',
      version=powerapi.__version__,
      description='PowerAPI is a middleware toolkit for building software-defined power meters.',
      url='http://github.com/powerapi-ng/powerapi',
      author='Fiene Guillaume, D\'Azémar Arthur, Bouchoucha Jordan, Rouvoy Romain',
      author_email='powerapi-staff@inria.fr',
      license='AGPL-3.0',
      packages=find_packages(exclude=("test",)),
      install_requires=requirements,
      entry_points={
          'console_scripts': [
              'powerapi-cli=powerapi.__main__:main'
          ]
      },
      zip_safe=False)
