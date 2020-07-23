#!/bin/csh -f

#Submission script siutable for high-throughput calculations

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

echo "Submitting $1 files"

set i=0
while ($i < $maxDepth)

	foreach j ($dirControl)
		cd j >~/scratch/uselessFile
	
		if (-f TO_BE_RESUBBED) then

#do stuff here------------------------------------------------------------------------------
if(!(-f SUBFLAG)) then
	cp $origLoc/RUN RUN$rnCount
	cp $origLoc/POTCAR .
	cp $origLoc/KPOINTS .
	cp $origLoc/INCAR .

	if(-f CONTCAR) then
		set contLines=`cat CONTCAR | wc -l`
		if("$contLines" > 5) then
			mv POSCAR POSCAR0
			mv OUTCAR OUTCAR0
			mv CONTCAR POSCAR
		endif
	endif

	qsub RUN$rnCount
	touch SUBFLAG
	@ rnCount++

	if($rnCount >= "$1") then
		goto earlyTerm
	endif
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

#SWITCH CASES
earlyTerm:
	cd $origLoc
	rm -rf depthControl

	echo "Exceeded max submissions.  Exiting now."
	exit 1

