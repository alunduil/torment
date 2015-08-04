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
import inspect
import logging
import typing  # pylint: disable=W0611
import unittest
import uuid

from torment import fixtures
from torment import contexts

LOGGER = logging.getLogger(__name__)


class FixturesCreateUnitTest(unittest.TestCase):  # pylint: disable=C0111
    def test_fixture_create_without_context(self) -> None:
        '''torment.fixtures.Fixture() → TypeError'''

        self.assertRaises(TypeError, fixtures.Fixture)

    def test_fixture_create_with_context(self) -> None:
        '''torment.fixtures.Fixture(context).context == context'''

        c = unittest.TestCase()  # pylint: disable=C0103
        f = fixtures.Fixture(c)  # pylint: disable=C0103

        self.assertEqual(f.context, c)


class FixturesPropertyUnitTest(unittest.TestCase):  # pylint: disable=C0111
    def setUp(self) -> None:
        self.c = unittest.TestCase()  # pylint: disable=C0103
        self.f = fixtures.Fixture(self.c)  # pylint: disable=C0103

    def test_fixture_category(self) -> None:
        '''torment.fixtures.Fixture(context).category == 'fixtures' '''

        self.f.__module__ = unittest.mock.MagicMock(__name__ = 'test_torment.test_unit.test_fixtures.fixture_a44bc6dda6654b1395a8c2cbd55d964d')

        self.assertEqual(self.f.category, 'fixtures')

    def test_fixture_description(self) -> None:
        '''torment.fixtures.Fixture(context).description == '94d7c58f6ee44683936c21cb84d1e458—torment.fixtures' '''

        self.f.context.module = 'fixtures'
        self.f.uuid = uuid.UUID('94d7c58f6ee44683936c21cb84d1e458')

        self.assertEqual(self.f.description, '94d7c58f6ee44683936c21cb84d1e458—fixtures')

    def test_fixture_name(self) -> None:
        '''torment.fixtures.Fixture(context).name == 'test_94d7c58f6ee44683936c21cb84d1e458' '''

        self.f.__class__.__name__ = '94d7c58f6ee44683936c21cb84d1e458'

        self.assertEqual(self.f.name, 'test_94d7c58f6ee44683936c21cb84d1e458')


class ErrorFixturesPropertyUnitTest(unittest.TestCase):
    def test_error_fixture_description(self) -> None:
        '''torment.fixtures.ErrorFixture(context).description == 'expected → failure' '''

        class Fixture(fixtures.Fixture):  # pylint: disable=C0111
            @property
            def description(self) -> str:  # pylint: disable=C0111
                return 'expected'

        class ErrorFixture(fixtures.ErrorFixture, Fixture):  # pylint: disable=C0111
            def __init__(self, *args, **kwargs) -> None:  # pylint: disable=C0111
                super().__init__(*args, **kwargs)
                self.error = RuntimeError('failure')

        c = unittest.TestCase()  # pylint: disable=C0103

        e = ErrorFixture(c)  # pylint: disable=C0103

        self.assertEqual(e.description, 'expected → failure')


class ErrorFixturesRunTest(unittest.TestCase):
    def test_error_fixture_run(self) -> None:
        '''torment.fixtures.ErrorFixture(context).run()'''

        class Fixture(fixtures.Fixture):  # pylint: disable=C0111
            def run(self):  # pylint: disable=C0111,R0201
                raise RuntimeError('failure')

        class ErrorFixture(fixtures.ErrorFixture, Fixture):  # pylint: disable=C0111
            def __init__(self, *args, **kwargs) -> None:  # pylint: disable=C0111
                super().__init__(*args, **kwargs)
                self.error = RuntimeError('failure')

        c = unittest.TestCase()  # pylint: disable=C0103

        e = ErrorFixture(c)  # pylint: disable=C0103
        e.run()

        self.assertIsInstance(e.exception, RuntimeError)
        self.assertEqual(e.exception.args, ( 'failure', ))


class OfUnitTest(unittest.TestCase):  # pylint: disable=C0111
    def test_of_zero(self) -> None:
        '''torment.fixtures.of(()) == []'''

        self.assertEqual(len(fixtures.of(())), 0)

    def test_of_many_without_subclasses(self) -> None:
        '''torment.fixtures.of(( FixtureA, )) == []'''

        class FixtureA(object):  # pylint: disable=C0111,R0903
            def __init__(self, context) -> None:  # pylint: disable=C0111
                pass

        self.assertEqual(len(fixtures.of(( FixtureA, ))), 0)

    def test_of_many_with_subclasses(self) -> None:
        '''torment.fixtures.of(( FixtureA, )) == [ fixture_a, ]'''

        class FixtureA(object):  # pylint: disable=C0111,R0903
            def __init__(self, context) -> None:  # pylint: disable=C0111
                pass

        class FixtureB(FixtureA):  # pylint: disable=C0111,R0903
            pass

        result = fixtures.of(( FixtureA, ))

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], FixtureB)


