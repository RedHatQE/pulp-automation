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

# insecure qpidd is required
cat <<QPIDD_CONF > /etc/qpid/qpidd.conf
ssl-require-client-authentication=no
auth=no
log-to-syslog=yes
log-enable=info+
log-time=yes
log-source=yes
log-function=yes
QPIDD_CONF

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

### BUILDBOT SECTION
### jsut a very basic single-node deployment
### tracking pulp & pulp_auto repos
iptables -I INPUT -p tcp --destination-port 8010 -j ACCEPT
service iptables save

yum groupinstall -y 'development tools'
yum install -y python-devel git tito createrepo ruby wget python-gevent python-nose checkpolicy selinux-policy-devel qpid-tools buildbot-master buildbot-slave python-boto

cat <<LOCAL_PULP_REPO_EOF > /etc/yum.repos.d/pulp-local.repo
[pulp-local-build]
name=pulp local build
baseurl=file:///tmp/tito
enabled=1
skip_if_unavailable=1
gpgcheck=0
LOCAL_PULP_REPO_EOF

sed -ie 's/^\s*\(Defaults\s*requiretty\)/# \1/' /etc/sudoers
adduser buildbot -d /home/buildbot -m -s /bin/bash
cat <<BUILDBOT_SUDOERS_EOF > /etc/sudoers.d/91-buildbot-users
buildbot ALL=(ALL) NOPASSWD:ALL
BUILDBOT_SUDOERS_EOF
chmod ugo-w /etc/sudoers.d/91-buildbot-users
restorecon /etc/sudoers.d/91-buildbot-users

mkdir -p /usr/share/pulp_auto/
cat <<INVENTORY_EOF > /usr/share/pulp_auto/inventory.yml
ROLES:
  pulp:
    auth: [admin, admin]
    url: 'https://`hostname`/'
  qpid:
    url: '`hostname`'
INVENTORY_EOF

# pipe the rest of this script via a sudo call
tail -n +$[LINENO+2] $0 | exec sudo -i -u buildbot bash
exit $?

# preserve logging
set -xe

mkdir -p /tmp/tito
pushd /tmp/tito
wget https://raw.github.com/pulp/pulp/master/comps.xml
popd

mkdir workdir
pushd workdir

buildbot create-master -r master
buildslave create-slave slave localhost:9989 example-slave pass

wget -N -O master/master.cfg https://raw.github.com/RedHatQE/pulp-automation/master/buildbot/master.cfg

buildbot start master
buildslave start slave
popd
