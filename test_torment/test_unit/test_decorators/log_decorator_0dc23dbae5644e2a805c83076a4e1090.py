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

from torment import fixtures

from test_torment.test_unit.test_decorators import LogDecoratorFixture

from torment import decorators


class Foo(object):  # pylint: disable=R0903
    @decorators.log
    def success(self):
        pass

fixtures.register(globals(), ( LogDecoratorFixture, ), {
    'function': Foo().success,

    'expected': [
        'INFO:torment.decorators:STARTING: Foo.success()',
        'INFO:torment.decorators:STOPPING: Foo.success()',
    ],
})
