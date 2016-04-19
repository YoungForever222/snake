# scripts


A personal collection of Python and bash scripts used to process the numerical solution
of simulations run with one of the following code:
* [PetIBM](https://github.com/barbagroup/PetIBM)
* [cuIBM](https://github.com/barbaGroup/cuIBM)
* [IBAMR](https://github.com/IBAMR/IBAMR)
* [OpenFOAM](www.openfoam.com)

To install the package:

  > python setup.py install


Some of the Python scripts call the environment variable `$SCRIPTS`.
The variable can set by adding the following line to your `.bashrc` 
or `.bash_profile` file:

	> export SCRIPTS="/path/to/the/git/repository"


In addition, this repository contains some `resources` such as geometries used 
for the simulations or literature results for comparison.

The directory `styles` provides the matplotlib style-sheet used to plot 
the figures.


Suggestions and bug-fix are welcome.
Contact: `mesnardo@gwu.edu`
