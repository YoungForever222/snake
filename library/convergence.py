# convergence.py
# author: Olivier Mesnard (mesnardo@gwu.edu)
# description: Functions related to a convergence study.


import os

import numpy
from matplotlib import pyplot

from field import Field


def get_exact_solution(simulations, *arguments):
  """Gets the exact solution on the finest grid available.
  If no analytical solution is available, the solution on the finest grid is 
  considered to be exact.

  Parameters
  ----------
  simulations: list of Simulation objects
    Solutions on grids with constant refinement ratio.
  arguments:
    Arguments for the analytical plug-in 
    (arguments of the __init__ method of the class).

  Returns
  -------
  exact: SolutionClass object
    Contains the exact solution.
  """
  finest = simulations.keys()[-1]
  if arguments:
    from solutions.dispatcher import dispatcher
    SolutionClass = dispatcher[arguments[0]]
    # compute analytical solution on finest grid
    exact = SolutionClass(simulations[finest].grid[0],
                          simulations[finest].grid[1],
                          *arguments[1:])
  else:
    # assume finest grid contains exact solution if no analytical solution
    exact = simulations[finest]
    del simulations[finest]
  return exact


def plot_grid_convergence(simulations, exact,
                          mask=None,
                          field_names=None,
                          norms=None,
                          directory=os.getcwd()+'/images', 
                          save_name=None, 
                          show=False):
  """Plots the grid-convergence in a log-log figure.

  Parameters
  ----------
  simulations: list of Simulation objects
    List of the cases to include in the figure.
  exact: Solution or Simulation object
    The exact solution; 
    either the solution on the finest grid or a Solution object.
  mask: Simulation object, optional
    Simulation whose grids are used to restrict the solution;
    default: None.
  field_names: list of strings, optional
    Names of the fields to include in the figure;
    default: None.
  directory: string, optional
    Directory where to save the figure;
    default: <current directory>.
  save_name: string, optional
    Prefix of the name of the .png file to save;
    default: None (does not save).
  show: boolean, optional
    Set 'True' if you want to display the figure; 
    default: False.
  """
  print('[info] plotting the grid convergence ...')
  fig, ax = pyplot.subplots(figsize=(6, 6))
  ax.grid(True, zorder=0)
  ax.set_xlabel('grid-spacing')
  ax.set_ylabel('errors')
  all_grid_spacings, all_errors = [], []
  norm_labels = {'L2': '$L_2$', 'Linf': '$L_\infty$'}
  for field_name in field_names:
    for norm in norms:
      grid_spacings = [case.get_grid_spacing() for case in simulations]
      errors = [case.get_error(exact, field_name, mask=mask, norm=norm) 
                for case in simulations]  
      ax.plot(grid_spacings, errors,
              label='{} - {}-norm'.format(field_name, norm_labels[norm]), 
              marker='o', zorder=10)
      all_grid_spacings += grid_spacings
      all_errors += errors
  ax.legend()
  ax.set_xlim(0.1*min(all_grid_spacings), 10.0*max(all_grid_spacings))
  pyplot.xscale('log')
  pyplot.yscale('log')
  ax.axis('equal')
  # save and display
  if save_name:
    print('[info] saving figure ...')
    if not os.path.isdir(directory):
      print('[info] creating directory: {} ...'.format(directory))
      os.makedirs(directory)
    time_step = getattr(simulations[0], field_names[0].replace('-', '_')).time_step
    pyplot.savefig('{}/{}{:0>7}.png'.format(directory, save_name, time_step))
  if show:
    print('[info] displaying figure ...')
    pyplot.show()


def get_observed_orders(simulations, field_names, mask,
                        directory=os.getcwd(),
                        save_name='observedOrders'):
  """Computes the observed orders of convergence using the solution on three grids
  with constant grid refinement ratio.

  Parameters
  ----------
  simulations: 3-list of Simulation objects
    Contains the simulations.
  field_names: list of strings
    List of field names whose observed order of convergence will be computed.
  mask: Simulation object
    Simulation whose grids are used as a mask to restrict the solutions.
  directory: string, optional
    Shared path of case directories; 
    default: current directory.
  save_name: string, optional
    Prefix of the name of the .dat files to save; 
    default: 'observedOrders'.

  Returns
  -------
  alpha: dictionary of (string, float) items
    Contains the observed order of convergence for each variable asked.
  """
  print('[info] computing observed orders of '
        'convergence using the grids {} ...'
        ''.format([case.description for case in simulations]))
  coarse, medium, fine = simulations
  ratio = coarse.get_grid_spacing()/medium.get_grid_spacing()
  alpha = {} # will contain observed order of convergence
  for field_name in field_names:
    attribute_name = field_name.replace('-', '_')
    grid = [getattr(mask, attribute_name).x, getattr(mask, attribute_name).y]
    alpha[field_name] = get_observed_order(getattr(coarse, attribute_name), 
                                           getattr(medium, attribute_name),
                                           getattr(fine, attribute_name),
                                           ratio,
                                           grid)
    print('\t{}: {}'.format(field_name, alpha[field_name]))
  if save_name:
    print('[info] writing orders into .dat file ...')
    time_step = getattr(mask, attribute_name).time_step
    if not os.path.isdir(directory):
      print('[info] creating directory: {} ...'.format(directory))
      os.makedirs(directory)
    file_path = '{}/{}_{}_{}_{}_{:0>7}.dat'.format(directory, 
                                                   save_name, 
                                                   coarse.description,
                                                   medium.description,
                                                   fine.description, 
                                                   time_step)
    with open(file_path, 'w') as outfile:
      for field_name in field_names:
        outfile.write('{}: {}\n'.format(field_name, alpha[field_name]))
  return alpha


