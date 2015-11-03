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

import copy
import dis
import functools
import inspect
import logging
import os
import typing  # noqa (use mypy typing)
import uuid

from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Tuple
from typing import Union

from torment import decorators
from torment import helpers

logger = logging.getLogger(__name__)


class Fixture(object):
    '''Collection of data and actions for a particular test case.

    Intended as a base class for custom fixtures.  Fixture provides an API
    that simplifies writing scalable test cases.

    Creating Fixture objects is broken into two parts.  This keeps the logic for
    a class of test cases separate from the data for particular cases while
    allowing re-use of the data provided by a fixture.

    The first part of Fixture object creation is crafting a proper subclass that
    implements the necessary actions:

    :``__init__``:   pre-data population initialization
    :``initialize``: post-data population initialization
    :``setup``:      pre-run setup
    :``run``:        REQUIRED—run code under test
    :``check``:      verify results of run

    .. note::
        ``initialize`` is run during ``__init__`` and setup is run after;
        otherwise, they serve the same function.  The split allows different
        actions to occur in different areas of the class heirarchy and generally
        isn't necessary.

    By default all actions are noops and simply do nothing but run is required.
    These actions allow complex class hierarchies to provide nuanced testing
    behavior.  For example, Fixture provides the absolute bare minimum to test
    any Fixture and no more.  By adding a set of subclasses, common
    initialization and checks can be performed at one layer while specific run
    decisions and checks can happen at a lower layer.

    The second part of Fixture object creation is crafting the data.  Tying data
    to a Fixture class should be done with ``torment.fixtures.register``.  It
    provides a declarative interface that binds a dictionary to a Fixture (keys
    of dictionary become Fixture properties).  ``torment.fixtures.register``
    creates a subclass that the rest of the torment knows how to transform into
    test cases that are compatible with nose.

    **Examples**

    Simplest Fixture subclass:

    .. code-block:: python

       class MyFixture(Fixture):
           pass

    Of course, to be useful the Fixture needs definitions of setup, run, and
    check that actually test the code we're interested in checking:

    .. code-block:: python

       def add(x, y):
           return x + y

       class AddFixture(Fixture):
           def run(self):
               self.result = add(self.parameters['x'], self.parameters['y'])

           def check(self):
               self.context.assertEqual(self.result, self.expected)

    This fixture uses a couple of conventions (not requirements):

    #. ``self.parameters`` as a dictionary of parameter names to values
    #. ``self.expected`` as the value we expect as a result
    #. ``self.result`` as the holder inside the fixture between ``run`` and
       ``check``

    This show-cases the ridiculity of using this testing framework for simple
    functions that have few cases that require testing.  This framework is
    designed to allow many cases to be easily and declaritively defined.

    The last component required to get these fixtures to actually run is hooking
    them together with a context:

    .. code-block:: python

       from torment import contexts

       class AddUnitTest(contexts.TestContext, metaclass = contexts.MetaContext):
           fixture_classes = (
               MyFixture,
               AddFixture,
           )

    The context that wraps a Fixture subclass should eventually inherit from
    TestContext (which inherits from ``unittest.TestCase`` and provides its assert
    methods).  In order for nose to find and execute this ``TestContext``, it
    must have a name that contains Test.

    **Properties**

    * ``category``
    * ``description`` (override)
    * ``name`` (do **not** override)

    **Methods To Override**

    * ``__init__``
    * ``check``
    * ``initialize``
    * ``run (required)``
    * ``setup``

    **Instance Variables**

    :``context``: the ``torment.TestContext`` this case is running in which
                  provides the assertion methods of ``unittest.TestCase``.

    '''

    def __init__(self, context: 'torment.TestContext') -> None:
        '''Create Fixture

        Initializes the Fixture's context (can be changed like any other
        property).

        **Parameters**

        :``context``: a subclass of ``torment.TestContext`` that provides
                      assertion methods and any other environmental information
                      for this test case

        '''

        self.context = context

    @property
    def category(self) -> str:
        '''Fixture's category (the containing testing module name)

        **Examples**

        :module:   test_torment.test_unit.test_fixtures.fixture_a44bc6dda6654b1395a8c2cbd55d964d
        :category: fixtures

        '''

        logger.debug('dir(self.__module__): %s', dir(self.__module__))

        return self.__module__.__name__.rsplit('.', 2)[-2].replace('test_', '')

    @property
    def description(self) -> str:
        '''Test name in nose output (intended to be overridden).'''

        return '{0.uuid.hex}—{1}'.format(self, self.context.module)

    @property
    def name(self) -> str:
        '''Method name in nose runtime.'''

        return 'test_' + self.__class__.__name__

    def initialize(self) -> None:
        '''Post-data population initialization hook.

        .. note::
            Override as necessary.  Default provided so re-defenition is not
            necessary.

        Called during ``__init__`` and after properties have been populated by
        ``torment.fixtures.register``.


        '''

        pass

    def setup(self) -> None:
        '''Pre-run initialization hook.

        .. note::
            Override as necessary.  Default provided so re-defenition is not
            necessary.

        Called after properties have been populated by
        ``torment.fixtures.register``.

        '''

        pass

    def check(self) -> None:
        '''Check that run ran as expected.

        .. note::
            Override as necessary.  Default provided so re-defenition is not
            necessary.

        Called after ``run`` and should be used to verify that run performed the
        expected actions.

        '''

        pass

    def _execute(self) -> None:
        '''Run Fixture actions (setup, run, check).

        Core test loop for Fixture.  Executes setup, run, and check in order.

        '''

        self.setup()
        self.run()
        self.check()


