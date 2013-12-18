#!/bin/bash
# follows https://pulp-user-guide.readthedocs.org/en/pulp-2.2/installation.html


exec &> /var/log/fedora_pulp.log
set -xe

while ! [ -x /sbin/ldconfig ] ; do sleep 1 ; echo -n . ; done
echo

# enable root access
cat ~fedora/.ssh/authorized_keys > ~/.ssh/authorized_keys
sed -i s,disable_root:.*,disable_root:0, /etc/cloud/cloud.cfg
grep disable_root /etc/cloud/cloud.cfg

# hostname
hostname `curl -# http://169.254.169.254/latest/meta-data/public-hostname`
grep HOSTNAME= /etc/sysconfig/network || echo HOSTNAME=`hostname` >> /etc/sysconfig/network
sed -i s,HOSTNAME=.*$,HOSTNAME=`hostname`, /etc/sysconfig/network
grep HOSTNAME= /etc/sysconfig/network
echo `curl -# http://169.254.169.254/latest/meta-data/public-ipv4` `hostname` >> /etc/hosts
tail -1 /etc/hosts

# fetch pulp repo file
pushd /etc/yum.repos.d/
cat << PULP_REPO_EOF > fedora-pulp.repo
# Version 2.x Production Releases
[pulp-v2-stable]
name=Pulp v2 Production Releases
baseurl=http://repos.fedorapeople.org/repos/pulp/pulp/stable/2/fedora-\$releasever/\$basearch/
enabled=1
skip_if_unavailable=1
gpgcheck=0

# Version 2.x Beta Builds
[pulp-v2-beta]
name=Pulp v2 Beta Builds
baseurl=http://repos.fedorapeople.org/repos/pulp/pulp/beta/2.3/fedora-\$releasever/\$basearch/
enabled=1
skip_if_unavailable=1
gpgcheck=0

# Weekly Testing Builds
[pulp-v2-testing]
name=Pulp v2 Testing Builds
baseurl=http://repos.fedorapeople.org/repos/pulp/pulp/testing/fedora-\$releasever/\$basearch/
enabled=1
skip_if_unavailable=1
gpgcheck=0 
PULP_REPO_EOF
popd

# install pulp
yum update -y selinux-policy-targeted ||: # avoid  https://bugzilla.redhat.com/show_bug.cgi?id=877831
yum update -y
# FIXME --- postinstall scriptlets failing...
yum -y groupinstall pulp-server

# configure firewall
iptables -I INPUT -p tcp --destination-port 443 -j ACCEPT
iptables -I INPUT -p tcp --destination-port 5672 -j ACCEPT
service iptables save

# configure pulp
sed -i s,url:.*tcp://.*:5672,url:tcp://`hostname`:5672, /etc/pulp/server.conf
grep url:.*:5672 /etc/pulp/server.conf

# configure qpidd
grep auth= /etc/qpidd.conf || echo auth=no >> /etc/qpidd.conf
sed -i s,auth=.*$,auth=no, /etc/qpidd.conf
grep auth= /etc/qpidd.conf

# configure pulp-admin
yum -y groupinstall pulp-admin
sed -i s,host.*=.*,host=`hostname`, /etc/pulp/admin/admin.conf
grep host= /etc/pulp/admin/admin.conf

# configure local consumer
yum -y groupinstall pulp-consumer
sed -i s,host.*=.*,host=`hostname`, /etc/pulp/consumer/consumer.conf
grep host= /etc/pulp/consumer/consumer.conf

# generate ssl certs
pushd /etc/pki/tls
old_umask=`umask`
umask 0077
openssl req -new -x509 -nodes -out certs/localhost.crt -keyout private/localhost.key -subj "/C=US/ST=NC/L=Raleigh/CN=`hostname`"
umask $old_umask
chmod go+r certs/localhost.crt
popd

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
