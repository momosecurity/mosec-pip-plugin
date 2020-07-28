"""
Copyright 2020 momosecurity.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging
import sys
from mosec.colorama.ansi import Fore, Style


class Logger(object):
    def __init__(self, name, level=logging.INFO):
        self.logger = logging.getLogger(name=name)
        # set lowest info critical > error > warning > info > debug
        self.logger.setLevel(level)

        self.ch = logging.StreamHandler(sys.stdout)
        self.ch.setLevel(level)
        self.logger.addHandler(self.ch)

    def debug(self, msg):
        self.logger.debug(str(msg))

    def warn(self, msg):
        self.logger.warning(Fore.YELLOW + str(msg) + Style.RESET_ALL)

    def info(self, msg):
        self.logger.info(Fore.LIGHTGREEN_EX + str(msg) + Style.RESET_ALL)

    def error(self, msg):
        self.logger.error(Fore.LIGHTRED_EX + str(msg) + Style.RESET_ALL)

    def set_log_level(self, level):
        self.logger.setLevel(level)
        self.ch.setLevel(level)
