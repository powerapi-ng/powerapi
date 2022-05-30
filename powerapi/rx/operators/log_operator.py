# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Author : Daniel Romero Acero
# Last modified : 2 May 2022

##############################
#
# Imports
#
##############################
import logging
import sys
from abc import abstractmethod
from typing import Optional

import colorlog as colorlog
import rx.operators
from rx import Observable
from rx.core.typing import Scheduler, Observer, Subject

from powerapi.rx.report import Report
from powerapi.rx.source import Source

##############################
#
# Constants
#
##############################

LOGGING_TYPES = [logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]


##############################
#
# Classes
#
##############################

class PowerAPILogFormatter(colorlog.ColoredFormatter):
    """ Simple formatter for PowerAPI logging"""

    def __init__(self):
        super().__init__('%(log_color)s [%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s',
                         datefmt='%a, %d %b %Y %H:%M:%S')

    def formatException(self, exc_info):
        result = super().formatException(exc_info)
        return repr(result)

    def format(self, record):
        result = super().format(record)
        if record.exc_text:
            result = result.replace("\n", "")
        return result

class LogOperator(Observable):
    """ Class for configuring PowerAPI loggers """

    def __init__(self, logger_name: str, level: int = logging.NOTSET) -> None:
        """ Creates a new logger
        
            If the given level is not in LOGGING_TYPES, logging.NOTSET is set by default

            Args:
                logger_name : The name that will be used for creating the log
                level : The log level, i.e., CRITICAL (50), ERROR (40), WARNING (30), INFO (20) DEBUG (10) NOTSET (0)
        """
        self.logger_name = logger_name
        self.operator = None
        if level not in LOGGING_TYPES:
            level = logging.NOTSET

        handler = logging.StreamHandler(sys.stdout)
        formatter = PowerAPILogFormatter()
        handler.setFormatter(formatter)

        # We configure the logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.addHandler(handler)

    def __call__(self, source: Source):
        log_report = self.log_report
        log_error = self.log_error

        def subscribe(operator: Observer, scheduler: Optional[Scheduler] = None):
            """ Required method for subscribing reports received by the logger

                Args:
                    operator: The observer (e.g. a destination) that will process the output of the logger
                    scheduler: Used for parallelism. Not used for the time being
            """
            nonlocal log_report
            nonlocal log_error
            nonlocal self
            self.operator = operator

            return source.subscribe(
                log_report,
                log_error,
                log_report,
                scheduler)

        self._subscribe = subscribe
        return self

        return rx.pipe(rx.operators.do(lambda event: self.log_event()))

    def log_report(self, report: Report):

        logger = logging.getLogger(self.logger_name)
        level = logger.level

        # We log events according to their types and log levels
        if level <= logging.DEBUG:
            logger.debug("Report of type {class_name} sent".format(class_name=report.__class__.__name__))
        elif level <= logging.INFO:
            logger.info("Report Sent: {report}".format(report=report))

        self.operator.on_next(report)

    def log_error(self, error):
        logger = logging.getLogger(self.logger_name)
        level = logger.level

        if level >= logging.ERROR:
            logger.error("The following error was found: {error}".format(error=error))

        self.operator.on_error(error)
