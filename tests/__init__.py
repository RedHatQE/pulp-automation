from pulp_auto import namespace
import yaml
global ROLES

# load inventory globals
with open('inventory.yml') as fd:
    globals().update(namespace.load_ns(yaml.load(fd)))
