#!/bin/bash
set -x

function pulp_services() {
systemctl list-unit-files | egrep 'pulp|httpd|gofer' | cut -d\  -f1
}

function reset_pulp() {
mongo pulp_database --eval "db.dropDatabase()"
sudo -u apache pulp-manage-db
}

function set_up() {
# stop pulp
# reset stats
# configure moncov
# restart updater
# enable moncov
# start pulp
BUFF_LEN=$1 ; shift
TIME_UPD=$1 ; shift
INS_CONC=$1 ; shift

moncov disable ||:
killall moncov ||:
systemctl stop `pulp_services`
reset_pulp

sed -i -e "s/lines, w=[01]/lines, w=$INS_CONC/" /usr/lib/python2.7/site-packages/moncov/tracer.py
cat << CONF_EOF > /etc/moncov.yaml
dbhost: localhost                                                                                                                                                                                                                            
dbport: 27017                                                                                                                                                                                                                                
events_count: $BUFF_LEN
blacklist: []                                                                                                                                                                                                                                
whitelist: ['.*pulp/.*', '.*pulp_rpm/.*', '.*pulp_puppet/.*', '.*nectar/.*', '.*gofer/.*']
CONF_EOF

moncov reset
moncov update -s -t $TIME_UPD
moncov enable
systemctl start `pulp_services`
sleep 60
}

function tear_down() {
# stop pulp
# reset pulp
# stop tracing
systemctl stop `pulp_services`
moncov disable ||:
killall moncov ||:
reset_pulp
}

function collect_stats() {
# dump simple_xml stats
FILE=$1; shift
moncov simple_xml -o $FILE
}

function run_tests() {
FILE=$1; shift
nosetests -v --with-xunit --xunit-file=$FILE  2> $FILE.log ||:
}

### MAIN
pushd /usr/share/pulp_auto
for repeat in {1..3} ; do
	for write_concerns in 0 1; do
		for buffer_length in 100000 150000 200000 250000 300000 ; do
			for update_time in "1" "0.8" "0.6" "0.4" "0.2" ; do
				DESCRIPTION="_r-${repeat}_w-${write_concerns}_b-${buffer_length}_t-${update_time}"
				COVERAGE_FILE=coverage-${DESCRIPTION}.xml
				XUNIT_FILE=xunit-${DESCRIPTION}.xml
				set_up $buffer_length $update_time $write_concerns
				run_tests $XUNIT_FILE
				tear_down
				collect_stats $COVERAGE_FILE
			done
		done
	done
done

popd