class ErrorFixture(Fixture):
    '''Common error checking for Fixture.

    Intended as a mixin when registering a new Fixture (via register) that will
    check an error case (one throwing an exception).

    **Examples**

    Using the AddFixture from the Examples in Fixture, we can create a Fixture
    that handles (an obviously contrived) exception by either crafting a new
    Fixture object or invoking register with the appropriate base classes.

    New Fixture Object:

    .. code-block:: python

       class ErrorAddFixture(ErrorFixture, AddFixture):
           pass

    Via call to register:

    .. code-block:: python

       register(globals(), ( ErrorFixture, AddFixture, ), { … })

    '''

    @property
    def description(self) -> str:
        '''Test name in nose output (adds error reason as result portion).'''

        return super().description + ' → {0.error}'.format(self)

    def run(self) -> None:
        '''Calls sibling with exception expectation.'''

        with self.context.assertRaises(self.error.__class__) as error:
            super().run()

        self.exception = error.exception


@decorators.log
def of(fixture_classes: Iterable[type], context: Union[None, 'torment.TestContext'] = None) -> Iterable['torment.fixtures.Fixture']:
    '''Obtain all Fixture objects of the provided classes.

    **Parameters**

    :``fixture_classes``: classes inheriting from ``torment.fixtures.Fixture``
    :``context``:         a ``torment.TestContext`` to initialize Fixtures with

    **Return Value(s)**

    Instantiated ``torment.fixtures.Fixture`` objects for each individual
    fixture class that inherits from one of the provided classes.

    '''

    classes = list(copy.copy(fixture_classes))
    fixtures = []  # type: Iterable[torment.fixtures.Fixture]

    while len(classes):
        current = classes.pop()
        subclasses = current.__subclasses__()

        if len(subclasses):
            classes.extend(subclasses)
        elif current not in fixture_classes:
            fixtures.append(current(context))

    return fixtures


