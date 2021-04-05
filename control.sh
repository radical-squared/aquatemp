#!/bin/bash
path=`dirname "$0":`
mqtt=`cat $path/settings | grep mqttserver | cut -f2`
mqttuser=`cat $path/settings | grep mqttuser | cut -f2`
mqttpass=`cat $path/settings | grep mqttpass | cut -f2`
mqttport=`cat $path/settings | grep mqttport | cut -f2`
name=`cat $path/settings | grep hassname | cut -f2`

mosquitto_sub -v -R -h $mqtt -p $mqttport -u $mqttuser -P $mqttpass -t homeassistant/# | while read line
do
	settemp=`echo $line | grep "$name"_settemp | rev | cut -d ' ' -f1 | rev`
	mode=`echo $line | grep "$name"_mode_set | rev | cut -d ' ' -f1 | rev`
	silent=`echo $line | grep "$name"_silent | rev | cut -d ' ' -f1 | rev`
	if [ ! -z $settemp ]; then
		$path/heatpump temp $settemp
	fi
	if [ ! -z $silent ]; then
		$path/heatpump silent $silent
	fi	
	if [ ! -z $mode ]; then
		if [ $mode = "off" ]; then
			$path/heatpump off
		elif [ $mode = "heat" ]; then
			$path/heatpump on
			$path/heatpump mode heat
		elif [ $mode = "auto" ]; then
			$path/heatpump on
			$path/heatpump mode auto
		elif [ $mode = "cool" ]; then
			$path/heatpump on
			$path/heatpump mode cool
		fi
	fi

done