class RegisterUnitTest(unittest.TestCase):  # pylint: disable=C0111
    def setUp(self) -> None:
        _ = unittest.mock.patch('torment.fixtures.inspect')
        mocked_inspect = _.start()
        self.addCleanup(_.stop)

        mocked_inspect.configure_mock(**{ 'isclass': inspect.isclass, 'isfunction': inspect.isfunction, })

        mocked_inspect.stack.return_value = ( None, ( None, 'test_unit/test_d43830e2e9624dd19c438b15250c5818.py', ), )  # pylint: disable=E1101

        class ContextStub(object):  # pylint: disable=C0111,R0903
            pass

        self.context = ContextStub()
        self.context.module = mocked_inspect.getmodule.return_value = 'stack'  # pylint: disable=E1101

        self.ns = {}  # type: Dict[str, Any]  pylint: disable=C0103
        self.class_name = 'f_d43830e2e9624dd19c438b15250c5818'

    def test_zero_properties(self) -> None:
        '''torment.fixtures.register({}, (), {})'''

        fixtures.register(self.ns, ( fixtures.Fixture, ), {})

        _ = self.ns[self.class_name](self.context)

        self.assertEqual(_.uuid, uuid.UUID('d43830e2e9624dd19c438b15250c5818'))

    def test_one_literal_properties(self) -> None:
        '''torment.fixtures.register({}, (), { 'a': 'a', })'''

        fixtures.register(self.ns, ( fixtures.Fixture, ), { 'a': 'a', })

        _ = self.ns[self.class_name](self.context)

        self.assertEqual(_.a, 'a')

    def test_one_class_properties(self) -> None:
        '''torment.fixtures.register({}, (), { 'a': class, })'''

        class A(object):  # pylint: disable=C0103,C0111,R0903
            pass

        fixtures.register(self.ns, ( fixtures.Fixture, ), { 'a': A, })

        _ = self.ns[self.class_name](self.context)

        self.assertIsInstance(_.a, A)

    def test_one_fixture_class_properties(self) -> None:
        '''torment.fixtures.register({}, (), { 'a': fixture_class, })'''

        class A(fixtures.Fixture):  # pylint: disable=C0103,C0111,R0903
            pass

        fixtures.register(self.ns, ( fixtures.Fixture, ), { 'a': A, })

        _ = self.ns[self.class_name](self.context)

        self.assertIsInstance(_.a, A)
        self.assertEqual(_.a.context, self.context)

    def test_one_function_properties(self) -> None:
        '''torment.fixtures.register({}, (), { 'a': self → None, })'''

        def a(self) -> None:  # pylint: disable=C0103,C0111,R0903,W0613
            pass

        fixtures.register(self.ns, ( fixtures.Fixture, ), { 'a': a, })

        _ = self.ns[self.class_name](self.context)

        self.assertIsNone(_.a)

    def test_description_property(self) -> None:
        '''torment.fixtures.register({}, (), { 'description': 'needle', })'''

        fixtures.register(self.ns, ( fixtures.Fixture, ), { 'description': 'needle', })

        _ = self.ns[self.class_name](self.context)

        self.assertEqual(_.description, 'd43830e2e9624dd19c438b15250c5818—stack—needle')

    def test_error_property(self) -> None:
        '''torment.fixtures.register({}, (), { 'error': …, })'''

        fixtures.register(self.ns, ( fixtures.Fixture, ), { 'error': { 'class': RuntimeError, }, })

        _ = self.ns[self.class_name](self.context)

        self.assertIsInstance(_.error, RuntimeError)

    def test_mocks_mock_property(self) -> None:
        '''torment.fixtures.register({}, (), { 'mocks': { 'symbol': …, }, }).setup()'''

        _ = unittest.mock.patch('torment.fixtures._find_mocker')
        mocked_fixtures_find_mocker = _.start()
        self.addCleanup(_.stop)
        mocked_fixtures_find_mocker.return_value = lambda: True

        _ = unittest.mock.patch('torment.fixtures._prepare_mock')
        mocked_fixtures_prepare_mock = _.start()
        self.addCleanup(_.stop)

        fixtures.register(self.ns, ( fixtures.Fixture, ), { 'mocks': { 'symbol': {}, }, })

        _ = self.ns[self.class_name](self.context)
        _.setup()

        mocked_fixtures_find_mocker.assert_called_once_with('symbol', self.context)
        mocked_fixtures_prepare_mock.assert_called_once_with(self.context, 'symbol')


