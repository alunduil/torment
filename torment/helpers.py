# Copyright 2015 Alex Brandt <alex.brandt@rackspace.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import importlib
import itertools
import logging
import os
import typing  # pylint: disable=W0611

from typing import Any
from typing import Dict
from typing import Iterable
from typing import Tuple

from torment import decorators

LOGGER = logging.getLogger(__name__)


def evert(iterable: Iterable[Dict[str, Tuple]]) -> Iterable[Iterable[Dict[str, Any]]]:
    '''Evert dictionaries with tuples.

    Iterates over the list of dictionaries and everts them with their tuple
    values.  For example:

    ``[ { 'a': ( 1, 2, ), }, ]``

    becomes

    ``[ ( { 'a': 1, }, ), ( { 'a', 2, }, ) ]``

    The resulting iterable contains the same number of tuples as the
    initial iterable had tuple elements.  The number of dictionaries is the same
    as the cartesian product of the initial iterable's tuple elements.

    Parameters
    ----------

    :``iterable``: list of dictionaries whose values are tuples

    Return Value(s)
    ---------------

    All combinations of the choices in the dictionaries.

    '''

    keys = list(itertools.chain.from_iterable([ _.keys() for _ in iterable ]))

    for values in itertools.product(*[ list(*_.values()) for _ in iterable ]):
        yield [ dict(( pair, )) for pair in zip(keys, values) ]


def extend(base: Dict[Any, Any], extension: Dict[Any, Any]) -> Dict[Any, Any]:
    '''Extend base by updating with the extension.

    **Arguments**

    :``base``:      dictionary to have keys updated or added
    :``extension``: dictionary to update base with

    **Return Value(s)**

    Resulting dictionary from updating base with extension.

    '''

    base = copy.deepcopy(base)

    base.update(extension)

    return base


def merge(base: Dict[Any, Any], extension: Dict[Any, Any]) -> Dict[Any, Any]:
    '''Merge extension into base recursively.

    **Argumetnts**

    :``base``:      dictionary to overlay values onto
    :``extension``: dictionary to overlay with

    **Return Value(s)**

    Resulting dictionary from overlaying extension on base.

    '''

    _ = copy.deepcopy(base)

    for key, value in extension.items():
        if isinstance(value, Dict) and key in _:
            _[key] = merge(_[key], value)
        else:
            _[key] = value

    return _


@decorators.log
def import_directory(module_basename: str, directory: str, sort_key = None) -> None:
    '''Load all python modules in directory and directory's children.

    Parameters
    ----------

    :``module_basename``: module name prefix for loaded modules
    :``directory``:       directory to load python modules from
    :``sort_key``:        function to sort module names with before loading

    '''

    LOGGER.info('loading submodules of %s', module_basename)
    LOGGER.info('loading modules from %s', directory)

    filenames = itertools.chain(*[ [ os.path.join(_[0], filename) for filename in _[2] ] for _ in os.walk(directory) if len(_[2]) ])
    modulenames = _filenames_to_modulenames(filenames, module_basename, directory)

    for modulename in sorted(modulenames, key = sort_key):
        try:
            importlib.import_module(modulename)
        except ImportError:
            LOGGER.warning('failed loading %s', modulename)
            LOGGER.exception('module loading failure')
        else:
            LOGGER.info('successfully loaded %s', modulename)


def powerset(iterable: Iterable[Any]) -> Iterable[Iterable[Any]]:
    '''Powerset of iterable.

    **Parameters**

    :``iterable``: set to generate powerset

    **Return Value(s)**

    Generator that produces all subsets of iterable.

    '''

    sequence = list(iterable)
    return itertools.chain.from_iterable(itertools.combinations(sequence, r) for r in range(len(sequence) + 1))


@decorators.log
def _filenames_to_modulenames(filenames: Iterable[str], modulename_prefix: str, filename_prefix: str = '') -> Iterable[str]:
    '''Convert given filenames to module names.

    Any filename that does not have a corresponding module name will be dropped
    from the result (i.e. __init__.py).

    Parameters
    ----------

    :``filename_prefix``:   a prefix to drop from all filenames (typically a
                            common directory); defaults to ''
    :``filenames``:         the filenames to transform into module names
    :``modulename_prefix``: a prefix to add to all module names

    Return Value(s)
    ---------------

    A list of modulenames corresponding to all filenames (for legal module names).

    '''

    modulenames = []  # type: Iterable[str]

    for filename in filenames:
        if not filename.endswith('.py'):
            continue

        name = filename

        name = name.replace(filename_prefix, '')
        name = name.replace('__init__.py', '')
        name = name.replace('.py', '')
        name = name.replace('/', '.')

        name = name.strip('.')

        if not len(name):
            continue

        if not modulename_prefix.endswith('.'):
            modulename_prefix += '.'

        name = modulename_prefix + name

        known_symbols = set()
        name = '.'.join([ _ for _ in name.split('.') if _ not in known_symbols and not known_symbols.add(_) ])

        if len(name):
            modulenames.append(name)

    return modulenames
