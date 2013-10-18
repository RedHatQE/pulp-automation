import contextlib, json, namespace

class QpidHandle(object):
    '''qpid handle'''

    def __init__(self, url, receiver_name, sender_name='pulp.task', asserting=False, **options):
        '''establishes a connection to given url; initializes session, sender and receiver'''
        self.url = url
        self.receiver_name = receiver_name
        self.sender_name = sender_name
        self._asserting = asserting
        self.last_sent = None
        self.last_fetched = None
        from qpid.messaging import Connection
        self.session = Connection.establish(self.url, **options).session()
        self.receiver = self.session.receiver(self.receiver_name)
        self.sender = self.session.sender(self.sender_name)

    def send(self, message):
        '''shortcut for self.sender.send(Message(content=json.dumps(message))'''
        from qpid.messaging import Message
        self.last_sent = Message(content=json.dumps(message))
        ret = self.sender.send(self.last_sent)
        if self._asserting:
            assert self.is_ok, 'QpidHandle was not OK:\n%s' % self
        return ret

    def fetch(self):
        '''shortcut for namespace.load_ns(json.loads(self.receiver.fetch().content))'''
        ret = self.receiver.fetch()
        self.last_fetched = ret
        if self._asserting:
            assert self.is_ok, 'Qpid session was not OK:\n%s' % self
        return namespace.load_ns(json.loads(ret.content))

    def __repr__(self):
        return type(self).__name__ + \
            '(%(url)s, %(receiver_name)s, sender_name=%(sender_name)s, asserting=%(_asserting)s)' % self.__dict__

    def __str__(self):
        '''display internal state'''
        return '>u: %(url)s\n>r: %(receiver_name)s\n>s: %(sender_name)s\n>>\n%(last_sent)s\n<<\n%(last_fetched)s\n' % self.__dict__

    @property
    def is_ok(self):
        '''when OK, there are no errors in self.session'''
        return self.session.error is None
    
    @property
    def error(self):
        '''shortcut to self.session.error'''
        return self.session.error

    @property
    def message(self):
        '''shortcut for self.fetch()'''
        return self.fetch()

    @contextlib.contextmanager
    def asserting(self, value=True):
        '''turn on/off asserting based on self.is_ok'''
        old_value = self._asserting
        self._asserting = value
        try:
            yield
        finally:
            self._asserting = old_value
        
