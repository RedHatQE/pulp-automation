#!/bin/bash
# follows https://pulp-user-guide.readthedocs.org/en/latest/installation.html


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
baseurl=http://repos.fedorapeople.org/repos/pulp/pulp/beta/2.4/fedora-\$releasever/\$basearch/
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

# eu-west-1 pulp-mirror
[pulp-v2-beta-mirror]
name=Pulp v2 Beta Builds Mirror
baseurl=http://ec2-54-74-186-187.eu-west-1.compute.amazonaws.com/pulp/repos/pulp/beta/2.4/fedora/\$basearch/
enabled=1
skip_if_unavailable=1
gpgcheck=0

PULP_REPO_EOF
popd

# install pulp
yum update -y selinux-policy-targeted ||: # avoid  https://bugzilla.redhat.com/show_bug.cgi?id=877831
yum update -y

# now need to install manually mongo and qpid as dependencies were removed
yum -y install mongodb-server
# qpid-cpp-server-store package provides durability, a feature that saves broker state if the broker is restarted. This is a required feature for the correct operation of Pulp
yum -y install qpid-cpp-server qpid-cpp-server-store
yum -y install redis

# FIXME --- postinstall scriptlets failing...
# For Pulp installation that use Qpid, install Pulp server using:
yum -y groupinstall pulp-server-qpid

yum groupinstall -y 'development tools'
yum install -y python-devel git tito createrepo ruby wget checkpolicy selinux-policy-devel qpid-tools buildbot-master buildbot-slave libxml2-devel libxslt-devel mongodb python-nose

# configure pulp
sed -i s,^[#\ ]*url:.*tcp://.*:5672,url:tcp://`hostname`:5672, /etc/pulp/server.conf
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
sed -i s,^[#\ ]*host.*=.*,host=`hostname`, /etc/pulp/admin/admin.conf
grep host= /etc/pulp/admin/admin.conf
#disable verification
#sed -i s,^[#\ ]*verify_ssl.*=.*,verify_ssl=False, /etc/pulp/admin/admin.conf

# configure local consumer
# For environments that use Qpid, install the Pulp consumer client, agent packages, and Qpid specific consumer dependencies with one command by running:
yum -y groupinstall pulp-consumer-qpid
sed -i s,^[#\ ]*host.*=.*,host=`hostname`, /etc/pulp/consumer/consumer.conf
grep host= /etc/pulp/consumer/consumer.conf
#disable verification
#sed -i s,^[#\ ]*verify_ssl.*=.*,verify_ssl=False, /etc/pulp/consumer/consumer.conf


#enable ssl
touch /etc/pki/CA/index.txt
echo '01' > /etc/pki/CA/serial
pushd /etc/pki/CA/
# CA
openssl req -new -x509 -nodes -out certs/myca.crt -keyout private/myca.key -subj "/C=US/ST=NC/L=Raleigh/O=Ltd/CN=`hostname`"
chmod 0400 /etc/pki/CA/private/myca.key
# apache
openssl req -new -nodes -keyout private/apache.key -out apache.csr -subj "/C=US/ST=NC/L=Raleigh/O=Ltd/CN=`hostname`"
chown root.apache /etc/pki/CA/private/apache.key
chmod 0440 /etc/pki/CA/private/apache.key
# sign apache
openssl ca -batch -cert certs/myca.crt -keyfile private/myca.key -out certs/apache.crt -in apache.csr
#TODO modify conf file
cp certs/myca.crt /etc/pki/tls/certs/
sed -i s,^[#\ ]*SSLCertificateFile.*,SSLCertificateFile\ /etc/pki/CA/certs/apache.crt, /etc/httpd/conf.d/ssl.conf
sed -i s,^[#\ ]*SSLCertificateKeyFile.*,SSLCertificateKeyFile\ /etc/pki/CA/private/apache.key, /etc/httpd/conf.d/ssl.conf
sed -i "/^\[server\]$/,/^\[/ s/^[#\ ]*ca_path =.*/ca_path = \/etc\/pki\/tls\/certs\/myca.crt/" /etc/pulp/consumer/consumer.conf
sed -i "/^\[server\]$/,/^\[/ s/^[#\ ]*ca_path =.*/ca_path = \/etc\/pki\/tls\/certs\/myca.crt/" /etc/pulp/admin/admin.conf
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


# Setting the number of apache processes to 1 due to https://bugzilla.redhat.com/show_bug.cgi?id=1121102 as a temprary workaround until the bz will be fixed.
# for more details see the bz itself
rpm -q --queryformat '%{VERSION}' pulp-server | grep '2\.4\.0' && sed -i s,processes=.,processes=1, /etc/httpd/conf.d/pulp.conf

# enable services
systemctl enable redis
systemctl start redis
systemctl enable mongod.service
systemctl start mongod.service || systemctl start mongod.service ||systemctl start mongod.service # sometimes it just takes too long and gets killed the first time
systemctl enable qpidd.service
systemctl start qpidd.service

# init db
su - apache -s /bin/sh -c pulp-manage-db

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

### BUILDBOT SECTION
### jsut a very basic single-node deployment
### tracking pulp & pulp_auto repos

# automation dependencies
easy_install pip
pip install -U moncov
cat <<MONCOV_CONF > /etc/moncov.yaml
dbhost: localhost
dbport: 6379
blacklist: []
whitelist: ['.*pulp/.*', '.*pulp_rpm/.*', '.*pulp_puppet/.*', '.*nectar/.*', '.*gofer/.*']

MONCOV_CONF

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
  pulp: &PULP
    auth: [admin, admin]
    url: 'https://`hostname`/'
    hostname: `hostname`
  qpid:
    url: `hostname`
  repos:
    - &ZOO
      id: zoo
      type: rpm
      feed: "http://repos.fedorapeople.org/repos/pulp/pulp/demo_repos/zoo/"
      display_name: ZOo rEPO
  consumers:
  - &MY_CONSUMER
    id: my_consumer
    hostname: `hostname`
    ssh_key:  /home/buildbot/.ssh/id_rsa
    os:
      name: Fedora
      version: 20
    repos:
    - *ZOO
    pulp: *PULP
INVENTORY_EOF
# make .coveragerc available for buildbot
#cp -f /usr/share/pulp_auto/tests/.coveragerc /usr/share/pulp_auto/

# pipe the rest of this script via a sudo call
tail -n +$[LINENO+2] $0 | exec sudo -i -u buildbot bash
exit $?

# preserve logging
set -xe

# create repo directory
mkdir -p /tmp/tito
pushd /tmp/tito
wget https://raw.github.com/pulp/pulp/master/comps.xml
popd

# allow buildbot logging-in via ssh (consumer simulation part)
ssh-keygen -f ~/.ssh/id_rsa -N ""
sudo tee -a /root/.ssh/authorized_keys < ~/.ssh/id_rsa.pub

# deploy buildbot
mkdir workdir
pushd workdir

buildbot create-master -r master
buildslave create-slave slave localhost:9989 example-slave pass

wget -N -O master/master.cfg https://raw.github.com/RedHatQE/pulp-automation/master/buildbot/master.cfg
wget -N -O master/jenkins_feed.py https://raw.github.com/RedHatQE/pulp-automation/master/buildbot/jenkins_feed.py
# FIXME disable the jenkins feed
sed -e "s/cmd\s*=\s*\['curl',/cmd = ['echo', 'curl',/" -i master/jenkins_feed.py

buildbot start master
buildslave start slave
popd
