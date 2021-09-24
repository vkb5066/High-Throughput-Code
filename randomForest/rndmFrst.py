#!/usr/bin/python3.9
from sklearn.ensemble import RandomForestRegressor
import os
import numpy as np
from time import sleep
from random import shuffle
from numpy.random import uniform

import headerPoscar as hp
import headerPoscarGen as hpg
import headerBRndmFrst as hrf
rfr = RandomForestRegressor()

TESTING = True ##ignores qsub commands, randomly sets energies, sleep time set to 0.01s
RESTART = False ##loops through existing 'priors/*/' and 'loop*/*/' dirs to reinit rf model

#File Location Constants
HOME = os.getcwd()
INIT_DB_LOC = os.path.join(HOME, "database")
LOG_LOC = os.path.join(HOME, "log")
TRAIN_DAT_LOC = os.path.join(HOME, "trainingDat")
PROG_DAT_LOC = os.path.join(HOME, "progress")
RES_LOC = os.path.join(HOME, "results")
##Vasp run stuff
VASP_DIR = os.path.join(HOME, "vaspRun")
VASP_RUNFILES = {"incar": os.path.join(VASP_DIR, "INCAR"),
                 "kpoints": os.path.join(VASP_DIR, "KPOINTS"),
                 "potcar": os.path.join(VASP_DIR, "POTCAR"),
                 "run": os.path.join(VASP_DIR, "RUN")}
POSCAR_GEN_DIR = os.path.join(HOME, "poscarGen")
POSCAR_GEN_LOCS = {"seedPoscar": os.path.join(POSCAR_GEN_DIR, "seedPoscar"),
                   "mpxSeed": os.path.join(POSCAR_GEN_DIR, "mpxSeeds"),
                   "mppxSeed": os.path.join(POSCAR_GEN_DIR, "mppxSeeds")}

#Random Forest Constants
N_PRIORS = 100
N_JOBS_PER_LOOP = 100
RED_FRAC = 0.1 ##fraction multiplied to old list to get new list for each loop

#Command Constants
N_MAX_RUNNING_JOBS = 100 ##number of jobs allowed to run at once.  floor(100 / coresPerJob) for psu machines
SLEEP_TIME = 900 ##seconds

def CheckExit():
    if(os.path.exists(os.path.join(HOME, "STOP"))):
        hrf.Log(logLoc=LOG_LOC, message="manual stop found\n")
        exit(1)

#-----Main Setup----------------------------------------------------------------------------------------------
if(TESTING):
    hrf.Log(logLoc=LOG_LOC, message="*-*-*-*-*-*  TESTING RUN  *-*-*-*-*-*\n")
    SLEEP_TIME = 0.01

#Read in database, set up list of nodes
hrf.Log(logLoc=LOG_LOC, message="---START DATABASE READ---\n")
allNodes = hrf.InitNodelist(dbLoc=INIT_DB_LOC)
hrf.Log(logLoc=LOG_LOC, message="---END DATABASE READ---\n")

#Setup necessary data for creating turk-style POSCAR files
hpg.Init(origPoscarLoc=POSCAR_GEN_LOCS["seedPoscar"], mpxSeedLoc=POSCAR_GEN_LOCS["mpxSeed"],
         mppxSeedLoc=POSCAR_GEN_LOCS["mppxSeed"])

#Lists for jobs that are available to be run, need to be run, already ran, and currently running
nodesAvail = allNodes[:]
nodesNeedRun = []
nodesFinRun = []
nodesCurrRun = []

#Default values that only change if RESTART = True
loopCounter = -1

if(RESTART):
    #List directories to test
    testDirs = ["priors"]
    i = 0
    while(True):
        if(os.path.exists(os.path.join(HOME, "loop" + str(i)))):
            testDirs.append("loop" + str(i))
            i += 1
        else:
            i = 0
            break
    testDirs = [os.path.join(HOME, td) for td in testDirs]

    #Test to make sure there are the correct number of jobs in each directory
    #If there are,