class PrepareMockUnitTest(unittest.TestCase):
    def setUp(self) -> None:
        class ContextStub(contexts.TestContext):  # pylint: disable=C0111
            mocked_symbol = unittest.mock.MagicMock(name = 'ContextStub.mocked_symbol')

        self.context = ContextStub()

    def test_prepare_mock_side_effect_zero_dots(self) -> None:
        '''tormnet.fixtures._prepare_mock(ContextStub, 'symbol', side_effect = range(2))'''

        fixtures._prepare_mock(self.context, 'symbol', side_effect = range(2))  # pylint: disable=W0212
        self.assertEqual(self.context.mocked_symbol(), 0)
        self.assertEqual(self.context.mocked_symbol(), 1)
        self.assertRaises(StopIteration, self.context.mocked_symbol)

    def test_prepare_mock_return_value_zero_dots(self) -> None:
        '''tormnet.fixtures._prepare_mock(ContextStub, 'symbol', return_value = 'a')'''

        fixtures._prepare_mock(self.context, 'symbol', return_value = 'a')  # pylint: disable=W0212
        self.assertEqual(self.context.mocked_symbol(), 'a')

    def test_prepare_mock_return_value_one_dots(self) -> None:
        '''tormnet.fixtures._prepare_mock(ContextStub, 'symbol.Sub', return_value = 'a')'''

        fixtures._prepare_mock(self.context, 'symbol.Sub', return_value = 'a')  # pylint: disable=W0212
        self.assertEqual(self.context.mocked_symbol.Sub(), 'a')

    def test_prepare_mock_return_value_many_dots(self) -> None:
        '''tormnet.fixtures._prepare_mock(ContextStub, 'symbol.sub.a.b.c', return_value = 'a')'''

        fixtures._prepare_mock(self.context, 'symbol.sub.a.b.c', return_value = 'a')  # pylint: disable=W0212
        self.assertEqual(self.context.mocked_symbol.sub.a.b.c(), 'a')

    def test_prepare_mock_return_value_many_dots_second_level(self) -> None:  # pylint: disable=C0103
        '''tormnet.fixtures._prepare_mock(ContextStub, 'symbol.sub.a.b.c', return_value = 'a')'''

        class ContextStub(contexts.TestContext):  # pylint: disable=C0111
            mocked_symbol_sub = unittest.mock.MagicMock(name = 'ContextStub.mocked_symbol_sub')

        c = ContextStub()  # pylint: disable=C0103

        fixtures._prepare_mock(c, 'symbol.sub.a.b.c', return_value = 'a')  # pylint: disable=W0212

        self.assertEqual(c.mocked_symbol_sub.a.b.c(), 'a')

    def test_prepare_mock_return_value_many_dots_all_levels(self) -> None:  # pylint: disable=C0103
        '''tormnet.fixtures._prepare_mock(ContextStub, 'symbol.Sub.a.b.c', return_value = 'a')'''

        class ContextStub(contexts.TestContext):  # pylint: disable=C0111
            mocked_symbol_sub_a_b_c = unittest.mock.MagicMock(name = 'ContextStub.mocked_symbol_sub_a_b_c')

        c = ContextStub()  # pylint: disable=C0103

        fixtures._prepare_mock(c, 'symbol.Sub.a.b.c', return_value = 'a')  # pylint: disable=W0212

        self.assertEqual(c.mocked_symbol_sub_a_b_c(), 'a')


class FindMockerUnitTest(unittest.TestCase):
    def test_find_mocker_found_zero_levels(self) -> None:
        '''tormnet.fixtures._find_mocker('symbol', ContextStub) == mock_symbol'''

        class ContextStub(contexts.TestContext):  # pylint: disable=C0111
            def mock_symbol(self):  # pylint: disable=C0111
                pass

        c = ContextStub()  # pylint: disable=C0103

        method = fixtures._find_mocker('symbol', c)  # pylint: disable=W0212
        self.assertEqual(method, c.mock_symbol)

    def test_find_mocker_found_second_level(self) -> None:
        '''tormnet.fixtures._find_mocker('symbol.Sub', ContextStub) == mock_symbol_Sub'''

        class ContextStub(contexts.TestContext):  # pylint: disable=C0111
            def mock_symbol_sub(self):  # pylint: disable=C0111
                pass

        c = ContextStub()  # pylint: disable=C0103

        method = fixtures._find_mocker('symbol.Sub', c)  # pylint: disable=W0212
        self.assertEqual(method, c.mock_symbol_sub)

    def test_find_mocker_found_many_levels(self) -> None:
        '''tormnet.fixtures._find_mocker('symbol.sub.a.b', ContextStub) == mock_symbol_sub_a_b'''

        class ContextStub(contexts.TestContext):  # pylint: disable=C0111
            def mock_symbol_sub_a_b(self):  # pylint: disable=C0111
                pass

        c = ContextStub()  # pylint: disable=C0103

        method = fixtures._find_mocker('symbol.sub.a.b', c)  # pylint: disable=W0212
        self.assertEqual(method, c.mock_symbol_sub_a_b)

    def test_find_mocker_not_found(self) -> None:
        '''tormnet.fixtures._find_mocker('fakesymbol', ContextStub) == lambda: False'''

        class ContextStub(contexts.TestContext):  # pylint: disable=C0111
            pass

        c = ContextStub()  # pylint: disable=C0103

        method = fixtures._find_mocker('fakesymbol', c)  # pylint: disable=W0212
        self.assertFalse(method())
        self.assertEqual(method.__name__, 'noop')


