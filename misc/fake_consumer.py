#!/usr/bin/python
from pulp_auto.qpid_handle import QpidHandle 
from pulp_auto.agent import Agent
from pulp_auto.handler.profile import PROFILE 
import logging, sys, pulp_auto, time
import aaargh


logging.basicConfig(level=logging.INFO) #level=logging.DEBUG)

app = aaargh.App(description='Fake pulp consumer')


@app.cmd(help='run the consumer')
@app.cmd_arg('-u', '--url', help='URL of the AMQP broker to use', default='localhost')
@app.cmd_arg('-n', '--consumer-name', help='consumer name to use', default='fake_consumer')
@app.cmd_arg('-r', '--reporting', help='propagate errors back', default=False, action='store_true')
@app.cmd_arg('-f', '--polling-frequency', help='polling frequency', type=float, default=3.0)
def run(url, consumer_name, reporting, polling_frequency):
    from gevent import monkey
    monkey.patch_all(select=False, thread=False)
    a = Agent(pulp_auto.handler, PROFILE=PROFILE)
    qh = QpidHandle(url, consumer_name)
    ###
    try:
        with a.catching(reporting), a.running(qh):
            while True:
                try:
                    time.sleep(1.0/polling_frequency)
                except KeyboardInterrupt:
                    break
    except Exception as e:
        pass


if __name__ == '__main__':
    app.run()
