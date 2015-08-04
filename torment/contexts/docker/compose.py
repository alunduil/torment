# Copyright 2015 Alex Brandt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import select
import subprocess
import typing  # pylint: disable=W0611

from typing import Iterable

LOGGER = logging.getLogger(__name__)


def found() -> bool:
    '''Determines if docker-compose is available as a shell command.

    Not only determines if docker-compose is available in the shell's PATH but
    also ensures that docker-compose can successfully stop all services.

    Return Value(s)
    ---------------

    True if docker-compose is available and functional; otherwise, False.

    '''

    return 0 == _call('which docker-compose', shell = True) and 0 == stop()


def stop() -> int:
    '''Stop all docker-compose services.

    Return Value(s)
    ---------------

    The integer status of ``docker-compose stop``.

    '''

    return _call('docker-compose stop', shell = True)


def up(services: Iterable[str] = ()) -> int:  # pylint: disable=C0103
    '''Start the specified docker-compose services.

    Parameters
    ----------

    :``services``: a list of docker-compose service names to start (must be
                   defined in docker-compose.yml)

    Return Value(s)
    ---------------

    The integer status of ``docker-compose up``.

    '''

    services = list(services)

    if not len(services):
        raise ValueError('empty iterable passed to up(): {0}'.format(services))

    return _call('docker-compose up --no-color -d --no-deps ' + ' '.join(services), shell = True)


def _call(command: str, *args, **kwargs) -> int:
    '''Wrapper around ``subprocess.Popen`` that sends command output to logger.

    .. seealso::

       ``subprocess.Popen``_

    Parameters
    ----------

    :``command``: string form of the command to execute

    All other parameters are passed directly to ``subprocess.Popen``.

    Return Value(s)
    ---------------

    The integer status of command.

    '''

    child = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, *args, **kwargs)

    def log():
        '''Send processes stdout and stderr to logger.'''

        for fh in select.select(( child.stdout, child.stderr, ), (), (), 0)[0]:  # pylint: disable=C0103
            line = fh.readline()[:-1]

            if len(line):
                getattr(LOGGER, {
                    child.stdout: 'debug',
                    child.stderr: 'error',
                }[fh])('%s: %s', command, line)

    while child.poll() is None:
        log()

    log()

    return child.wait()