class ResolveFunctionsUnitTest(unittest.TestCase):  # pylint: disable=C0111
    def setUp(self) -> None:
        class StubFixture(object):  # pylint: disable=C0103,C0111,R0903
            pass

        self.f = StubFixture()  # pylint: disable=C0103
        self.f.name = 'testing_fixture_stub'

        self.o = copy.deepcopy(self.f)  # pylint: disable=C0103

    def test_zero_functions(self) -> None:
        '''torment.fixtures._resolve_functions({}, fixture)'''

        fixtures._resolve_functions({}, self.f)  # pylint: disable=W0212

        self.assertEqual(dir(self.o), dir(self.f))

    def test_one_functions_without_parameters(self) -> None:
        '''torment.fixtures._resolve_functions({ 'a': ø → None, }, fixture)'''

        def a() -> None:  # pylint: disable=C0103,C0111
            pass

        fixtures._resolve_functions({ 'a': a, }, self.f)  # pylint: disable=W0212

        self.assertEqual(id(self.f.a), id(a))  # pylint: disable=E1101

    def test_one_functions_with_self_parameter(self) -> None:
        '''torment.fixtures._resolve_functions({ 'a': self → None, }, fixture)'''

        def a(self) -> None:  # pylint: disable=C0103,C0111,W0613
            pass

        fixtures._resolve_functions({ 'a': a, }, self.f)  # pylint: disable=W0212

        self.assertIsNone(self.f.a)  # pylint: disable=E1101

    def test_one_functions_with_self_parameter_raises_attributeerror(self) -> None:  # pylint: disable=C0103
        '''torment.fixtures._resolve_functions({ 'a': self → self.b, }, fixture)'''

        def a(self):  # pylint: disable=C0103,C0111
            return self.b

        fixtures._resolve_functions({ 'a': a, }, self.f)  # pylint: disable=W0212

        self.assertEqual(id(self.f.a), id(a))  # pylint: disable=E1101

    def test_many_functions(self) -> None:
        '''torment.fixtures._resolve_functions({ 'a': self → self.b, 'b': self → None, }, fixture)'''

        def a(self) -> None:  # pylint: disable=C0103,C0111
            return self.b

        def b(self) -> None:  # pylint: disable=C0103,C0111,W0613
            pass

        fixtures._resolve_functions({ 'a': a, 'b': b, }, self.f)  # pylint: disable=W0212

        self.assertIsNone(self.f.a)  # pylint: disable=E1101
        self.assertIsNone(self.f.b)  # pylint: disable=E1101


class UniqueClassNameUnitTest(unittest.TestCase):  # pylint: disable=C0111
    def setUp(self) -> None:
        self.uuid = uuid.uuid4()

    def test_empty_namespace(self) -> None:
        '''torment.fixtures._unique_class_name({}, uuid) == 'f_{uuid}' '''

        n = fixtures._unique_class_name({}, self.uuid)  # pylint: disable=C0103,W0212

        self.assertEqual(n, 'f_' + self.uuid.hex)

    def test_one_namespace(self) -> None:
        '''torment.fixtures._unique_class_name({ 'f_{uuid}': None, }, uuid) == 'f_{uuid}_1' '''

        n = fixtures._unique_class_name({ 'f_' + self.uuid.hex: None, }, self.uuid)  # pylint: disable=C0103,W0212

        self.assertEqual(n, 'f_' + self.uuid.hex + '_1')

    def test_two_namespace(self) -> None:
        '''torment.fixtures._unique_class_name({ 'f_{uuid}': None, 'f_{uuid}_1': None, }, uuid) == 'f_{uuid}_2' '''

        n = fixtures._unique_class_name({ 'f_' + self.uuid.hex: None, 'f_' + self.uuid.hex + '_1': None, }, self.uuid)  # pylint: disable=C0103,W0212

        self.assertEqual(n, 'f_' + self.uuid.hex + '_2')
