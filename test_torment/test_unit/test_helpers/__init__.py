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

import importlib
import os
import typing  # pylint: disable=W0611
import unittest

from torment import contexts
from torment import fixtures

from torment import helpers


class EvertFixture(fixtures.Fixture):
    @property
    def description(self) -> str:
        return super().description + '.evert({0.parameters[iterable]}) == {0.expected}'.format(self)  # pylint: disable=W1306

    def run(self) -> None:  # pylint: disable=C0111
        self.result = list(helpers.evert(self.parameters['iterable']))  # pylint: disable=E1101

    def check(self) -> None:  # pylint: disable=C0111
        self.context.assertEqual(self.expected, self.result)  # pylint: disable=E1101


class ExtendFixture(fixtures.Fixture):  # pylint: disable=C0111
    @property
    def description(self) -> str:
        return super().description + '.extend({{ {0.parameters[base]} }}, {{ {0.parameters[extension]} }}) == {{ {0.expected} }}'.format(self)  # pylint: disable=W1306

    def run(self) -> None:  # pylint: disable=C0111
        self.result = helpers.extend(self.parameters['base'], self.parameters['extension'])  # pylint: disable=E1101

    def check(self) -> None:  # pylint: disable=C0111
        self.context.assertEqual(self.expected, self.result)  # pylint: disable=E1101


class MergeFixture(fixtures.Fixture):
    @property
    def description(self) -> str:
        return super().description + '.merge({{ {0.parameters[base]} }}, {{ {0.parameters[extension]} }}) == {{ {0.expected} }}'.format(self)  # pylint: disable=W1306

    def run(self) -> None:
        self.result = helpers.merge(self.parameters['base'], self.parameters['extension'])  # pylint: disable=E1101

    def check(self) -> None:
        self.context.assertEqual(self.expected, self.result)  # pylint: disable=E1101


class PowersetFixture(fixtures.Fixture):
    @property
    def description(self) -> str:
        return super().description + '.powerset({0.parameters[iterable]}) == {0.expected}'.format(self)  # pylint: disable=W1306

    def run(self) -> None:
        self.result = list(helpers.powerset(self.parameters['iterable']))  # pylint: disable=E1101

    def check(self) -> None:
        self.context.assertEqual(self.expected, self.result)  # pylint: disable=E1101

helpers.import_directory(__name__, os.path.dirname(__file__))


class HelperUnitTest(contexts.TestContext, metaclass = contexts.MetaContext):  # pylint: disable=C0111
    fixture_classes = (
        EvertFixture,
        ExtendFixture,
        MergeFixture,
        PowersetFixture,
    )


class ImportDirectoryUnitTest(unittest.TestCase):  # pylint: disable=C0111
    def setUp(self) -> None:
        _ = unittest.mock.patch('helpers.importlib', wraps = importlib)
        self.mocked_importlib = _.start()
        self.addCleanup(_.stop)

    @unittest.skip('implementation needed')
    def test_import_zero_modules(self) -> None:
        '''torment.helpers.import_directory(module_base, './mock_import_directories/zero')'''

        self.fail('implement me')

        helpers.import_directory(self.__module__, 'mock_import_directories/zero')

        self.assertFalse(self.mocked_importlib.import_module.called)  # pylint: disable=E1101


class FilenamesToModulenamesUnitTest(unittest.TestCase):  # pylint: disable=C0111
    def test_zero_filenames(self) -> None:
        '''torment.helpers._filenames_to_modulenames([], 'test_helpers', 'test_helpers') == []'''

        mns = helpers._filenames_to_modulenames([], 'test_helpers', 'test_helpers')  # pylint: disable=W0212

        self.assertCountEqual([], mns)

    def test_one_filenames_proper(self) -> None:
        '''torment.helpers._filenames_to_modulenames([ 'test_helpers/extend_dc1fe29410fc4587bae0962d519f94ce.py', ], 'test_helpers', 'test_helpers') == [ test_helpers.extend_dc1fe29410fc4587bae0962d519f94ce', ]'''

        mns = helpers._filenames_to_modulenames([ 'test_helpers/extend_dc1fe29410fc4587bae0962d519f94ce.py', ], 'test_helpers', 'test_helpers')  # pylint: disable=W0212

        self.assertCountEqual([ 'test_helpers.extend_dc1fe29410fc4587bae0962d519f94ce', ], mns)

    def test_one_filenames_init(self) -> None:
        '''torment.helpers._filenames_to_modulenames([ 'test_helpers/__init__.py', ], 'test_helpers', 'test_helpers') == []'''

        mns = helpers._filenames_to_modulenames([], 'test_helpers', 'test_helpers')  # pylint: disable=W0212

        self.assertCountEqual([], mns)

    def test_one_filenames_without_py(self) -> None:
        '''torment.helpers._filenames_to_modulenames([ 'test_helpers/data.txt', ], 'test_helpers', 'test_helpers') == []'''

        mns = helpers._filenames_to_modulenames([], 'test_helpers', 'test_helpers')  # pylint: disable=W0212

        self.assertCountEqual([], mns)

    @unittest.skip('test known_symbols logic')
    def test_one_filenames_with_duplicate_symbols(self) -> None:
        '''torment.helpers._filenames_to_modulenames([ …, ], 'test_helpers', 'test_helpers') == [ …, ]'''

        pass
