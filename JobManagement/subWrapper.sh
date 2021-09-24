#!/bin/csh

set wrapLoc=`pwd`
while(1)
	#Forced term condition.  Use by appending the word STOP to nohup.out
	if(-f "nohup.out") then
		set tai=`tail -1 nohup.out`
		if("$tai" == "STOP") then
			break
		endif
	endif
	
	#Find the number of files that we have room to submit, and submit them  
	set lines=`qstat -u vkb5066 | grep vkb5066 | wc -l`
	set toSub=`echo "99-$lines" | bc -l`
	if("$toSub" > "2") then
		cd $wrapLoc
		./htSub.sh "$toSub"
	else
		echo "Files are still in queue"
	endif

	#End of script condition.  htSub.sh will write this string to nohup.out when 
	#there are no more files to submit
	if(-f "nohup.out") then
		set tai=`tail -1 nohup.out`
		if("$tai" == "Script Finished") then
			break
		endif
	endif		

	sleep 900
end
