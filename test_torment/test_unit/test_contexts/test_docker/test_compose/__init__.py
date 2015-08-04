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
import unittest

from torment import contexts
from torment import decorators
from torment import fixtures
from torment import helpers

from torment.contexts.docker import compose

LOGGER = logging.getLogger(__name__)


class CallWrapperFixture(fixtures.Fixture):  # pylint: disable=C0111
    def __init__(self, context) -> None:
        super().__init__(context)

        self.parameters = {}

    @property
    def description(self) -> str:
        return super().description + '.{0.function_name}()'.format(self)  # pylint: disable=W1306

    def setup(self) -> None:
        LOGGER.debug('self.expected: %s', self.expected)  # pylint: disable=E0203

        self.expected = [ unittest.mock.call(*arguments[0], **arguments[1]) for arguments in self.expected ]

        if self.context.mock_call():
            self.context.mocked_call.return_value = 0

    def run(self) -> None:  # pylint: disable=C0111
        getattr(compose, self.function_name)(**self.parameters)  # pylint: disable=E1101

    def check(self) -> None:
        self.context.mocked_call.assert_has_calls(self.expected)


class UpFixture(CallWrapperFixture):  # pylint: disable=C0111
    @property
    def description(self) -> str:
        return super().description[:-1] + '{0.parameters[services]})'.format(self)  # pylint: disable=W1307


class ErrorUpFixture(CallWrapperFixture):  # pylint: disable=C0111
    @property
    def description(self) -> str:
        return super().description[:-1] + '{0.parameters[services]}) → {0.error}'.format(self)  # pylint: disable=W1307,W1306

    def run(self) -> None:
        with self.context.assertRaises(self.error.__class__, msg = self.error.args[0]) as error:  # pylint: disable=E1101
            compose.up(**self.parameters)

        self.exception = error.exception

    def check(self) -> None:
        self.context.assertEqual(self.exception.args, self.error.args)  # pylint: disable=E1101


helpers.import_directory(__name__, os.path.dirname(__file__))


class CallWrapperUnitTest(contexts.TestContext, metaclass = contexts.MetaContext):  # pylint: disable=C0111
    fixture_classes = (
        CallWrapperFixture,
    )

    mocks = set()  # type: Set[str]

    mocks.add('call')

    @decorators.mock('_call')
    def mock_call(self) -> None:  # pylint: disable=C0111
        self.patch('_call')
