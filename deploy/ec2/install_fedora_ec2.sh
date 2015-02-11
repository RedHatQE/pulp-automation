#!/bin/bash

OUTPUT="/var/log/fedora_pulp_amazon.log"
exec &> $OUTPUT
set -xe

# while ! [ -x /sbin/ldconfig ] ; do sleep 1 ; echo -n . ; done
# echo

## enable root access
cat ~fedora/.ssh/authorized_keys > ~/.ssh/authorized_keys
sed -i s,disable_root:.*,disable_root:0, /etc/cloud/cloud.cfg
grep disable_root /etc/cloud/cloud.cfg

## hostname
hostname `curl -# http://169.254.169.254/latest/meta-data/public-hostname`
grep HOSTNAME= /etc/sysconfig/network || echo HOSTNAME=`hostname` >> /etc/sysconfig/network
sed -i s,HOSTNAME=.*$,HOSTNAME=`hostname`, /etc/sysconfig/network
grep HOSTNAME= /etc/sysconfig/network
echo `curl -# http://169.254.169.254/latest/meta-data/public-ipv4` `hostname` >> /etc/hosts
tail -1 /etc/hosts

# PULP install
#
curl https://raw.githubusercontent.com/kvitajakub/pulp-automation/master/deploy/ec2/install_pulp.sh | su - root -s /bin/sh &>> $OUTPUT

# configure firewall
# iptables -I INPUT -p tcp --destination-port 443 -j ACCEPT
# iptables -I INPUT -p tcp --destination-port 5672 -j ACCEPT
# service iptables save ||

# BUILDBOT install
#
curl https://raw.githubusercontent.com/kvitajakub/pulp-automation/master/deploy/ec2/install_buildbot.sh | su - root -s /bin/sh &>> $OUTPUT