#-----Random Priors-------------------------------------------------------------------------------------------
hrf.Log(logLoc=LOG_LOC, message="---START PRIOR RUNS---\n")
#Choose which nodes to run, redefine lists
shuffle(nodesAvail)

nodesNeedRun = nodesAvail[:min(N_PRIORS, len(nodesAvail))]
nodesAvail = nodesAvail[min(N_PRIORS, len(nodesAvail)):]
#Main prior loop
hrf.Log(logLoc=LOG_LOC, message="starting loop prior\n")
while(True):
    CheckExit()
    #Prep running directories
    hrf.Log(logLoc=LOG_LOC, message=" (re)creating directories of " + str(len(nodesNeedRun)) + " nodes...\n")
    for node in nodesNeedRun:
        hrf.Log(logLoc=LOG_LOC, message="  genNum=" + str(node.genNum) + " code=" + str(node.codeStr) + \
                                        " (re)created\n")
        node.absPath = os.path.join(HOME, "priors", str(node.genNum))
        node.PrepVaspRun(incarLoc=VASP_RUNFILES["incar"], kptsLoc=VASP_RUNFILES["kpoints"],
                         potcarLoc=VASP_RUNFILES["potcar"], runLoc=VASP_RUNFILES["run"])
        if(not node.VerifyStoich()):
            hrf.Log(logLoc=LOG_LOC, message="  genNum=" + str(node.genNum) + " code=" + str(node.codeStr) + \
                                            " WARNING: POSCAR stoich. error\n")

    #Check currently running files to see which ones are complete, what needs resubbed, etc
    hrf.Log(logLoc=LOG_LOC, message=" updating status of " + str(len(nodesCurrRun)) + " nodes...\n")
    toRemove = []
    for node in nodesCurrRun:
        node.UpdateMyStatus()
        if(TESTING):
            node.myStatus = "converged"
        ##Node is finished running, but not converged yet - remove from curr run list, add to needs run list
        if(node.myStatus == "needs resubbed"):
            hrf.Log(logLoc=LOG_LOC, message="  genNum=" + str(node.genNum) + " code=" + str(node.codeStr) + \
                                            " needs (re)subbed\n")
            toRemove.append(node)
            nodesNeedRun.append(node)
            continue
        ##Unsure of node's convergence (VASP prob. still running).  Can't do anything yet
        if(node.myStatus == "unsure"):
            continue
        ##Node is finished running and converged - read energy, remove from curr run list, add to fin list
        if(node.myStatus == "converged"):
            hrf.Log(logLoc=LOG_LOC, message="  genNum=" + str(node.genNum) + " code=" + str(node.codeStr) + \
                                            " converged\n")
            if(TESTING):
                node.yAct = uniform(low=-100.0, high=0.0)
            else:
                node.GetFinEnergy()
            toRemove.append(node)
            nodesFinRun.append(node)
            continue
    for node in toRemove:
        nodesCurrRun.remove(node)

    #Sub any nodes that need run up to allowed number of running jobs
    hrf.Log(logLoc=LOG_LOC, message=" attempting to sub " + str(len(nodesNeedRun)) + " nodes...\n")
    toRemove = []
    for node in nodesNeedRun:
        if(len(nodesCurrRun) >= N_MAX_RUNNING_JOBS):
            hrf.Log(logLoc=LOG_LOC, message="  sub limit reached - breaking\n")
            break

        hrf.Log(logLoc=LOG_LOC, message="  genNum=" + str(node.genNum) + " code=" + str(node.codeStr) + \
                                        " being subbed\n")
        if(TESTING):
            node.nSubs += 1
        else:
            node.SubVaspRun(returnDir=HOME)
        toRemove.append(node)
        nodesCurrRun.append(node)
    for node in toRemove:
        nodesNeedRun.remove(node)

    #Break conditions: there must be no more jobs that need to be run and no more jobs running
    if(len(nodesNeedRun) + len(nodesCurrRun) == 0):
        hrf.Log(logLoc=LOG_LOC, message="finished loop prior\n")
        break
    #Else take a nap and try again later
    hrf.Log(logLoc=LOG_LOC, message="loop prior still running.  waiting " + str(SLEEP_TIME) + "s\n")
    sleep(SLEEP_TIME)

