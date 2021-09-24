# High-Throughput-Code
Code that I've used to create, submit and manage large amounts of VASP runs on Penn State ACI machines.


FileCreation/ and JobManagement/ are a collection of c++, python, and shell scripts.  The c++ code is used to generate a file of seeds that the python scripts read and use to generate unique POSCAR files.  The shell scripts are used to submit and manage VASP jobs on a system using PBS.
 
randomForest/ are generalizations of the above code with the option to apply a random forest model to find minimum energy cells.   
  
  
  
  
  
 
