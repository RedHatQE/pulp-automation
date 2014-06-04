#!/usr/bin/python
from pulp_auto.qpid_handle import QpidHandle
from pulp_auto.agent import Agent
from pulp_auto.handler.profile import PROFILE
from pulp_auto.consumer import Consumer
from pulp_auto.pulp import Pulp
from pulp_auto.authenticator import Authenticator
import logging, sys, pulp_auto, time
import aaargh
import urllib3
from M2Crypto import (RSA, BIO)


logging.basicConfig(level=logging.INFO) #level=logging.DEBUG)
log = logging.getLogger(__file__)

app = aaargh.App(description='Fake pulp consumer')


@app.cmd(help='run the consumer')
@app.cmd_arg('-u', '--url', help='URL of the AMQP broker to use', default='localhost')
@app.cmd_arg('-n', '--consumer-name', help='consumer name to use', default='fake_consumer')
@app.cmd_arg('-r', '--reporting', help='propagate errors back', default=False, action='store_true')
@app.cmd_arg('-f', '--polling-frequency', help='polling frequency', type=float, default=3.0)
@app.cmd_arg('-k', '--key-file', help='path to a key fille', default="")
@app.cmd_arg('-p', '--pulp-url', help='pulp url to use', default="")
def run(url, consumer_name, reporting, polling_frequency, key_file, pulp_url):
    from gevent import monkey
    monkey.patch_all(select=False, thread=False)

    if not pulp_url:
        # use http://admin:admin@<host part from amqp url>/"
        amqp_url = urllib3.util.parse_url(url)
        pulp_url = 'https://admin:admin@' + amqp_url.host + '/'

    rsa = None
    pem = ""
    if key_file:
        # load rsa and set-up authentication
        rsa = RSA.load_key(key_file)
        bio_fd = BIO.MemoryBuffer()
        rsa.save_pub_key_bio(bio_fd)
        pem = bio_fd.getvalue()

    pulp = Pulp(pulp_url)
    consumer = Consumer.register(pulp, consumer_name, rsa_pub=pem)
    log.info("registered: " + str(consumer))
    a = Agent(pulp_auto.handler, PROFILE=PROFILE)
    qh = QpidHandle(url, consumer_name, authenticator=Authenticator(signing_key=rsa, verifying_key=pulp.pubkey))

    ###
    try:
        with a.catching(reporting), a.running(qh):
            while True:
                try:
                    time.sleep(1.0/polling_frequency)
                except KeyboardInterrupt:
                    log.info("unregistered: " + str(consumer.delete(pulp)))
                    break
    except Exception as e:
        pass


if __name__ == '__main__':
    app.run()