hrf.Log(logLoc=LOG_LOC, message="---END PRIOR RUNS---\n")


#-----Search Space Min Loops----------------------------------------------------------------------------------
hrf.Log(logLoc=LOG_LOC, message="---START MIN RUNS---\n")

while(loopCounter < len(allNodes)):
    #Pre-loop stuff
    hrf.Log(logLoc=LOG_LOC, message="pre loop " + str(loopCounter) + "\n")
    ##Train model on all available nodes
    hrf.Log(logLoc=LOG_LOC, message=" training model on " + str(len(nodesFinRun)) + " nodes\n")
    rfr.fit(X=np.array([node.X for node in nodesFinRun]), y=np.array([node.yAct for node in nodesFinRun]))
    ##Break Condition: If we've run out of nodes to eval, we're done
    if(len(nodesAvail) == 0):
        break
    ##Predict energies of all available nodes
    hrf.Log(logLoc=LOG_LOC, message=" predicting energies of " + str(len(nodesAvail)) + " nodes\n")
    yPreds = rfr.predict(np.array([node.X for node in nodesAvail]))
    for i, yp in enumerate(list(yPreds)):
        nodesAvail[i].yPred = yp
    ##Dump training data for restarts if necessary
    hrf.Log(logLoc=LOG_LOC, message=" writing training data from " + str(len(nodesFinRun)) + " nodes\n")
    hrf.WriteNodeData(outfileLoc=TRAIN_DAT_LOC, nodeList=nodesFinRun)
    ##Dump progress data for restarts if necessary
    hrf.Log(logLoc=LOG_LOC, message=" writing progress\n")
    lc = "prior" if (loopCounter == 0) else loopCounter - 1 ## -1 bc this is progress of the prev loop
    hrf.WriteProgressData(outfileLoc=PROG_DAT_LOC, loopchar=str(lc),
                          availNodes=nodesAvail, finishedNodes=nodesFinRun)
    ##Reduce search space: sort available nodes from lowest to highest nrgs & remove high nrgs
    if(len(nodesAvail) < N_JOBS_PER_LOOP):
        ssSize = len(nodesAvail)
    else:
        ssSize = int(len(nodesAvail)*RED_FRAC)
    hrf.Log(logLoc=LOG_LOC, message=" reducing search space to " + str(ssSize) + " nodes\n")
    nodesAvail.sort(key=lambda x: x.yPred)
    nodesAvail = nodesAvail[:ssSize]
    ##Randomly choose jobs to run out of the remaining available nodes
    shuffle(nodesAvail)
    nodesNeedRun = nodesAvail[:min(N_JOBS_PER_LOOP, len(nodesAvail))]
    nodesAvail = nodesAvail[min(N_JOBS_PER_LOOP, len(nodesAvail)):]

    # Main minimization loop
    hrf.Log(logLoc=LOG_LOC, message="starting loop " + str(loopCounter) + "\n")
    while (True):
        CheckExit()
        # Prep running directories
        hrf.Log(logLoc=LOG_LOC, message=" (re)creating directories of " + str(len(nodesNeedRun)) + \
                                        " nodes...\n")
        for node in nodesNeedRun:
            hrf.Log(logLoc=LOG_LOC, message="  genNum=" + str(node.genNum) + " code=" + str(node.codeStr) + \
                                            " (re)created\n")
            node.absPath = os.path.join(HOME, "loop" + str(loopCounter), str(node.genNum))
            node.PrepVaspRun(incarLoc=VASP_RUNFILES["incar"], kptsLoc=VASP_RUNFILES["kpoints"],
                             potcarLoc=VASP_RUNFILES["potcar"], runLoc=VASP_RUNFILES["run"])
            if (not node.VerifyStoich()):
                hrf.Log(logLoc=LOG_LOC,
                        message="  genNum=" + str(node.genNum) + " code=" + str(node.codeStr) + \
                                " WARNING: POSCAR stoich. error\n")

        # Check currently running files to see which ones are complete, what needs resubbed, etc
        hrf.Log(logLoc=LOG_LOC, message=" updating status of " + str(len(nodesCurrRun)) + " nodes...\n")
        toRemove = []
        for node in nodesCurrRun:
            node.UpdateMyStatus()
            if(TESTING):
                node.myStatus = "converged"
            ##Node is finished running, but not converged yet - remove from curr run list, add to needs run list
            if (node.myStatus == "needs resubbed"):
                hrf.Log(logLoc=LOG_LOC,
                        message="  genNum=" + str(node.genNum) + " code=" + str(node.codeStr) + \
                                " needs (re)subbed\n")
                toRemove.append(node)
                nodesNeedRun.append(node)
                continue
            ##Unsure of node's convergence (VASP prob. still running).  Can't do anything yet
            if (node.myStatus == "unsure"):
                continue
            ##Node is finished running and converged - read energy, remove from curr run list, add to fin list
            if (node.myStatus == "converged"):
                hrf.Log(logLoc=LOG_LOC,
                        message="  genNum=" + str(node.genNum) + " code=" + str(node.codeStr) + \
                                " converged\n")
                if (TESTING):
                    node.yAct = uniform(low=-100.0, high=0.0)
                else:
                    node.GetFinEnergy()
                toRemove.append(node)
                nodesFinRun.append(node)
                continue
        for node in toRemove:
            nodesCurrRun.remove(node)

        # Sub any nodes that need run up to allowed number of running jobs
        hrf.Log(logLoc=LOG_LOC, message=" attempting to sub " + str(len(nodesNeedRun)) + " nodes...\n")
        toRemove = []
        for node in nodesNeedRun:
            if (len(nodesCurrRun) >= N_MAX_RUNNING_JOBS):
                hrf.Log(logLoc=LOG_LOC, message="  sub limit reached - breaking\n")
                break

            hrf.Log(logLoc=LOG_LOC, message="  genNum=" + str(node.genNum) + " code=" + str(node.codeStr) + \
                                            " being subbed\n")
            if (TESTING):
                node.nSubs += 1
            else:
                node.SubVaspRun(returnDir=HOME)
            toRemove.append(node)
            nodesCurrRun.append(node)
        for node in toRemove:
            nodesNeedRun.remove(node)

        # Break conditions: there must be no more jobs that need to be run and no more jobs running
        if (len(nodesNeedRun) + len(nodesCurrRun) == 0):
            hrf.Log(logLoc=LOG_LOC, message="finished loop " + str(loopCounter) + "\n")
            break
        # Else take a nap and try again later
        hrf.Log(logLoc=LOG_LOC, message="loop " + str(loopCounter) + " still running.  waiting " + \
                                        str(SLEEP_TIME) + "s\n")
        sleep(SLEEP_TIME)

hrf.Log(logLoc=LOG_LOC, message="---END MIN RUNS---\n")


#-----Final Results-------------------------------------------------------------------------------------------
hrf.Log(logLoc=LOG_LOC, message="---START FINAL RESULTS---\n")
##Dump training data for restarts if necessary
hrf.Log(logLoc=LOG_LOC, message=" writing training data from " + str(len(nodesFinRun)) + " nodes\n")
hrf.WriteNodeData(outfileLoc=TRAIN_DAT_LOC, nodeList=nodesFinRun)
##Dump progress data for restarts if necessary
hrf.Log(logLoc=LOG_LOC, message=" writing progress\n")
lc = "final"
hrf.WriteProgressData(outfileLoc=PROG_DAT_LOC, loopchar=str(lc),
                      availNodes=nodesAvail, finishedNodes=nodesFinRun)

nodesFinRun.sort(key=lambda x: x.yAct)
hrf.WriteNodeData(outfileLoc=RES_LOC, nodeList=nodesFinRun)
hrf.Log(logLoc=LOG_LOC, message="---END FINAL RESULTS---\n")
