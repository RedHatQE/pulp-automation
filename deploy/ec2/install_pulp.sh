#!/bin/bash
# follows https://pulp-user-guide.readthedocs.org/en/pulp-2.2/installation.html


# exec &>> /var/log/fedora_pulp.log
set -xe

# fetch pulp repo file
pushd /etc/yum.repos.d/
cat <<PULP_REPO_EOF > fedora-pulp.repo
# beta
[pulp-v2-beta]
name=Pulp v2 Beta Builds
baseurl=http://repos.fedorapeople.org/repos/pulp/pulp/beta/2.6/fedora-\$releasever/\$basearch/
enabled=1
skip_if_unavailable=1
gpgcheck=0
PULP_REPO_EOF
popd

# configure firewall
# iptables -I INPUT -p tcp --destination-port 443 -j ACCEPT
# iptables -I INPUT -p tcp --destination-port 5672 -j ACCEPT
# service iptables save ||

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
sed -i "/^\[server\]$/,/^\[/ s/^[# ]*host\s*[:=].*/host: `hostname`/"  /etc/pulp/admin/admin.conf
grep host: /etc/pulp/admin/admin.conf
#disable verification
#sed -i "/^\[server\]$/,/^\[/ s/^[# ]*verify_ssl:.*/verify_ssl: False /"  /etc/pulp/admin/admin.conf

# configure local consumer
# For environments that use Qpid, install the Pulp consumer client, agent packages, and Qpid specific consumer dependencies with one command by running:
yum -y groupinstall pulp-consumer-qpid
sed -i "/^\[server\]$/,/^\[/ s/^[# ]*host\s*[:=].*/host: `hostname`/"  /etc/pulp/consumer/consumer.conf
grep host: /etc/pulp/consumer/consumer.conf
#disable verification
#sed -i "/^\[server\]$/,/^\[/ s/^[# ]*verify_ssl:.*/verify_ssl: False /" /etc/pulp/consumer/consumer.conf

#install Docker plugins
yum install -y pulp-docker-admin-extensions pulp-docker-plugins python-pulp-docker-common

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
sed -i "/^\[server\]$/,/^\[/ s/^[# ]*ca_path[: =].*/ca_path: \/etc\/pki\/tls\/certs\/myca.crt/"  /etc/pulp/consumer/consumer.conf
sed -i "/^\[server\]$/,/^\[/ s/^[# ]*ca_path[: =].*/ca_path: \/etc\/pki\/tls\/certs\/myca.crt/"  /etc/pulp/admin/admin.conf
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
rpm -q --queryformat '%{VERSION}' pulp-server | grep '2\.4\.1' && sed -i s,processes=.,processes=1, /etc/httpd/conf.d/pulp.conf

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
