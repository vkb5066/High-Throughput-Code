import re
import os
from shutil import copy
import subprocess
from subprocess import run as externRun

import headerPoscar as hp
import headerPoscarGen as hpg

"""
*-*-*-*-* NODE CLASS DESCRIPTIONS / FUNCTIONS *-*-*-*-*
"""

#Stoichiometry rules
STOICH = {"AgBiI4":  {"Ag": 1, "Bi": 1, 'I': 4}}

#Helper functions
def FileWordCount(infileLoc):
    cnt = 0
    with open(infileLoc, 'r') as infile:
        for li in infile:
            cnt += 1
        infile.close()
    return cnt

#Returns true if OUTCAR has timing info at the end
def CheckOutcarForTime(filePath = "OUTCAR"):
    def Tail(filePath, nLines=10, buff=1028):
        infile = open(filePath, 'r')
        foundLines = []

        blockCnt = -1
        # keep going until there are n lines
        while (len(foundLines) < nLines):
            try:
                infile.seek(blockCnt * buff, os.SEEK_END)
            except IOError:  # in case of small file
                infile.seek(0)
                foundLines = infile.readlines()
                break

            foundLines = infile.readlines()
            blockCnt = blockCnt - 1
        infile.close()

        return foundLines[-nLines:]

    end = Tail(filePath, nLines = 32, buff = 4096)
    for words in end:
        if(re.search("Voluntary context switches", words)):
            return True
    return False


