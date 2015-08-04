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

import os
import typing  # pylint: disable=W0611
import unittest

from torment.contexts import docker


class DockerContextPropertyUnitTest(unittest.TestCase):  # pylint: disable=C0111
    def setUp(self) -> None:
        self.c = docker.DockerContext()  # pylint: disable=C0103

    def test_dockercontext_docker_compose_services(self) -> None:  # pylint: disable=C0103
        '''torment.contexts.DockerContext().docker_compose_services == {}'''

        self.assertEqual(self.c.docker_compose_services, set())

    def test_dockercontext_host(self) -> None:
        '''torment.contexts.DockerContext().host == '127.0.0.1' '''

        self.assertEqual(self.c.host, '127.0.0.1')

    def test_dockercontext_remote_host(self) -> None:
        '''torment.contexts.DockerContext().host == '192.0.2.103' '''

        os.environ['DOCKER_HOST'] = 'tcp://192.0.2.103:2376'
        self.addCleanup(lambda: os.environ.pop('DOCKER_HOST'))

        self.c = docker.DockerContext()

        self.assertEqual(self.c.host, '192.0.2.103')
