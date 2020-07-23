#!/bin/csh -f

set origLoc=`pwd`
set dirControl="$origLoc/"
set maxDepth=5
set add="*/"
set rnCount=0

#make dirControl in folder to avoid early termination
set z=0
cd $dirControl
mkdir depthControl
cd depthControl
while ($z < $maxDepth)
        mkdir $z
        cd $z
        @ z++
end

set i=0
while ($i < $maxDepth)

	foreach j ($dirControl)
		cd j >~/scratch/uselessFile
	
		if (-f POSCAR) then

#do stuff here------------------------------------------------------------------------------
	if(-f OUTCAR) then
		set comp=`grep "User time (sec)" OUTCAR | wc -l`
		if($comp < 1) then
			touch TO_BE_RESUBBED
		endif
	else
		touch TO_BE_RESUBBED
	endif
#stop doing stuff here----------------------------------------------------------------------
		
		cd ../
		endif
	end

set dirControl="$dirControl$add"
@ i++

end

cd $origLoc
rm -rf depthControl
echo "Script Finished"
exit 0
