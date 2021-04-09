#!/bin/bash
path=`dirname "$0":`
mqtt=`cat $path/settings | grep mqttserver | cut -f2`
mqttuser=`cat $path/settings | grep mqttuser | cut -f2`
mqttpass=`cat $path/settings | grep mqttpass | cut -f2`
mqttport=`cat $path/settings | grep mqttport | cut -f2`
name=`cat $path/settings | grep hassname | cut -f2`

check()
{
$path/heatpump info
sleep 1
}

mosquitto_sub -v -R -h $mqtt -p $mqttport -u $mqttuser -P $mqttpass -t homeassistant/# | while read line
do
	settemp=`echo $line | grep "$name"_settemp/state | rev | cut -d ' ' -f1 | rev`
	mode=`echo $line | grep "$name"_mode_set/state | rev | cut -d ' ' -f1 | rev`
	silent=`echo $line | grep "$name"_silent/set | rev | cut -d ' ' -f1 | rev`
	if [ ! -z $settemp ]; then
		$path/heatpump temp $settemp
		echo $line
		check
	fi
	if [ ! -z $silent ]; then
		$path/heatpump silent $silent
		echo $line
		check
	fi	
	if [ ! -z $mode ]; then
		echo $line
		if [ $mode = "off" ]; then
			$path/heatpump off
			check
		elif [ $mode = "heat" ]; then
			$path/heatpump on
			$path/heatpump mode heat
			check
		elif [ $mode = "auto" ]; then
			$path/heatpump on
			$path/heatpump mode auto
			check
		elif [ $mode = "cool" ]; then
			$path/heatpump on
			$path/heatpump mode cool
			check
		fi
	fi

done