def register(namespace, base_classes: Tuple[type], properties: Dict[str, Any]) -> None:
    '''Register a Fixture class in namespace with the given properties.

    Creates a Fixture class (not object) and inserts it into the provided
    namespace.  The properties is a dict but allows functions to reference other
    properties and acts like a small DSL (domain specific language).  This is
    really just a declarative way to compose data about a test fixture and make
    it repeatable.

    Files calling this function are expected to house one or more Fixtures and
    have a name that ends with a UUID without its hyphens.  For example:
    foo_38de9ceec5694c96ace90c9ca37e5bcb.py.  This UUID is used to uniquely
    track the Fixture through the test suite and allow Fixtures to scale without
    concern.

    **Parameters**

    :``namespace``:    dictionary to insert the generated class into
    :``base_classes``: list of classes the new class should inherit
    :``properties``:   dictionary of properties with their values

    Properties can have the following forms:

    :functions: invoked with the Fixture as it's argument
    :classes:   instantiated without any arguments (unless it subclasses
                ``torment.fixtures.Fixture`` in which case it's passed context)
    :literals:  any standard python type (i.e. int, str, dict)

    .. note::
        function execution may error (this will be emitted as a logging event).
        functions will continually be tried until they resolve or the same set
        of functions is continually erroring.  These functions that failed to
        resolve are left in tact for later processing.

    Properties by the following names also have defined behavior:

    :description: added to the Fixture's description as an addendum
    :error:       must be a dictionary with three keys:
                  :class:  class to instantiate (usually an exception)
                  :args:   arguments to pass to class initialization
                  :kwargs: keyword arguments to pass to class initialization
    :mocks:       dictionary mapping mock symbols to corresponding values

    Properties by the following names are reserved and should not be used:

    * name

    '''

    # ensure we have a clean copy of the data
    # and won't stomp on re-uses elsewhere in
    # someone's code
    props = copy.deepcopy(properties)

    desc = props.pop('description', None)  # type: Union[str, None]

    caller_frame = inspect.stack()[1]

    caller_file = caller_frame[1]
    caller_module = inspect.getmodule(caller_frame[0])

    my_uuid = uuid.UUID(os.path.basename(caller_file).replace('.py', '').rsplit('_', 1)[-1])
    class_name = _unique_class_name(namespace, my_uuid)

    @property
    def description(self) -> str:
        _ = super(self.__class__, self).description

        if desc is not None:
            _ += '—' + desc

        return _

    def __init__(self, context: 'torment.TestContext') -> None:
        super(self.__class__, self).__init__(context)

        functions = {}

        for name, value in props.items():
            if name == 'error':
                self.error = value['class'](*value.get('args', ()), **value.get('kwargs', {}))
                continue

            if inspect.isclass(value):
                if issubclass(value, Fixture):
                    value = value(self.context)
                else:
                    value = value()

            if inspect.isfunction(value):
                functions[name] = value
                continue

            setattr(self, name, value)

        _resolve_functions(functions, self)

        self.initialize()

    def setup(self) -> None:
        if hasattr(self, 'mocks'):
            logger.debug('self.mocks: %s', self.mocks)

            for mock_symbol, mock_result in self.mocks.items():
                if _find_mocker(mock_symbol, self.context)():
                    _prepare_mock(self.context, mock_symbol, **mock_result)

        super(self.__class__, self).setup()

    namespace[class_name] = type(class_name, base_classes, {
        'description': description,
        '__init__': __init__,
        '__module__': caller_module,
        'setup': setup,
        'uuid': my_uuid,
    })


def _prepare_mock(context: 'torment.contexts.TestContext', symbol: str, return_value = None, side_effect = None) -> None:
    '''Sets return value or side effect of symbol's mock in context.

    .. seealso:: :py:func:`_find_mocker`

    **Parameters**

    :``context``:       the search context
    :``symbol``:        the symbol to be located
    :``return_value``:  pass through to mock ``return_value``
    :``side_effect``:   pass through to mock ``side_effect``

    '''

    methods = symbol.split('.')
    index = len(methods)

    mock = None

    while index > 0:
        name = 'mocked_' + '_'.join(methods[:index]).lower()
        logger.debug('name: %s', name)

        if hasattr(context, name):
            mock = getattr(context, name)
            break

        index -= 1

    logger.debug('mock: %s', mock)

    if mock is not None:
        mock = functools.reduce(getattr, methods[index:], mock)
        logger.debug('mock: %s', mock)

        if return_value is not None:
            mock.return_value = return_value

        if side_effect is not None:
            mock.side_effect = side_effect


