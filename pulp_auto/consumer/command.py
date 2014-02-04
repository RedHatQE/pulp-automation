class Command(object):
    '''represents a command to be executed in the plumbum fashion'''
    def __init__(self, command, *args, **kvs):
        '''create the command representation convert attr_name=attr_value to --attr-name=attr_value
        cli string args tuple
        '''
        self.command = command
        # merge args and kvs together to form a huge tuple
        # that plumbum understands
        self.args = reduce(
            lambda the_tuple, key_value_pair: the_tuple + key_value_pair,
            [ \
                (Command.key_to_argname(key), Command.value_to_argvalue(value)) \
                for key, value in kvs.items() if value is not None \
            ],
            tuple(args)
        )

    @staticmethod
    def key_to_argname(key):
        return '--' + str(key).replace('_', '-')

    @staticmethod
    def value_to_argvalue(value):
        return str(value)

    @staticmethod
    def kvs_to_args(**kvs):
        return 

    def __call__(self, remote):
        '''create plumbum-fashion command over remote'''
        return remote[self.command][self.args]

    def __str__(self):
        return str(self.args)

