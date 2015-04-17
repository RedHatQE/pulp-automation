#!/usr/bin/env python
"""replace pulp hostname, pulp url and qpid url with env['PULPHOST'], if provided"""


import os
import sys
import yaml

DEFAULT_INVENTORY='inventory.yml'

pulphost = os.environ.get('PULPHOST')
if not pulphost:
    # nothing to do
    exit(0)


if len(sys.argv) > 1:
    # first opt overrides DEFAULT_INVENTORY
    inventory = sys.argv[1]
else:
    inventory = DEFAULT_INVENTORY

with open(inventory) as f:
    data = yaml.load(f)

# mandatory fields:
try:
    data['ROLES']['pulp']['url'] = 'https://%s/' % pulphost
    data['ROLES']['qpid']['url'] = pulphost
except KeyError as err:
    print >>sys.stderr, err
    exit(1)

# optional fields:
try:
    data['ROLES']['pulp']['hostname'] = pulphost
except KeyError as err:
    print err

with open(inventory, 'w') as f:
    f.write(yaml.dump(data))
