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

import unittest
import unittest.mock
import re
import logging
import typing  # pylint: disable=W0611
import warnings

from typing import Any
from typing import Callable

from torment import decorators
from torment import fixtures

LOGGER = logging.getLogger(__name__)


@property
def _module(self) -> str:
    '''Actual module name corresponding to this context's testing module.'''

    return re.sub(r'\.[^.]+', '', self.__module__.replace('test_', ''), 1)


class MetaContext(type):
    '''``torment.TestContext`` class creator.

    Generates all testing methods that correspond with the fixtures associated
    with a ``torment.TestContext``.  Also updates the definitions of
    ``mocks_mask`` and ``mocks`` to include the union of all involved classes
    in the creation process (all parent classes and the class being created).

    When creating a ``torment.TestContext`` subclass, ensure you specify this
    class as its metaclass to automatically generate test cases based on its
    ``fixture_classes`` property.

    '''

    module = _module

    def __init__(cls, name, bases, dct) -> None:
        super(MetaContext, cls).__init__(name, bases, dct)

        cls.mocks_mask = set().union(getattr(cls, 'mocks_mask', set()), *[ getattr(base, 'mocks_mask', set()) for base in bases ])
        cls.mocks = set().union(getattr(cls, 'mocks', set()), *[ getattr(base, 'mocks', set()) for base in bases ])

        cls.docker_compose_services = set().union(getattr(cls, 'docker_compose_services', set()), *[ getattr(base, 'docker_compose_services', set()) for base in bases ])

        def generate_case(fixture: fixtures.Fixture) -> Callable[[Any], None]:
            '''Generate a ``unittest.TestCase`` compatible test method.

            Parameters
            ----------

            :``fixture``: the fixture to transform into a ``unittest.TestCase``
                          compatible test method

            Return Value(s)
            ---------------

            An acceptable method that nose will execute as a test case.

            '''

            def case(self) -> None:  # pylint: disable=C0111
                fixture.context = self
                fixture.execute()

            case.__name__ = fixture.name
            case.__doc__ = fixture.description

            if len(cls.mocks_mask):
                case.__doc__ += '—unmocked:' + ','.join(sorted(cls.mocks_mask))

            return case

        if not hasattr(cls, 'fixture_classes'):
            warnings.warn('type object \'{0}\' has no attribute \'fixture_classes\'')
        else:
            for fixture in fixtures.of(cls.fixture_classes, context = cls):
                case = generate_case(fixture)
                setattr(cls, case.__name__, case)


class TestContext(unittest.TestCase):
    '''Environment for Fixture execution.

    Provides convenience methods indicating the environment a Fixture is
    executing in.  This includes a references to the real module corresponding
    to the context's testing module as well as a housing for the assertion
    methods.

    Inherits most of its functionality from ``unittest.TestCase`` with a couple
    of additions.  TestContext does extend setUp.

    When used in conjunction with ``torment.MetaContext``, the
    ``fixture_classes`` property must be an iterable of subclasses of
    ``torment.fixtures.Fixture``.

    **Properties**

    * ``module``

    **Public Methods**

    * ``patch``

    **Class Variables**

    :``mocks_mask``: set of mocks to mask from being mocked
    :``mocks``:      set of mocks this TestContext provides

    '''

    mocks_mask = set()  # type: Set[str]
    mocks = set()  # type: Set[str]

    module = _module

    def setUp(self) -> None:
        super().setUp()

        LOGGER.debug('self.__class__.mocks_mask: %s', self.__class__.mocks_mask)
        LOGGER.debug('self.__class__.mocks: %s', self.__class__.mocks)

    @decorators.log
    def patch(self, name: str, relative: bool = True) -> None:
        '''Patch name with mock in actual module.

        Sets up mock objects for the given symbol in the actual module
        corresponding to this context's testing module.

        **Parameters**

        :``name``:     the symbol to mock—must exist in the actual module under test
        :``relative``: prefix actual module corresponding to this context's
                       testing module to the given symbol to patch

        '''

        prefix = ''

        if relative:
            prefix = self.module + '.'

        LOGGER.debug('prefix: %s', prefix)

        _ = unittest.mock.patch(prefix + name)
        setattr(self, 'mocked_' + name.replace('.', '_').strip('_'), _.start())
        self.addCleanup(_.stop)