def _find_mocker(symbol: str, context: 'torment.contexts.TestContext') -> Callable[[], bool]:
    '''Find method within the context that mocks symbol.

    Given a symbol (i.e. ``tornado.httpclient.AsyncHTTPClient.fetch``), find
    the shortest ``mock_`` method that resembles the symbol. Resembles means
    the lowercased and periods replaced with underscores.

    If no match is found, a dummy function (only returns False) is returned.

    **Parameters**

    :``symbol``:  the symbol to be located
    :``context``: the search context

    **Return Value(s)**

    The method used to mock the symbol.

    **Examples**

    Assuming the symbol is ``tornado.httpclient.AsyncHTTPClient.fetch``, the
    first of the following methods would be returned:

    * ``mock_tornado``
    * ``mock_tornado_httpclient``
    * ``mock_tornado_httpclient_asynchttpclient``
    * ``mock_tornado_httpclient_asynchttpclient_fetch``

    '''

    components = []
    method = None

    for component in symbol.split('.'):
        components.append(component.lower())
        name = '_'.join([ 'mock' ] + components)

        if hasattr(context, name):
            method = getattr(context, name)
            break

    if method is None:
        logger.warn('no mocker for %s', symbol)

        def noop(*args, **kwargs):
            return False

        method = noop

    return method


def _resolve_functions(functions: Dict[str, Callable[..., Any]], fixture: Fixture) -> None:
    '''Apply functions and collect values as properties on fixture.

    Call functions and apply their values as properteis on fixture.
    Functions will continue to get applied until no more functions resolve.
    All unresolved functions are logged and the last exception to have
    occurred is also logged.  This function does not return but adds the
    results to fixture directly.

    **Parameters**

    :``functions``: dict mapping function names (property names) to
                    callable functions
    :``fixture``:   Fixture to add values to

    '''

    function_names = dict(zip(functions.values(), functions.keys()))

    selfless, selfish = helpers.binary_partition(lambda item: len(item.__code__.co_varnames) and 'self' == item.__code__.co_varnames[0], function_names)
    logger.debug('selfless: %s', selfless)
    logger.debug('selfish: %s', selfish)

    for function in selfless:
        setattr(fixture, function_names[function], function)

    dependencies = { function_names[function]: _function_self_properties(function) for function in selfish }  # TODO add properties from fixture
    dependencies.update({ symbol: [] for symbol in dir(fixture) })
    logger.debug('dependencies: %s', dependencies)

    try:
        selfish = [ _ for _ in helpers.topological_sort(dependencies) if _ not in dir(fixture) ]
        logger.debug('selfish: %s', selfish)
    except RuntimeError as error:
        logger.debug('error.args: %s', error.args)

        raise AttributeError(fixture.name + ' object does not have attribute(s) ' + ','.join(error.args[1][0][1]) + ' for ' + error.args[1][0][0])

    for function in selfish:
        setattr(fixture, function, functions[function](fixture))


def _function_self_properties(function: Callable[..., Any]) -> Iterable[str]:
    '''Returns the references to self required by the function.

    This assumes that the passed function's first argument is self.  It finds
    all references to self's properties in the function.

    **Arguments**

    :``function``: the function to find self references

    **Return Value(s)**

    A list of self properties referenced in the function.

    '''

    properties = []

    seen_self = False

    for instruction in dis.get_instructions(function):
        if instruction.opname == 'LOAD_ATTR' and seen_self:
            properties.append(instruction.argval)

        if instruction.argval == 'self':
            seen_self = True
        else:
            seen_self = False

    return properties


def _unique_class_name(namespace: Dict[str, Any], uuid: uuid.UUID) -> str:
    '''Generate unique to namespace name for a class using uuid.

    **Parameters**

    :``namespace``: the namespace to verify uniqueness against
    :``uuid``:      the "unique" portion of the name

    **Return Value(s)**

    A unique string (in namespace) using uuid.

    '''

    count = 0

    name = original_name = 'f_' + uuid.hex
    while name in namespace:
        count += 1
        name = original_name + '_' + str(count)

    return name
