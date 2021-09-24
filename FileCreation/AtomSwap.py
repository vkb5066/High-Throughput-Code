#!/usr/bin/env python3.6
import Poscar
import os

origPoscar = Poscar.Poscar("agbii4Seed")

         #0     1
elems = ['Ag', 'Bi']
idsToSwap = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]


with open ("seeds", 'r') as infile:
    #For each "word" in the permutation file
    count = 0
    for f in infile:
        #Create a list of split digits (and exclude the newline character at the end)
        arr = [char for char in f][0:-1]
        arr = [int(i) for i in arr]
        #Create a new POSCAR instance
        newPoscar = Poscar.deepcopy(origPoscar)
        newPoscar.comment = "Generation Seed Number " + str(count)
        #The index of the split digits array corresponds to the ID of the atom to swap,
        #and the value at that location in the array tells what atom to swap it with
        for i in range (0, len(arr)):
            newPoscar.atoms[idsToSwap[i] - 1].atomType = elems[arr[i]]
        #Refresh the atom counts (not needed here) and the atom locations (needed here)
        newPoscar.Refresh()
        #Make sure the elements are in order Ag, Bi, I
        newPoscar.ChangeAtomOrder(['Ag', 'Bi', 'I'])
        #The sum of the first half of the intigers in the array determine the number of swaps,
        #so I can decide where to place the files based off of this
        os.mkdir("all//" + str(count))
        newPoscar.Write("all//" + str(count) + "//POSCAR")
        count = count + 1
