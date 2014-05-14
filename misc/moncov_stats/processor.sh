#!/bin/bash
set -xe

function filename_to_csv_address() {
	# convert an $ID, $FILE to a CSV address 
	# ID,round,write_concern,buff_len,update_speed
	local ID ; ID=$1 ; shift
	local FILE ; FILE=$1 ; shift
	# strip unnecessary information
	FILE=${FILE#*-}
	FILE=${FILE%.xml*}
	# convert to a CSV address & 'return'
	echo ${ID}${FILE//_?-/,}
}	

function log_to_data() {
	# convert nosetests log file staus:
	#   Ran 199 tests in 381.084s
	#
	#   FAILED (errors=14, failures=16)
	# to a CSV value:
	#   ,total_tests,total_time,errors,failures
	local FILE ; FILE=$1 ; shift
	local total_tests_and_time;
	tail -3 $FILE | head -1 | sed -e's/[^[:digit:]]\+\([[:digit:]]\+\)[^[:digit:]]\+\([[:digit:]\.]\+\).*/,\1,\2/'
	echo -n ','
	tail -1 $FILE | sed -e 's/[^[:digit:]]*\([[:digit:]]\+\)[^[:digit:]]*\([[:digit:]]\+\).*/\1,\2/'
}

function coverage_to_data() {
	# convert coverage cobertura.xml:
	#   <coverage timestamp="1399046719586" complexity="0.00" version="3.7" branch-rate="0.0000" line-rate="0.0000" lines-covered="0" lines-valid="0" branches-covered="0" branches-valid="0"> 
	# to data:
	#   ,line_rate,branch_rate
	local FILE ; FILE=$1 ; shift
	head -3 $FILE | tail -1 | sed -e's/.*branch-rate="\([[:digit:]\.]\+\).*line-rate="\([[:digit:]\.]\+\).*/,\2,\1/'
}

function data_file_pairs() {
	# files from a directory as data pairs
	# coverage-*.xml and xunit-*.log
	local dir ; dir=$1; shift
	local coverage_file
	local log_file
	for coverage_file in ${dir}/coverage-*.xml ; do
		log_file=${dir}/xunit-${coverage_file#*coverage-}.log
		echo ${coverage_file},${log_file}
	done
}
	

### main
# $@: all directories to process;
# `basename $directory` will be the first column of data
echo dir,round,write_concern,buff_len,update_speed,total_tests,total_time,errors,failures,line_rate,branch_rate
for dir in $@ ; do
	for file_pair in `data_file_pairs $dir` ; do
		log=${file_pair#*,}
		coverage=${file_pair%,*}
		address_file=`basename $log`
		id=`basename $dir`
		address=`filename_to_csv_address $id $address_file`
		test_stats=`log_to_data $log`
		coverage_stats=`coverage_to_data $coverage`
		echo ${address}${test_stats}${coverage_stats}
	done
done
