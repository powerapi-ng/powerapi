import os
import sys

from setuptools import setup
from setuptools.command.install import install

import powerapi



def get_tag():
    """get tag from the circle_ci env and remove the first character (v)"""
    return os.getenv('CIRCLE_TAG')[1:]


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = get_tag()

        if tag != powerapi.__version__:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, powerapi.__version__
            )
            sys.exit(info)


setup(cmdclass={
        'verify': VerifyVersionCommand,
    })