def get_observed_order(coarse, medium, fine, ratio, grid, order=None):
  """Computes the observed order of convergence
  using the solution on three consecutive grids with constant refinement ratio.

  Parameters
  ----------
  coarse, medium, fine: Field objects
    Solutions on three consecutive grids restricted on the coarsest grid.
  ratio: float
    Grid-refinement ratio.
  grid: 2-list of 1d arrays of floats
    Nodal stations in each direction used to restrict a solution.
  order: non-zero integer, inf, -inf, 'fro', 'nuc', optional
    Order of the norm;
    default: None (L2-norm).

  Returns
  -------
  p: float
    The observed order of convergence.
  """
  # restrict coarse solution onto grid
  coarse = coarse.restriction(grid)
  # restrict medium solution onto grid
  medium = medium.restriction(grid)
  # restrict fine solution onto grid
  fine = fine.restriction(grid)
  # observed order of convergence
  p = (  numpy.log(  numpy.linalg.norm(medium.values - coarse.values, ord=order) 
                   / numpy.linalg.norm(fine.values - medium.values, ord=order)  )
       / numpy.log(ratio)  )
  return p


def plot_asymptotic_ranges(simulations, orders, mask, 
                           directory=os.getcwd()+'/images'):
  """Computes and plots the asymptotic range fields 
  using the grid convergence index and given the observed orders of convergence.

  References
  ----------
  [1] http://www.grc.nasa.gov/WWW/wind/valid/tutorial/spatconv.html

  Parameters
  ----------
  simulations: 3-list of Simulation objects.
    The three cases to use.
  orders: dictionary of (string, float) items
    Contains the observed order of convergence of each flow variable considered.
  mask: Simulation  object
    Case whose grids are used to restrict the other (finer) solutions.
  directory: string, optional
    Directory where to save the contours;
    default: <current directory>/images.
  """
  field_names = orders.keys()
  coarse, medium, fine = simulations
  ratio = coarse.get_grid_spacing()/medium.get_grid_spacing()
  for field_name in field_names:
    attribute_name = field_name.replace('-', '_')
    grid = [getattr(mask, attribute_name).x, getattr(mask, attribute_name).y]
    field = get_asymptotic_range(getattr(coarse, attribute_name),
                                 getattr(medium, attribute_name),
                                 getattr(fine, attribute_name),
                                 orders[field_name],
                                 ratio,
                                 grid)
    field.plot_contour(field_range=(0.0, 2.0, 101),
                       view=[coarse.grid[0][0], coarse.grid[1][0],
                             coarse.grid[0][-1], coarse.grid[1][-1]],
                       directory='{}/gci_{}_{}_{}'.format(directory,
                                                          coarse.description,
                                                          medium.description,
                                                          fine.description))


def get_asymptotic_range(coarse, medium, fine, order, ratio, grid):
  """Computes the asymptotic range field using the grid convergence index.

  The three solutions are in the asymptotic range if the field returned contains
  values that are close to 1.0.

  References
  ----------
  [1] http://www.grc.nasa.gov/WWW/wind/valid/tutorial/spatconv.html

  Parameters
  ----------
  coarse, medium, fine: Field objects
    Solutions on coarse, medium, and fine grids.
  order: float
    Observed order of convergence.
  ratio: float
    Grid refinement ratio between the two consecutive grids.
  grid: 2-list of 1d arrays of floats
    Nodal stations in each direction used to restrict the fields.

  Returns
  -------
  asymptotic_range: Field object
    The asymptotic range as a Field.
  """
  gci_23 = get_grid_convergence_index(coarse, medium, order, ratio, grid, Fs=1.25)
  gci_12 = get_grid_convergence_index(medium, fine, order, ratio, grid, Fs=1.25)
  return Field(x=grid[0], y=grid[1],
               values=gci_23.values/(gci_12.values*ratio**order),
               time_step=coarse.time_step,
               label='asymptotic-range-'+coarse.label)


def get_grid_convergence_index(coarse, fine, order, ratio, grid, Fs=1.25):
  """Computes the Grid Convergence Index using the solution obtained on two grids,
  coarse and fine, with a constant grid refinement ratio.

  Choose 3.0 as a safety factor, if only two grids were used to estimate the
  observed order of convergence, and 1.25 if three or more grids were used.

  References
  ----------
  [1] http://www.grc.nasa.gov/WWW/wind/valid/tutorial/spatconv.html

  Parameters
  ----------
  coarse, fine: Field objects
    Solutions on coarse and fine grids.
  order: float
    Observed order of convergence.
  ratio: float
    Grid refinement ratio between the two grids.
  grid: 2-list of 1d arrays of floats
    Nodal stations in each direction used to restrict the fields.
  Fs: float, optional
    Safety factor;
    default: 1.25.

  Returns
  -------
  GCI: Field object
    The Grid Convergence Index (in percentage) as a Field.
  """
  coarse = coarse.restriction(grid)
  fine = fine.restriction(grid)
  # remove small field values to avoid large estimations in the relative difference
  tolerance = 1.0E-06
  mask = numpy.logical_or(numpy.absolute(coarse.values) < tolerance, 
                          numpy.absolute(fine.values) < tolerance)
  coarse.values[mask], fine.values[mask] = None, None
  # compute relative differences
  relative_differences = numpy.absolute((coarse.values-fine.values)/fine.values)
  return Field(x=grid[0], y=grid[1],
               values=Fs*relative_differences/(ratio**order-1.0)*100.0,
               time_step=coarse.time_step,
               label='GCI-'+coarse.label)