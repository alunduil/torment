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

import hypothesis
import hypothesis.strategies
import importlib
import itertools
import logging
import os
import typing  # noqa (use mypy typing)
import unittest

from torment import contexts
from torment import fixtures

from torment import helpers

logger = logging.getLogger(__name__)


class EvertFixture(fixtures.Fixture):
    @property
    def description(self) -> str:
        return super().description + '.evert({0.parameters[iterable]}) == {0.expected}'.format(self)

    def run(self) -> None:
        self.result = list(helpers.evert(self.parameters['iterable']))

    def check(self) -> None:
        self.context.assertEqual(self.expected, self.result)


class ExtendFixture(fixtures.Fixture):
    @property
    def description(self) -> str:
        return super().description + '.extend({{ {0.parameters[base]} }}, {{ {0.parameters[extension]} }}) == {{ {0.expected} }}'.format(self)

    def run(self) -> None:
        self.result = helpers.extend(self.parameters['base'], self.parameters['extension'])

    def check(self) -> None:
        self.context.assertEqual(self.expected, self.result)


class MergeFixture(fixtures.Fixture):
    @property
    def description(self) -> str:
        return super().description + '.merge({{ {0.parameters[base]} }}, {{ {0.parameters[extension]} }}) == {{ {0.expected} }}'.format(self)

    def run(self) -> None:
        self.result = helpers.merge(self.parameters['base'], self.parameters['extension'])

    def check(self) -> None:
        self.context.assertEqual(self.expected, self.result)


class PowersetFixture(fixtures.Fixture):
    @property
    def description(self) -> str:
        return super().description + '.powerset({0.parameters[iterable]}) == {0.expected}'.format(self)

    def run(self) -> None:
        self.result = list(helpers.powerset(self.parameters['iterable']))

    def check(self) -> None:
        self.context.assertEqual(self.expected, self.result)

helpers.import_directory(__name__, os.path.dirname(__file__))


class HelperUnitTest(contexts.TestContext, metaclass = contexts.MetaContext):
    fixture_classes = (
        EvertFixture,
        ExtendFixture,
        MergeFixture,
        PowersetFixture,
    )


class BinaryPartitionUnitTest(unittest.TestCase):
    @hypothesis.given(hypothesis.strategies.lists(elements = hypothesis.strategies.integers()))
    def test_even_and_odd(self, items):
        '''torment.helpers.binary_partition(lambda item: item % 2, [ 1, 2, … ]) == ( [ 1, 3, … ], [ 2, 4, … ], )'''

        evens, odds = helpers.binary_partition(lambda item: item % 2, items)

        self.assertTrue(all([ n % 2 == 0 for n in evens ]))
        self.assertTrue(all([ n % 2 == 1 for n in odds ]))


class ImportDirectoryUnitTest(unittest.TestCase):
    def setUp(self) -> None:
        _ = unittest.mock.patch('helpers.importlib', wraps = importlib)
        self.mocked_importlib = _.start()
        self.addCleanup(_.stop)

    @unittest.skip('implementation needed')
    def test_import_zero_modules(self) -> None:
        '''torment.helpers.import_directory(module_base, './mock_import_directories/zero')'''

        self.fail('implement me')

        helpers.import_directory(self.__module__, 'mock_import_directories/zero')

        self.assertFalse(self.mocked_importlib.import_module.called)


class FilenamesToModulenamesUnitTest(unittest.TestCase):
    def test_zero_filenames(self) -> None:
        '''torment.helpers._filenames_to_modulenames([], 'test_helpers', 'test_helpers') == []'''

        mns = helpers._filenames_to_modulenames([], 'test_helpers', 'test_helpers')

        self.assertCountEqual([], mns)

    def test_one_filenames_proper(self) -> None:
        '''torment.helpers._filenames_to_modulenames([ 'test_helpers/extend_dc1fe29410fc4587bae0962d519f94ce.py', ], 'test_helpers', 'test_helpers') == [ test_helpers.extend_dc1fe29410fc4587bae0962d519f94ce', ]'''

        mns = helpers._filenames_to_modulenames([ 'test_helpers/extend_dc1fe29410fc4587bae0962d519f94ce.py', ], 'test_helpers', 'test_helpers')

        self.assertCountEqual([ 'test_helpers.extend_dc1fe29410fc4587bae0962d519f94ce', ], mns)

    def test_one_filenames_init(self) -> None:
        '''torment.helpers._filenames_to_modulenames([ 'test_helpers/__init__.py', ], 'test_helpers', 'test_helpers') == []'''

        mns = helpers._filenames_to_modulenames([], 'test_helpers', 'test_helpers')

        self.assertCountEqual([], mns)

    def test_one_filenames_without_py(self) -> None:
        '''torment.helpers._filenames_to_modulenames([ 'test_helpers/data.txt', ], 'test_helpers', 'test_helpers') == []'''

        mns = helpers._filenames_to_modulenames([], 'test_helpers', 'test_helpers')

        self.assertCountEqual([], mns)

    @unittest.skip('test known_symbols logic')
    def test_one_filenames_with_duplicate_symbols(self) -> None:
        '''torment.helpers._filenames_to_modulenames([ …, ], 'test_helpers', 'test_helpers') == [ …, ]'''

        pass

DIGITS = [ str(_) for _ in range(10) ]


class TopologicalSortUnitTest(unittest.TestCase):
    def test_empty_graph(self):
        '''torment.helpers.topological_sort({}) == []'''

        self.assertEqual(helpers.topological_sort({}), [])

    def test_single_resolvable(self):
        '''torment.helpers.topological_sort({ 'a': [], }) == [ 'a', ]'''

        self.assertEqual(helpers.topological_sort({ 'a': [], }), [ 'a', ])

    def test_single_unresolvable(self):
        '''torment.helpers.topological_sort({ 'a': [ 'b', ], }) → RuntimeError'''

        with self.assertRaises(RuntimeError):
            helpers.topological_sort({ 'a': [ 'b', ], })

    @hypothesis.given(hypothesis.strategies.dictionaries(keys = hypothesis.strategies.text(alphabet = DIGITS, min_size = 1, max_size = 1), values = hypothesis.strategies.lists(elements = hypothesis.strategies.text(alphabet = DIGITS, min_size = 1, max_size = 1), max_size = 10, unique = True), max_size = 10))
    def test_deep_resolvable(self, graph):
        '''torment.helpers.topological_sort({ … }) == [ … ]'''

        def has_cycle(graph):
            cycle = False

            predecessors = [ ( node, node, ) for node in graph.keys() ]
            logger.debug('predecessors: %s', predecessors)

            while len(predecessors):
                predecessors = [ ( node + path, node, ) for path, successor in predecessors for node in graph.keys() if successor in graph[node] ]
                logger.debug('predecessors: %s', predecessors)

                if any([ len(predecessor[0]) != len(set(predecessor[0])) for predecessor in predecessors ]):
                    cycle = True
                    break

            logger.debug('len(predecessors): %s', len(predecessors))

            return cycle

        hypothesis.assume(len([ key for key in graph.keys() if not len(graph[key]) ]))
        hypothesis.assume(set(graph.keys()) >= set(itertools.chain(*graph.values())))
        hypothesis.assume(all([ key not in graph[key] for key in graph.keys() ]))
        hypothesis.assume(not has_cycle(graph))

        result = helpers.topological_sort(graph)

        logger.debug('result: %s', result)

        self.assertEqual(len(result), len(graph.keys()))
        self.assertEqual(set(result), set(graph.keys()))
