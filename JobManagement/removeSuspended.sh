#!/bin/bash

origLoc=`pwd`
while [ true ]; do
	#Forced Terminating Condition
        if [ -f "nohup.out" ]; then
                tai=`tail -1 nohup.out`
                if [ "$tai" == "STOP" ]; then
                        break
                fi
        fi       

	#Get all suspended files into an array (it will find them if the requested time ends with the string 00)
        qstat -u vkb5066 | grep "00 S" | awk -F '.' '{print $1}' >$origLoc/suspendedFiles
        mapfile -t arr <$origLoc/suspendedFiles
        
	#Delete the files from the queue
        for i in "${arr[@]}"; do
        	qdel "$i"
        done

	#Terminating Condition
        if [ -f "nohup.out" ]; then
                tai=`tail -1 nohup.out`
                if [ "$tai" == "Script Finished" ]; then
                        break
                fi
        fi       
 
        sleep 900
done
