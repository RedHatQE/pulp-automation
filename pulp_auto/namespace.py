#!/usr/bin/env python
from collections import OrderedDict

def key_parts(key):
    '''
    return list of all prefix/suffix pairs; if key == 'a.b.c':
    [
       ('a.b.c', ''),
       ('a.b', 'c'),
       ('a', 'b.c')
    ]
    '''
    sub_items = key.split('.')
    return [
        ('.'.join(list_prefix), '.'.join(sub_items[i:])) \
        for list_prefix in [sub_items[:i] for i in range(len(sub_items), 0, -1)]
    ]

class Namespace(dict):
    '''an attribure-access dictionary'''
    def __init__(self, *args, **kvargs):
        super(dict, self).__init__(*args, **kvargs)
        # a little magic
        self.__dict__ = self

    def copy(self):
        '''return a namespace made out of self'''
        return load_ns(super(Namespace, self).copy())

    def __getitem__(self, key):
        def locate(ns, key):
            if not type(key) in (unicode, str):
                # no point in splitting; try directly
                return  dict.__getitem__(ns, key)

            if key == '':
                # item found
                return ns

            if type(ns) not in (Namespace, dict):
                # item not found
                raise KeyError(repr(key))

            for item_prefix, item_suffix in key_parts(key):
                if item_prefix in ns.keys():
                    return locate(dict.__getitem__(ns, item_prefix), item_suffix, )

            # item not found
            raise KeyError(repr(key))
        return locate(self.__dict__, key)

    def __contains__(self, key):
        try:
            self[key]
            return True
        except KeyError:
            return False




def load_ns(d, leaf_processor=lambda x: x):
    '''a recursive dict-to-Namespace loader'''
    if not isinstance(d, dict):
        if isinstance(d, list):
            return [load_ns(item) for item in d]
        if isinstance(d, tuple):
            return tuple([load_ns(item) for item in d])
        return leaf_processor(d)
    ns = Namespace()
    for k, v in d.items():
        ns[k] = load_ns(v, leaf_processor)
    return ns


def dump_ns(ns, leaf_processor=lambda x: x):
    '''a recursive namespace-to-dict dumper'''
    if isinstance(ns, tuple):
        return tuple([dump_ns(item) for item in ns])
    if isinstance(ns, list):
        return [dump_ns(item) for item in ns]
    if isinstance(ns, dict) or isinstance(ns, Namespace):
        return {k: dump_ns(v) for k, v in ns.items()}

    return leaf_processor(ns)

def dump_ns_sorted(ns, leaf_processor=lambda x: x):
    '''a recursive namespace-to-dict dumper with in-place sorting'''
    if isinstance(ns, tuple):
        return tuple([dump_ns_sorted(item) for item in sorted(ns)])
    if isinstance(ns, list):
        return [dump_ns_sorted(item) for item in sorted(ns)]
    if isinstance(ns, dict) or isinstance(ns, Namespace):
        return OrderedDict([(k, dump_ns_sorted(v)) for k, v in sorted(ns.items(), key=lambda pair: pair[0])])

    return leaf_processor(ns)


def locate_ns_item(ns, item, building=False):
    '''
    locate queries of the form 'a.b.c' in a Namespace instance
    tries to find longest match
    '''
    if type(item) not in (unicode, str):
        # no point in splitting; try directly
        return  ns[item]

    if item == '':
        # item found
        return ns

    if type(ns) not in (Namespace, dict):
        # item not found
        raise KeyError(repr(item))

    for item_prefix, item_suffix in key_parts(item):
        if item_prefix in ns.keys():
            if building:
                return {item_prefix: locate_ns_item(ns[item_prefix], item_suffix, building=building)}
            else:
                return locate_ns_item(ns[item_prefix], item_suffix, building=building)

    # item not found
    raise KeyError(repr(item))


def in_ns(ns, item):
    try:
        locate_ns_item(ns, item)
        return True
    except KeyError:
        return False

def setattr_ns(obj, ns, leaf_processor=lambda x: x):
    '''kinda recursive setattr from a namespace to an arbitrary object'''

    if not isinstance(ns, dict):
        obj = leaf_processor(ns)

    for k, v in ns.items():
        try:
            setattr_ns(getattr(obj, k), v, leaf_processor=leaf_processor)
        except AttributeError:
            setattr(obj, k, leaf_processor(v))
