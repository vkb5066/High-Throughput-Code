# High-Throughput-Code
Code that I've used to create, submit and manage large amounts of VASP runs on Penn State ACI machines.


***FILE CREATION FOLDER***:
The idea is to start with a base POSCAR file and generate every possible combo of atom positions (with some reasonable restrictions - 
i.e. the number of atoms that you began with must be the same as the number you end with.  This could be removed, but the number of
possible files grows very fast by doing this).
Then, represent each element as a number, and each atom site as an index (just make arbitrary choices, but stick with them). 
After that, generate all of the permutations of those numbers and indexes.  
Translate them into VASP POSCAR files.

  WriteConfigs.cpp:
  I used the 16 bit version (2 elements and 16 sites), but later generalized the code for n elements and m sites.  In the generalized code,
  BASE is the number of unique elements, BUFF is the number of sites, and COND is a restriction array.  It is set to print permutations to
  the screen instead of to a file, so it is easiest to pipe the output to a file.  I ran it by:
    g++ -o write WriteConfigs16Bit.cpp
    ./write >seeds

  AtomSwap.py:
  Translates seeds into POSCAR files.  As is written right now, Ag is 0 and Bi is 1.  My beginning POSCAR file was named "start". It creates 
  a directory for each POSCAR file created.  The dir names correspond to the seed number, and they are ordered by the number of atoms that 
  have been swapped (0 thru 8).  
  
  Poscar.py:
  Helper file for AtomSwap.py.  Takes care of reading, organizing, and writing POSCAR files


***JOB MANAGEMENT FOLDER***
After making the files, use these scripts to manage (hopefully automatically) the jobs.  It is written with the assumption that the user has
a limited number of nodes that they can use.  It is also written with my username (vkb5066) in it, so be sure to change all of those to your
username before running these.

  subWrapper.sh:
  An infinite loop that runs every 15 minutes until either the user kills it or there are no more files to run.  Checks the current queue and
  automatically submits files up until the queue is filled to a certian capacity.  Can be stopped manually by writing the string "STOP" to 
  nohup.out.  Use it like so:
    nohup ./subWrapper.sh &
  
  htSub.sh:
  Sub-script that is called by the wrapper script.  Takes care of traversing the directory tree, submitting files, and exiting when necessary.
  You do not need to execute this script, just leave it in the same directory as the wrapper script.
  
  tagFilesThatAreNotDone.sh:
  Moves through the directory tree and checks OUTCAR files for the timing information that is written when a run is sucessfully completed.  If
  that info is not found, it puts a resubmission flag in the directory.  You would use this by running subWrapper.sh, and then when all of the 
  files have finished running, run this script to tag files that need resubmitted.
  
  removeSuspended.sh:
  Periodically checks the user's queue to remove suspended jobs from the queue, which frees those spots for new files to be submitted.  It will
  stop under the same circumstances that subWrapper.sh will stop.  Run with
    nohup ./removeSuspended.sh &
  It is useful to stagger this script w.r.t. the subWrapper by about 5-10 minutes.
  
  
  
  
  
  
 