class Node:
    genNum = None
    codeStr = None #string binary representation of generation number

    portion = None #portion of the ml process this node belongs to: (U)nused, (P)rior, (F)inal, str(<loopNum>)
    absPath = None #absolute path to this node

    pbsStatus = None #status (from pbs): (R)unning, (Q)ueue, (S)uspended, (C)ompleted, (D)oes (N)ot (E)xist
    myStatus = None #status (for my code): "needs resubbed", "converged", "unsure"
    nSubs = None #number of times this node has been subbed

    X = None #descriptor -- ALREADY SORTED
    yPred = None #predicted target (energy, eV)
    yAct = None #actual target (energy, eV)

    def __init__(self, genNum, code, path, portion='U', pbsStat="", myStat="needs resubbed", numSubs=0):
        self.genNum = None
        self.codeStr = None
        self.portion = None
        self.absPath = None
        self.pbsStatus = None
        self.myStatus = None
        self.nSubs = None
        self.X = None
        self.yPred = None
        self.yAct = None

        self.genNum = genNum
        self.codeStr = code
        self.portion = portion
        self.absPath = path
        self.pbsStatus = pbsStat
        self.myStatus = myStat
        self.nSubs = numSubs

        return

    def VerifyStoich(self, fileName="POSCAR"):
        if(not os.path.exists(os.path.join(self.absPath, fileName))):
            return False
        thisPos = hp.Poscar(os.path.join(self.absPath, fileName))

        counts = {"Ag": 0, "Bi": 0, 'I': 0}
        for i in range(0, len(thisPos.atoms)):
            if (thisPos.atoms[i].atomType in ["Ag", "Bi", 'I']):
                counts[thisPos.atoms[i].atomType] += 1

        ok = True
        for elem, elemCount in STOICH["AgBiI4"].items():
            if (round(counts[elem] / min(counts.values())) != elemCount):
                ok = False

        return ok

    #Captures output from PBS qstat command to get current job status
    def UpdatePbsStatus(self):
        cmd = "qstat -u vkb5066 | grep RUN_" + str(self.genNum)
        psuLine = externRun(cmd, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')

        #If grep can't locate the running file, it must not exist
        if(psuLine == '' or psuLine == " "):
            self.pbsStatus = "DNE"
            return

        #If we're here, psuLine looks something like this:
        #  vvv garbage                    vvv queue      vvv garbage   vvv mem/node   V stat
        #29542262.torque01.util  vkb5066  open  RUN_671  23433  1   1  9gb  06:00:00  R  00:07:35
        #                 usrnme ^^^            ^^^RUN_genNum   ^^^nodes, ppn ^^^ req. walltime ^^^cur runtime
        self.pbsStatus = str(psuLine.split()[9])
        return

    #Relies on PBS output and some file info to see if this job is converged or not
    def UpdateMyStatus(self):
        self.UpdatePbsStatus()

        #Here, PBS is done with its job - need to decide if it needs resubbed or not
        if(self.pbsStatus == "DNE" or self.pbsStatus == 'C'):
            if(os.path.exists(os.path.join(self.absPath, "OUTCAR"))):
                if(CheckOutcarForTime(os.path.join(self.absPath, "OUTCAR"))):
                    self.myStatus = "converged" ##converged if timing info is written
                    return
            self.myStatus = "needs resubbed" ##no time info or OUTCAR dne - needs (re)subbed regardless
            return

        #Here, PBS is not done with yet (VASP running, job is queued/suspended).  Unsure of final result
        self.myStatus = "unsure"

        return


    #Moves INCAR, KPOINTS, POTCAR, RUN script, to correct directory, generates POSCAR, creates POSCAR0
    def PrepVaspRun(self, incarLoc, kptsLoc, potcarLoc, runLoc):
        if (not os.path.exists(self.absPath)):
            os.makedirs(self.absPath)

        ##remove files if they exist because copy can't overwrite files for some reason
        for file in ["INCAR", "KPOINTS", "POTCAR", "RUN_" + str(self.genNum)]:
            if (os.path.exists(os.path.join(self.absPath, file))):
                os.remove(os.path.join(self.absPath, file))

        copy(incarLoc, os.path.join(self.absPath, "INCAR"))
        copy(kptsLoc, os.path.join(self.absPath, "KPOINTS"))
        copy(potcarLoc, os.path.join(self.absPath, "POTCAR"))
        copy(runLoc, os.path.join(self.absPath, "RUN" + '_' + str(self.genNum)))

        #Don't overwrite existing POSCAR (in case this is a continuation job)
        if(not os.path.exists(os.path.join(self.absPath, "POSCAR"))):
            hpg.MakeThisPoscar(newLoc=os.path.join(self.absPath, "POSCAR"),
                               mxMap=hpg.CodeToGenMap(self.codeStr))

        #Don't overwrite POSCAR0 if it exists
        if((os.path.exists(os.path.join(self.absPath, "POSCAR"))) and
            (not os.path.exists(os.path.join(self.absPath, "POSCAR0")))):
            copy(os.path.join(self.absPath, "POSCAR"), os.path.join(self.absPath, "POSCAR0"))

        return

    #Submits a vasp run, increments this node's sub counter
    def SubVaspRun(self, returnDir, cmd="qsub"):
        os.chdir(self.absPath)

        #In case of resubmission jobs
        if(os.path.exists("CONTCAR")):
            if(FileWordCount("CONTCAR") > 5):
                copy("CONTCAR", "POSCAR")

        externRun(cmd + " RUN_" + str(self.genNum), shell=True)
        self.nSubs = self.nSubs + 1

        os.chdir(returnDir)
        return

    #Initializes a node's X from the databse file's line
    #This may change depending on what descriptors we use
    #Current descriptors: 24 site locations & 6 nearest neighbor counts
    #Current format: gen number, unique identifier, X0, X1, ...
    def InitDesc(self, line, readStartInd=2):
        split = line.split()
        self.X = [int(s) for s in split[readStartInd:]] ##

        return

    #Updates the final energy for this node from the OUTCAR file
    def GetFinEnergy(self):
        with open(os.path.join(self.absPath, "OUTCAR"), 'r') as infile:
            for line in infile:
                if ("TOTEN" in line.split()):
                    self.yAct = float(line.split()[4].replace("eV", ''))
            infile.close()

        return



"""
*-*-*-*-* OTHER FUNCTIONS *-*-*-*-*
"""
#Reads in database
def InitNodelist(dbLoc):
    ret = []
    with open(dbLoc, 'r') as infile:
        for line in infile:
            lin = line.split()
            thisNode = Node(genNum=int(lin[0]), code=lin[1], path="uninitialized")
            thisNode.InitDesc(line=line)
            ret.append(thisNode)
        infile.close()

    return ret

#Writes log message
def Log(logLoc, message):
    with open(logLoc, 'a') as outfile:
        outfile.write(str(message))
        outfile.close()

def Fmt(s, prec=5):
    return f'{float(s):.{prec}f}'
#Write training data to file
def WriteNodeData(outfileLoc, nodeList):
    with open(outfileLoc, 'w') as outfile:
        for node in nodeList:
            toWrite = str(node.genNum) + ' ' + str(node.codeStr)
            for x in node.X:
                toWrite += ' ' + str(x)
            toWrite += ' ' + Fmt(node.yAct) + "\n"

            outfile.write(toWrite)
        outfile.close()

    return

#Write progress to file
def WriteProgressData(outfileLoc, loopchar, availNodes, finishedNodes):
    with open(outfileLoc, 'a') as outfile:
        outfile.write("Progress from loop " + str(loopchar) + "\n")
        outfile.write("Nodes left in search space... (y = yPred)\n")
        for node in availNodes:
            toWrite = str(node.genNum) + ' ' + str(node.codeStr)
            for x in node.X:
                toWrite += ' ' + str(x)
            toWrite += ' ' + Fmt(node.yPred) + "\n"
            outfile.write(toWrite)

        outfile.write("Nodes already evaluated... (y = yAct)\n")
        for node in finishedNodes:
            toWrite = str(node.genNum) + ' ' + str(node.codeStr)
            for x in node.X:
                toWrite += ' ' + str(x)
            toWrite += ' ' + Fmt(node.yAct) + "\n"
            outfile.write(toWrite)

        outfile.close()
    return
