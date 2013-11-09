from pulp_auto.namespace import load_ns 


# a lump of custom profile data
# makes the fake-consumer a Fedora 19 system
PROFILE = load_ns({
    'reboot': {
        'scheduled': False,
        'details': {}
    },
    'details': {
        'rpm': {
            'details': [
                   {'vendor': 'Fedora Project', 'name': 'perl-Carp', 'epoch': 0, 'version': '1.26', 'release': '243.fc19', 'arch': 'noarch'},
                   {'vendor': 'Fedora Project', 'name': 'boost-program-options', 'epoch': 0, 'version': '1.53.0', 'release': '14.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'basesystem', 'epoch': 0, 'version': '10.0', 'release': '8.fc19', 'arch': 'noarch'},
                   {'vendor': 'Fedora Project', 'name': 'perl-PathTools', 'epoch': 0, 'version': '3.40', 'release': '3.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'libibverbs', 'epoch': 0, 'version': '1.1.7', 'release': '3.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'tzdata', 'epoch': 0, 'version': '2013c', 'release': '1.fc19', 'arch': 'noarch'},
                   {'vendor': 'Fedora Project', 'name': 'perl', 'epoch': 4L, 'version': '5.16.3', 'release': '265.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'python-simplejson', 'epoch': 0, 'version': '3.2.0', 'release': '1.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'libstdc++', 'epoch': 0, 'version': '4.8.1', 'release': '1.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'perl-Git', 'epoch': 0, 'version': '1.8.3.1', 'release': '1.fc19', 'arch': 'noarch'},
                   {'vendor': 'Fedora Project', 'name': 'xerces-c', 'epoch': 0, 'version': '3.1.1', 'release': '4.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'libattr', 'epoch': 0, 'version': '2.4.46', 'release': '10.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'gpm-libs', 'epoch': 0, 'version': '1.20.6', 'release': '33.fc19', 'arch': 'x86_64'},
                   {'vendor': None, 'name': 'm2crypto', 'epoch': 0, 'version': '0.21.1.pulp', 'release': '8.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'zlib', 'epoch': 0, 'version': '1.2.7', 'release': '10.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'qpid-cpp-client', 'epoch': 0, 'version': '0.24', 'release': '3.fc19.1', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'python-rhsm', 'epoch': 0, 'version': '1.10.1', 'release': '1.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'chkconfig', 'epoch': 0, 'version': '1.3.60', 'release': '3.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'python-qpid', 'epoch': 0, 'version': '0.24', 'release': '1.fc19', 'arch': 'noarch'},
                   {'vendor': 'Fedora Project', 'name': 'python-oauth2', 'epoch': 0, 'version': '1.5.211', 'release': '4.fc19', 'arch': 'noarch'},
                   {'vendor': 'Fedora Project', 'name': 'libdb', 'epoch': 0, 'version': '5.3.21', 'release': '11.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'qpid-cpp-server', 'epoch': 0, 'version': '0.24', 'release': '3.fc19.1', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'boost-timer', 'epoch': 0, 'version': '1.53.0', 'release': '14.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'libgpg-error', 'epoch': 0, 'version': '1.11', 'release': '1.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'libxml2-python', 'epoch': 0, 'version': '2.9.1', 'release': '1.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'readline', 'epoch': 0, 'version': '6.2', 'release': '6.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'boost-iostreams', 'epoch': 0, 'version': '1.53.0', 'release': '14.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'lua', 'epoch': 0, 'version': '5.1.4', 'release': '12.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'boost-test', 'epoch': 0, 'version': '1.53.0', 'release': '14.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'libffi', 'epoch': 0, 'version': '3.0.13', 'release': '4.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'boost-context', 'epoch': 0, 'version': '1.53.0', 'release': '14.fc19', 'arch': 'x86_64'},
                   {'vendor': 'Fedora Project', 'name': 'tcp_wrappers-libs', 'epoch': 0, 'version': '7.6', 'release': '73.fc19', 'arch': 'x86_64'},
            ],
            'succeeded': True
        }
    }, 
    'succeeded': True,
    'num_changes': 0
})


