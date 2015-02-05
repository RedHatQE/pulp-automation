#!/bin/bash

exec &> /var/log/fedora_pulp_amazon.log
set -xe

# while ! [ -x /sbin/ldconfig ] ; do sleep 1 ; echo -n . ; done
# echo

# # enable root access - not allowed by default
cat ~fedora/.ssh/authorized_keys > ~/.ssh/authorized_keys
sed -i s,disable_root:.*,disable_root:0, /etc/cloud/cloud.cfg
grep disable_root /etc/cloud/cloud.cfg

# # hostname - internal and external hostname at amazon cloud differs
hostname `curl -# http://169.254.169.254/latest/meta-data/public-hostname`
grep HOSTNAME= /etc/sysconfig/network || echo HOSTNAME=`hostname` >> /etc/sysconfig/network
sed -i s,HOSTNAME=.*$,HOSTNAME=`hostname`, /etc/sysconfig/network
grep HOSTNAME= /etc/sysconfig/network
echo `curl -# http://169.254.169.254/latest/meta-data/public-ipv4` `hostname` >> /etc/hosts
tail -1 /etc/hosts

#TODO how to run it?
#
# PULP install
#
# curl https://raw.githubusercontent.com/kvitajakub/pulp-automation/master/deploy/ec2/install_pulp.sh | sed "s/exec &>/exec &>>/"

# configure firewall
iptables -I INPUT -p tcp --destination-port 443 -j ACCEPT
iptables -I INPUT -p tcp --destination-port 5672 -j ACCEPT
service iptables save ||


# enable services
systemctl enable mongod.service
systemctl start mongod.service || systemctl start mongod.service # sometimes it just takes too long and gets killed the first time
systemctl enable qpidd.service
systemctl start qpidd.service

# init db
pulp-manage-db

# start apache
systemctl enable httpd.service
systemctl start httpd.service

# start consumer service
systemctl enable goferd.service
systemctl start goferd.service

#celery section
#enable pulp workers to perform ditributed tasks
systemctl enable pulp_workers
systemctl start pulp_workers
systemctl enable pulp_celerybeat
systemctl start pulp_celerybeat
# this process acts as a task router, deciding which worker should perform certain types of tasks.
systemctl enable pulp_resource_manager
systemctl start pulp_resource_manager


# TODO copy from the other
# buildbot install
#
#
# curl