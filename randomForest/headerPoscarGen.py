import headerPoscar as hp

#Stuff to not change, usually
ELEMS = ["Ag", "Bi", "Vac", "I"] ##corresponds to how the seed files were written.
MpXZ =  [0./6., 2./6., 4./6.] ##M'X z coords in fractional.  0.0 and 1.0 are the same layer
MppXZ = [1./6., 3./6., 5./6.] ##M''X z coords in fracional.

def AlmEqu(a, b, tol=0.01):
    return abs(a - b) <= tol

#                             vvv
origPoscar = None
mpxArr, mppxArr = [], []
inds = {"mpx1": [], "mpx2": [], "mpx3": [], "mppx1": [], "mppx2": [], "mppx3": []}
#Initializes all of this junk ^^^
def Init(origPoscarLoc, mpxSeedLoc, mppxSeedLoc):
    global origPoscar #why don't I have to use global for m*Arr or inds?  Who fucking knows
    origPoscar = hp.Poscar(origPoscarLoc)

    ##Init mpxArrs
    with open(mpxSeedLoc, 'r') as infile:
        for f in infile:
            arr = [char for char in f if char != "\n"]
            mpxArr.append([int(i) for i in arr])
        infile.close()
    with open(mppxSeedLoc, 'r') as infile:
        for f in infile:
            arr = [char for char in f if char != "\n"]
            mppxArr.append([int(i) for i in arr])
        infile.close()

    ##Init inds
    for n, atom in enumerate(origPoscar.atoms):
        for i in range(0, len(MpXZ)):
            if (AlmEqu(atom.c, MpXZ[i])):
                inds["mpx" + str(i + 1)].append(n)
        for i in range(0, len(MppXZ)):
            if (AlmEqu(atom.c, MppXZ[i])):
                inds["mppx" + str(i + 1)].append(n)
    for va in inds.values():
        if (len(va) != 4):
            print("Error in initializing indices")
            print(inds)
            exit(1)

    return

#Takes a code string (from database) and turns it into the map necessary for turk-style poscar gen
#Currently, code is in the form "mpxI1-mpxI2-mpxI3-mppxI1-mppxI2-mppxI3"
def CodeToGenMap(codeStr):
    return [int(c) for c in codeStr.split('-')]

#Make a POSCAR given only a list of [mpxI1, mpxI2, mpxI3, mppxI1, mppxI2, mppxI3] where *In is the index
#of the nth layer of *
def MakeThisPoscar(newLoc, mxMap):
    newPoscar = hp.deepcopy(origPoscar)

    ##M'X layer substitutions
    for layerInd in range(0, 3):
        thisElemInds = mpxArr[mxMap[layerInd]]
        for i in range(0, 4):  ##4 = num elements per layer
            newPoscar.atoms[inds["mpx" + str(layerInd + 1)][i]].atomType = ELEMS[thisElemInds[i]]
    ##M''X layer substitutions
    for layerInd in range(3, 6):
        thisElemInds = mppxArr[mxMap[layerInd]]
        for i in range(0, 4):  ##4 = num elements per layer
            newPoscar.atoms[inds["mppx" + str(layerInd - 3 + 1)][i]].atomType = ELEMS[thisElemInds[i]]

    ##Remove vacancies, refresh, write, end
    newPoscar.atoms = [atom for atom in newPoscar.atoms if atom.atomType != "Vac"]
    newPoscar.Refresh()
    newPoscar.ChangeAtomOrder(['Ag', 'Bi', 'I'])
    newPoscar.Write(newLoc)

    return
