#!/bin/bash


exec &> /var/log/fedora_pulp.log
set -xe

while ! [ -x /sbin/ldconfig ] ; do sleep 1 ; echo -n . ; done
echo

function service_start {
    systemctl enable $1.service
    if [ "$1" == "mongod" ]; then
      systemctl start $1.service
      sleep 300
      systemctl status $1.service
    else
      systemctl start $1.service
    fi
}

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
cat << PULP_REPO_EOF > rhel6-pulp.repo
# Weekly Testing Builds
[pulp-v2-testing]
name=Pulp v2 Testing Builds
baseurl=http://repos.fedorapeople.org/repos/pulp/pulp/testing/2.6/\$releasever/\$basearch/
enabled=1
skip_if_unavailable=1
gpgcheck=0
PULP_REPO_EOF

cat << EPEL_REPO_EOF > rhel7-epel.repo
[epel]
name=Extra Packages for Enterprise Linux 7 - $basearch
#baseurl=http://download.fedoraproject.org/pub/epel/7/$basearch
mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-7&arch=$basearch
failovermethod=priority
enabled=1
gpgcheck=0
EPEL_REPO_EOF
popd

# install pulp
yum update -y selinux-policy-targeted ||: # avoid  https://bugzilla.redhat.com/show_bug.cgi?id=877831
yum update -y
# FIXME --- postinstall scriptlets failing...
yum -y install mongodb-server
yum -y install qpid-cpp-server
yum -y groupinstall pulp-server
yum -y install python-qpid-qmf

# configure firewall
iptables -I INPUT -p tcp --destination-port 443 -j ACCEPT
iptables -I INPUT -p tcp --destination-port 5672 -j ACCEPT
service iptables save ||

# configure pulp
sed -i s,url:.*tcp://.*:5672,url:tcp://`hostname`:5672, /etc/pulp/server.conf
grep url:.*:5672 /etc/pulp/server.conf

#configure borker_url
sed -i s,^[#\ ]*broker_url:.*qpid://guest@localhost/,broker_url:qpid://`hostname`:5672/, /etc/pulp/server.conf
grep broker_url:.*:5672/ /etc/pulp/server.conf

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

#install Docker plugins
yum install -y pulp-docker-admin-extensions pulp-docker-plugins python-pulp-docker-common

# generate ssl certs and ca
pulp-gen-ca-certificate
pushd /etc/pki/tls/certs
# make the pulp ca.crt trusted system-wide
ln -sf /etc/pki/pulp/ca.crt `openssl x509 -noout -hash -in /etc/pki/pulp/ca.crt`.0
popd

pushd /etc/qpid/
cat << QPIDD_EOF > qpidd.conf
ssl-require-client-authentication=no
auth=no
log-to-syslog=yes
log-enable=info+
log-time=yes
log-source=yes
log-function=yes
QPIDD_EOF
popd

#Workaround bug 1121102
rpm -q --queryformat '%{VERSION}' pulp-server | grep '2\.4\.0' && sed -i s,processes=.,processes=1, /etc/httpd/conf.d/pulp.conf

# enable services
  service_start mongod
  service_start qpidd
  su - apache -s /bin/sh -c pulp-manage-db
  service_start httpd
  service_start goferd
  service_start pulp_workers
  service_start pulp_celerybeat
  service_start pulp_resource_manager

