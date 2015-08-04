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
import os
import typing  # pylint: disable=W0611
import urllib

from torment import contexts
from torment.contexts.docker import compose

LOGGER = logging.getLogger(__name__)


class DockerContext(contexts.TestContext):
    '''Environment including docker-compose for Fixture execution.

    Extends ``torment.contexts.TestContext`` to include docker-compose
    integration to allow specific services to be live during test runs.

    Provides staticmethods for setUpModule and tearDownModule that should be
    assigned to the corresponding functions in integration modules (to ensure
    that docker-compose is prepared).

    Properties
    ----------

    :``host``: the IP for connecting to docker-compose services

    Static Methods
    --------------

    * ``setUpModule``
    * ``tearDownModule``

    Class Variables
    ---------------

    :``docker_compose_services``: services defined in docker-compose.yml that
                                  this TestContext should start and stop for
                                  each test case

    '''

    docker_compose_services = set()  # type: Set[str]

    @staticmethod
    def setUpModule() -> None:  # pylint: disable=C0103
        '''Ensure docker-compose is available and all services are stopped.

        Must be set in the module as the module's setUpModule function::

            from torment import contexts
            setUpModule = contexts.docker.DockerContext.setUpModule

        '''

        compose.found()

    @staticmethod
    def tearDownModule() -> None:  # pylint: disable=C0103
        '''Ensure docker-compose is stopped when the module is finished.

        Must be set in the module as the module's tearDownModule function::

            from torment import contexts
            tearDownModule = contexts.docker.DockerContext.tearDownModule

        '''

        if compose.found():
            compose.stop()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.host = urllib.parse.urlparse(os.environ.get('DOCKER_HOST', 'tcp://127.0.0.1')).hostname

    def setUp(self) -> None:
        if not compose.found():
            self.skipTest('docker-compose not found')

        super().setUp()

        LOGGER.debug('self.__class__.docker_compose_services: %s', self.__class__.docker_compose_services)

        compose.up(self.docker_compose_services)
        self.addCleanup(compose.stop)
