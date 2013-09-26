#!/usr/bin/env python

class Namespace(dict):
    '''an attribure-access dictionary'''
    def __init__(self, *args, **kvargs):
        super(dict, self).__init__(*args, **kvargs)
        # a little magic
        self.__dict__ = self

    def copy(self):
        '''return a namespace made out of self'''
        return load_ns(super(Namespace, self).copy())

def load_ns(d, leaf_processor=lambda x: x):
    '''a recursive dict-to-Namespace loader'''
    if not isinstance(d, dict):
        return leaf_processor(d)
    ns = Namespace()
    for k, v in d.items():
        ns[k] = load_ns(v, leaf_processor)
    return ns

def locate_ns_item(ns, item):
    '''
    locate queries of the form 'a.b.c' in a Namespace instance
    tries to find longest match
    '''
    if item == '':
        # item found
        return ns

    sub_items = item.split('.')
    for list_prefix in [ sub_items[:i] for i in range(len(sub_items), 0, -1)]:
        item_prefix = '.'.join(list_prefix)
        item_suffix = '.'.join(sub_items[i:])
        print item, item_prefix, item_suffix
        if item_prefix in ns:
            return ns_locate(ns[item_prefix], item_suffix)

    # no match
    raise KeyError('item not found: %s' % item)

def setattr_ns(obj, ns, leaf_processor=lambda x: x):
    '''kinda recursive setattr from a namespace to an arbitrary object'''

    if not isinstance(ns, dict):
        obj = leaf_processor(ns)

    for k, v in ns.items():
        try:
            setattr_ns(getattr(obj, k), v, leaf_processor=leaf_processor)
        except AttributeError:
            setattr(obj, k, leaf_processor(v))

