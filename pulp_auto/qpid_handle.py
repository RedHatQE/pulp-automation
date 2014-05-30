import contextlib, json, namespace
from qpid.messaging import Connection
from qpid.messaging import Message
from base64 import b64encode, b64decode
from qpid.messaging.exceptions import (Timeout, Empty)
from authenticator import (Authenticator, AuthenticationError)

class QpidHandle(object):
    '''qpid handle'''

    def __init__(self, url, receiver_name, sender_name='pulp.task', asserting=False, auth=Authenticator(), **options):
        '''establishes a connection to given url; initializes session, sender and receiver'''
        self.url = url
        self.receiver_name = receiver_name
        self.sender_name = sender_name
        self._asserting = asserting
        self.last_sent = None
        self.last_fetched = None
        self.session = Connection.establish(self.url, **options).session()
        self.receiver = self.session.receiver("pulp.agent.%s; {create: always}" % self.receiver_name)
        self.sender = self.session.sender(self.sender_name)
        self._timeout = None
        self.auth = auth

    def send(self, message):
        '''shortcut for self.sender.send(Message(content=json.dumps(message))'''
        self.last_sent = Message(content=json.dumps(message))
        ret = self.sender.send(self.last_sent)
        if self._asserting:
            assert self.is_ok, 'QpidHandle was not OK:\n%s' % self
        return ret

    def fetch(self):
        '''shortcut for namespace.load_ns(json.loads(self.receiver.fetch().content))'''
        ret = self.receiver.fetch(timeout=self._timeout)
        self.session.acknowledge()
        self.last_fetched = ret
        if self._asserting:
            assert self.is_ok, 'Qpid session was not OK:\n%s' % self
        return namespace.load_ns(json.loads(ret.content))

    def close(self):
        '''shortcut for self.session.close()'''
        return self.session.close()

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
        '''shortcut for self.fetch() with some check-sums handling'''
        content = self.fetch()
        assert 'signature' in content, 'no signature in message: %s' % content
        try:
            signature = b64decode(content.signature)
        except TypeError as e:
            # rethrow as assertion failure
            raise AssertionError(e)
        self.auth.verify(content.message, signature)
        # The second load of message is required because
        # if the message was transported as a dict
        # the checksum/signature might change upon the message
        # deserialization (un-ordered-dict)??
        return namespace.load_ns(json.loads(content.message))

    @message.setter
    def message(self, other):
        '''shortcut for self.send()'''
        # need to keep ordering so that everyone computes correct sha256 digest;
        # sorting based on key names
        content = {
            'message':  json.dumps(namespace.dump_ns_sorted(other)),
            'signature': b64encode(self.auth.sign(other) or '') # empty string in case no signature
        }
        self.send(content)

    @contextlib.contextmanager
    def asserting(self, value=True):
        '''turn on/off asserting based on self.is_ok'''
        old_value = self._asserting
        self._asserting = value
        try:
            yield
        finally:
            self._asserting = old_value

    @contextlib.contextmanager
    def timeout(self, value=None):
        '''enter a timeout context where fetch/self.message raise Timeouts'''
        old_value = self._timeout
        self._timeout = value
        try:
            yield self
        finally:
            self._timeout = old_value
