#!/bin/bash


echo $1

base_time=`date +%m%d`
echo "testresult will be kept in /home/jf/temp/weekly/"$base_time$1"/"
sleep 3

base_dir="/samba/weekly/"$base_time$1"/"
remote_ip="10.239.44.21"

page_dir="pc_"
tab_dir="tb_"
ld_dir="ld_"

pc_run=0 #pagecycler
tb_run=0 #tabswitch
ld_run=5 #loading.desktop5

#stop powerd _ now not work
stp="ssh "$remote_ip" -l root \"stop powerd\"" 
echo $stp

#run 3 times pageCycler
for((i=1;i<=$pc_run;i++));  
do
echo "testing pc#0"$i
testcmd="python /home/jf/MyWork/AutoTest/perf/run_benchmark --remote="$remote_ip" --browser=cros-chrome page_cycler_v2.typical_25 --pageset-repeat=1 --output-format=html --output-dir="$base_dir$page_dir"0"$i
echo $testcmd  
$testcmd;  
done
 
#run 5 times tabSwitch
for((i=1;i<=$tb_run;i++));  
do
echo "testing tb#0"$i
testcmd="python /home/jf/MyWork/AutoTest/perf/run_benchmark --remote="$remote_ip" --browser=cros-chrome tab_switching.typical_25 --pageset-repeat=1 --output-format=html --also-run-disabled-tests --output-dir="$base_dir$tab_dir"0"$i  
echo $testcmd
$testcmd;  
done 

#run 5 times loading.desktop
for((i=1;i<=$ld_run;i++));
do
echo "testing ld#0"$i
testcmd="python /home/jf/MyWork/AutoTest/perf/run_benchmark --remote="$remote_ip" --browser=cros-chrome loading.desktop --story-tag-filter=typical --pageset-repeat=1 --output-format=html --output-dir="$base_dir$ld_dir"0"$i
echo $testcmd
$testcmd;  
done 
 
chmod 777 /home/jf/temp/weekly/ -R
cd /home/jf/temp/weekly/


