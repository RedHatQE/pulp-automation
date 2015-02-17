#!/bin/bash
# follows https://pulp-user-guide.readthedocs.org/en/latest/installation.html


# exec &>> /var/log/fedora_pulp.log
set -xe

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
cat <<INVENTORY_EOF | exec sudo -i -u buildbot bash
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
INVENTORY_EOF
exit $?
