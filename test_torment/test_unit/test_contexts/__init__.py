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
import typing  # pylint: disable=W0611
import unittest
import unittest.mock

from torment import contexts

LOGGER = logging.getLogger(__name__)


def PATCH():  # pylint: disable=invalid-name
    return 'not patched'


class MetaContextGenerateCasesUnitTest(unittest.TestCase):  # pylint: disable=C0111
    def setUp(self) -> None:
        _ = unittest.mock.patch('torment.contexts.fixtures.of')
        self.mocked_fixtures_of = _.start()
        self.addCleanup(_.stop)

        self.directory = [
            '__class__',
            '__delattr__',
            '__dict__',
            '__dir__',
            '__doc__',
            '__eq__',
            '__format__',
            '__ge__',
            '__getattribute__',
            '__gt__',
            '__hash__',
            '__init__',
            '__le__',
            '__lt__',
            '__module__',
            '__ne__',
            '__new__',
            '__reduce__',
            '__reduce_ex__',
            '__repr__',
            '__setattr__',
            '__sizeof__',
            '__str__',
            '__subclasshook__',
            '__weakref__',
            'docker_compose_services',
            'mocks',
            'mocks_mask',
        ]

    def test_null_fixture_classes(self) -> None:
        '''torment.contexts.MetaContext: fixture_classes == ø'''

        with self.assertWarns(UserWarning):
            class NullFixtureClasses(object, metaclass = contexts.MetaContext):  # pylint: disable=C0111,R0903
                pass

        self.assertCountEqual(dir(NullFixtureClasses), self.directory)

    def test_zero_fixture_classes(self) -> None:
        '''torment.contexts.MetaContext: len(fixture_classes) == 0'''

        self.mocked_fixtures_of.return_value = []

        class ZeroFixtureClasses(object, metaclass = contexts.MetaContext):  # pylint: disable=C0111,R0903
            fixture_classes = ()

        self.directory.append('fixture_classes')

        self.assertCountEqual(dir(ZeroFixtureClasses), self.directory)

    def test_one_fixture_classes(self) -> None:
        '''torment.contexts.MetaContext: len(fixture_classes) > 0'''

        class DummyFixtureA(object):  # pylint: disable=C0111
            @property
            def name(self) -> str:  # pylint: disable=C0111,R0201
                return 'test_method'

            @property
            def description(self) -> str:  # pylint: disable=C0111,R0201
                return 'test_method'

        self.mocked_fixtures_of.return_value = [ DummyFixtureA(), ]

        class ManyFixtureClasses(object, metaclass = contexts.MetaContext):  # pylint: disable=C0111,R0903
            fixture_classes = ( DummyFixtureA, )

        self.directory.extend([
            'fixture_classes',
            'test_method',
        ])

        self.assertCountEqual(dir(ManyFixtureClasses), self.directory)


class TestContextPropertyUnitTest(unittest.TestCase):  # pylint: disable=C0111
    def setUp(self) -> None:
        self.c = contexts.TestContext()  # pylint: disable=C0103

    def test_testcontext_mocks(self) -> None:
        '''torment.contexts.TestContext().mocks == {}'''

        self.assertEqual(self.c.mocks, set())

    def test_testcontext_mocks_mask(self) -> None:
        '''torment.contexts.TestContext().mocks_mask == {}'''

        self.assertEqual(self.c.mocks_mask, set())

    def test_testcontext_module(self) -> None:
        '''torment.contexts.TestContext().module == 'torment.fixtures' '''

        self.c.__module__ = 'test_torment.test_unit.test_fixtures'

        self.assertEqual(self.c.module, 'torment.fixtures')


class TestContextPatchUnitTest(unittest.TestCase):  # pylint: disable=C0111
    def test_testcontext_patch(self) -> None:
        '''torment.contexts.TestContext().patch('PATCH')'''

        LOGGER.debug('self.__module__: %s', self.__module__)

        _ = unittest.mock.patch.object(contexts.TestContext, 'module', self.__module__)
        _.start()
        self.addCleanup(_.stop)

        c = contexts.TestContext()  # pylint: disable=C0103

        c.patch('PATCH')

        self.assertTrue(hasattr(c, 'mocked_PATCH'))
        self.assertIsInstance(c.mocked_PATCH, unittest.mock.MagicMock)  # pylint: disable=E1101
