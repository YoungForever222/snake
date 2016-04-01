# file: Simulation.py
# author: Olivier Mesnard (mesnardo@gwu.edu)
# description: Information related to a simulation.


import os
import sys

import numpy
from matplotlib import pyplot
import pandas

from .field import Field
from .force import Force


class Simulation(object):
  """Simulation manager."""
  def __init__(self, description=None, directory=os.getcwd(), software=None, **kwargs):
    """Registers the simulations.

    Parameters
    ----------
    description: string
      Description of the simulation; default: None.
    directory: string
      Directory of the simulation; default: current working directory.
    software: string
      Name of the software used for the simulation; default: None.
    **kwargs: dictionary
      Other attributes to create.
    """
    try:
      self.description = description.replace('_', ' ')
    except:
      self.description = description
    self.directory = directory
    self.software = software
    for key, value in kwargs.iteritems():
      setattr(self, key, value)
    self.print_registration()
    self.derive_class()
    self.fields = {}

  def print_registration(self):
    """Prints global details of the simulation"""
    print('[info] registering simulation ...')
    print('\t- directory: {}'.format(self.directory))
    print('\t- description: {}'.format(self.description))
    print('\t- software: {}'.format(self.software))

  def derive_class(self):
    """Finds the appropriate child class based on the software used."""
    if self.software == 'cuibm':
      from .cuIBM.simulation import CuIBMSimulation
      self.__class__ = CuIBMSimulation
    elif self.software == 'petibm':
      from .PetIBM.simulation import PetIBMSimulation
      self.__class__ = PetIBMSimulation
    elif self.software == 'openfoam':
      from .OpenFOAM.simulation import OpenFOAMSimulation
      self.__class__ = OpenFOAMSimulation
    elif self.software == 'ibamr':
      from .IBAMR.simulation import IBAMRSimulation
      self.__class__ = IBAMRSimulation
    else:
      print('[error] software indicated: {}'.format(self.software))
      print('[error] simulation type should be one of the followings: '
            'cuibm, petibm, openfoam, or ibamr')
      sys.exit(0)

  def get_mean_forces(self, limits=[0.0, float('inf')], last_period=False, order=5):
    """Computes the time-averaged forces (or force-coefficients).

    Parameters
    ----------
    limits: list of floats
      Time-limits used to compute the mean; default: [0.0, +inf].
    last_period: bool
      Set 'True' if only the last period define the time-limits; default: False.
    order: int
      Number of neighboring points used to define an extremum; default: 5.

    Returns
    -------
    fx_mean, fy_mean: dict
      Time-limits and mean value for forces in each direction.
    """
    self.fx_mean = self.force_x.get_mean(limits=limits, last_period=last_period, order=order)
    self.fy_mean = self.force_y.get_mean(limits=limits, last_period=last_period, order=order)
    return self.fx_mean, self.fy_mean

  def get_strouhal(self, L=1.0, U=1.0, n_periods=1, end_time=float('inf'), order=5):
    """Computes the Strouhal number based on the frequency of the lift force.

    The frequency is beased on the lift history and is computed using the minima
    of the lift curve.

    Parameters
    ----------
    L: float
      Characteristics length of the body; default: 1.0.
    U: float
      Characteristics velocity of the body; default: 1.0.
    n_periods: integer
      Number of periods (starting from end) to average the Strouhal number; default: 1.
    end_time: float
      Time-limit reference used to average the Strouhal number; default: inf.
    order: integer
      Number of neighbors used on each side to define an extremum; default: 5.

    Returns
    -------
    strouhal: float
      The averaged Strouhal number.
    strouhals: list of floats
      Strouhal numbers used to average.
    """
    minima, _ = self.force_y.get_extrema(order=order)
    mask = numpy.where(self.force_y.times[minima] <= end_time)[0]
    strouhals = L/U/( self.force_y.times[minima[mask[-n_periods:]]] 
                    - self.force_y.times[minima[mask[-n_periods-1:-1]]] )
    self.strouhal = strouhals.mean()
    self.n_periods_strouhal = n_periods
    self.end_time_strouhal = end_time
    return self.strouhal, strouhals

  def plot_forces(self, 
                  display_lift=True, display_drag=True, 
                  display_coefficients=False, coefficient=1.0,
                  limits=[0.0, float('inf'), 0.0, float('inf')],
                  title=None, save_name=None, show=False,
                  display_extrema=False, order=5, display_guides=False, fill_between=False,
                  other_simulations=[], other_coefficients=[]):
    """Displays the forces into a figure.

    Parameters
    ----------
    display_lift: boolean
      Set 'True' if the lift curve should be added to the figure; default: True.
    display_drag: boolean
      Set 'True' if the drag curve should be added to the figure; default: True.
    display_coefficients: boolean
      Set 'True' if plotting force coefficients instead of forces; default: False.
    coefficient: float
      scale coefficient to convert a force in a force coefficient; default: 1.0.
    limits: list of floats
      Limits of the axes [xmin, xmax, ymin, ymax]; default: [0.0, +inf, 0.0, +inf].
    title: string
      Title of the figure; default: None.
    save_name: string
      Name of the .PNG file to save; default: None (does not save).
    show: boolean
      Set 'True' to display the figure; default: False.
    display_extrema: boolean
      Set 'True' to emphasize the extrema of the curves; default: False.
    order: int
      Number of neighbors used on each side to define an extreme; default: 5.
    display_guides: boolean
      Set 'True' to display guides to judge steady regime; default: False.
    fill_between: boolean
      Set 'True' to fill between lines defined by the extrema; default: False.
    other_simulations: list of Simulation objects
      List of other simulations to add to plot; default: [].
    other_coefficients: list of floats
      Scale coefficients for each other simulation; default: [].
    """
    if not (save_name or show):
      return
    print('[info] plotting forces ...')
    pyplot.style.use('{}/styles/mesnardo.mplstyle'.format(os.environ['SCRIPTS']))
    fig, ax = pyplot.subplots(figsize=(8, 6))
    color_cycle = ax._get_lines.prop_cycler
    ax.grid(True, zorder=0)
    ax.set_xlabel('time')
    ax.set_ylabel('force coefficients' if display_coefficients else 'forces')
    forces_to_plot, info = [], []
    if display_drag:
      forces_to_plot.append(self.force_x)
      info.append('$C_d$' if display_coefficients else '$F_x$')
    if display_lift:
      forces_to_plot.append(self.force_y)
      info.append('$C_l$' if display_coefficients else '$F_y$')
    for index, force in enumerate(forces_to_plot):
      color = next(color_cycle)['color']
      line, = ax.plot(force.times, coefficient*force.values,
              label=' - '.join(filter(None, [self.description, info[index]])),
              color=color, linestyle='-', zorder=9)
      if display_extrema:
        minima, maxima = force.get_extrema(order=order)
        ax.scatter(force.times[minima], coefficient*force.values[minima],
                   c=color, marker='o', zorder=10)
        ax.scatter(force.times[maxima], coefficient*force.values[maxima],
                   c=color, marker='o', zorder=10)
        if fill_between:
          line.remove()
          ax.plot(force.times[minima], coefficient*force.values[minima],
                  color='white', linestyle='-', zorder=9)
          ax.plot(force.times[maxima], coefficient*force.values[maxima],
                  color='white', linestyle='-', zorder=9)
          times = numpy.concatenate((force.times[minima], 
                                     force.times[maxima][::-1]))
          values = coefficient*numpy.concatenate((force.values[minima], 
                                                  force.values[maxima][::-1]))
          ax.fill(times, values, 
                  label=' - '.join(filter(None, [self.description, info[index]])),
                  facecolor=color, alpha=0.8, zorder=8)
        if display_guides:
          ax.axhline(coefficient*force.values[minima[-1]],
                     color=color, linestyle=':', zorder=10)
          ax.axhline(coefficient*force.values[maxima[-1]],
                     color=color, linestyle=':', zorder=10)
    for i, simulation in enumerate(other_simulations):
      forces_to_plot = []
      if display_drag:
        forces_to_plot.append(simulation.force_x)
      if display_lift:
        forces_to_plot.append(simulation.force_y)
      for index, force in enumerate(forces_to_plot):
        color = next(color_cycle)['color']
        line, = ax.plot(force.times, other_coefficients[i]*force.values,
                        label=' - '.join(filter(None, [simulation.description, info[index]])),
                        color=color, linestyle='--', zorder=9)
        if fill_between:
          line.remove()
          minima, maxima = force.get_extrema(order=order)
          ax.scatter(force.times[minima], other_coefficients[i]*force.values[minima],
                     c=color, marker='o', zorder=10)
          ax.scatter(force.times[maxima], other_coefficients[i]*force.values[maxima],
                     c=color, marker='o', zorder=10)
          ax.plot(force.times[minima], other_coefficients[i]*force.values[minima],
                  color='white', linestyle='-', zorder=9)
          ax.plot(force.times[maxima], other_coefficients[i]*force.values[maxima],
                  color='white', linestyle='-', zorder=9)
          times = numpy.concatenate((force.times[minima], 
                                     force.times[maxima][::-1]))
          values = other_coefficients[index]*numpy.concatenate((force.values[minima], 
                                                                force.values[maxima][::-1]))
          ax.fill(times, values, 
                  label=' - '.join(filter(None, [simulation.description, info[index]])),
                  facecolor=color, alpha=0.5, zorder=7)

    legend = ax.legend()
    legend.set_zorder(20) # put legend on top
    ax.axis(limits)
    if title:
      ax.title(title)
    if save_name:
      images_directory = '{}/images'.format(self.directory)
      print('[info] saving figure {}.png in directory {} ...'.format(save_name, images_directory))
      if not os.path.isdir(images_directory):
        os.makedirs(images_directory)
      pyplot.savefig('{}/{}.png'.format(images_directory, save_name))
    if show:
      print('[info] displaying figure ...')
      pyplot.show()
    pyplot.close()

  def create_dataframe_forces(self, 
                              display_coefficients=False, coefficient=1.0,
                              other_simulations=[], other_coefficients=[]):
    """Creates a data frame with Pandas to display 
    time-averaged forces (or force coefficients).

    Parameters
    ----------
    display_coefficients: boolean
      Set 'True' if force coefficients are to be displayed; default: False.
    coefficient: float
      Scale factor to convert a force into a force-coefficient; default: 1.0.
    other_simulations: list of Simulation objects
      List of other simulations used for comparison; default: [].
    other_coefficients: list of floats
      List of scale factors of other simulations; default: [].

    Returns
    -------
    dataframe: Pandas dataframe
      The dataframe of the simulation.
    """
    print('[info] instantaneous signals are averaged between '
          '{} and {} time-units.'.format(self.fx_mean['start'], 
                                         self.fx_mean['end']))
    dataframe = pandas.DataFrame([['{0:.4f}'.format(coefficient*self.fx_mean['value']),
                                   '{0:.4f}'.format(coefficient*self.fy_mean['value'])]],
                                 index=['<no description>' if not self.description else self.description],
                                 columns=[('<Cd>' if display_coefficients else '<Fx>'),
                                          ('<Cl>' if display_coefficients else '<Fy>')])
    try:
      print('[info] Strouhal number is averaged '
            'over the last {} oscillations of the lift curve '
            'ending at {} time-units.'.format(int(self.n_periods_strouhal),
                                              self.end_time_strouhal))
      dataframe['<St>'] = '{0:.4f}'.format(self.strouhal)
    except:
      pass
    for index, simulation in enumerate(other_simulations):
      dataframe = dataframe.append(simulation.create_dataframe_forces(display_coefficients=display_coefficients,
                                                                      coefficient=other_coefficients[index]))
    return dataframe


class BarbaGroupSimulation(object):
  def __init__(self):
    self.fields = {}

  def create_uniform_grid(self, bottom_left=[], top_right=[], n_cells=[]):
    """Creates a uniform Cartesian grid.

    Parameters
    ----------
    bottom_left: list of floats, optional
      Coordinates of the bottom-left corner;
      default: []
    top_right: list of floats, optional
      Coordinates of the top-right corner;
      default: []
    n_cells: list of integers, optional
      Number of cells in each direction;
      default: []
    """
    print('[info] creating a uniform Cartesian grid ...'),
    assert len(bottom_left) == len(n_cells)
    assert len(top_right) == len(n_cells)
    self.grid = []
    for i, n in enumerate(n_cells):
      self.grid.append(numpy.linspace(bottom_left[i], top_right[i], n+1,
                                      dtype=numpy.float64))
    print('done')

  def get_time_steps(self, time_steps_range=None):
    """Returns a list of the time-steps to post-process.

    Parameters
    ----------
    time_steps_range: 3-list of integers, optional
      Initial, final and stride of the time-steps to consider;
      default: None (all saved time-steps).
    """
    if time_steps_range:
      return range(time_steps_range[0],
                   time_steps_range[1]+1,
                   time_steps_range[2])
    else:
      return sorted(int(folder) for folder in os.listdir(self.directory)
                                if folder[0] == '0')

  def get_grid_spacing(self):
    """Returns the grid-spacing of a uniform grid."""
    return (self.grid[0][-1]-self.grid[0][0])/(self.grid[0].size-1)

  def read_fields(self, field_names, time_step, 
                  periodic_directions=[]):
    """Gets the field at a given time-step. 

    Parameters
    ----------
    field_names: list of strings
      Name of the fields to get; 
      choices: 'pressure', 'vorticity', 
               'x-velocity', 'y-velocity', 
               'x-flux', 'y-flux'.
    time_step: integer
      Time-step at which the solution is read.
    periodic_directions: list of strings
      Directions that uses periodic boundary conditions; 
      choices: 'x', 'y', 'z',
      default: [].
    """
    if 'pressure' in field_names:
      self.fields['pressure'] = self.read_pressure(time_step)
    if any(name in ['x-flux', 'y-flux'] for name in field_names):
      self.fields['x-flux'], self.fields['y-flux'] = self.read_fluxes(time_step, 
                                         periodic_directions=periodic_directions)
    if any(name in ['x-velocity', 'y-velocity'] for name in field_names):
      self.fields['x-velocity'], self.fields['y-velocity'] = self.get_velocity(time_step, 
                                                 periodic_directions=periodic_directions)
    if 'vorticity' in field_names:
      self.read_velocity(time_step, 
                         periodic_directions=periodic_directions)
      self.compute_vorticity()

  def compute_vorticity(self):
    """Computes the vorticity field for a two-dimensional simulation.

    Parameters
    ----------
    time_step: integer
      Time-step at which to read the velocity fields.
    """
    time_step = self.x_velocity.time_step
    print('[time-step {}] computing the vorticity field ...'.format(time_step)),
    u, v = self.x_velocity, self.y_velocity
    mask_x = numpy.where(numpy.logical_and(u.x > v.x[0], u.x < v.x[-1]))[0]
    mask_y = numpy.where(numpy.logical_and(v.y > u.y[0], v.y < u.y[-1]))[0]
    # vorticity nodes at cell vertices intersection
    xw, yw = 0.5*(v.x[:-1]+v.x[1:]), 0.5*(u.y[:-1]+u.y[1:])
    # compute vorticity
    w = ( (v.values[mask_y, 1:] - v.values[mask_y, :-1])
          / numpy.outer(numpy.ones(yw.size), v.x[1:]-v.x[:-1])
        - (u.values[1:, mask_x] - u.values[:-1, mask_x])
          / numpy.outer(u.y[1:]-u.y[:-1], numpy.ones(xw.size)) )
    self.vorticity = Field(x=xw, y=yw, values=w, 
                           time_step=time_step, label='vorticity')
    print('done')

  def get_velocity(self, time_step, periodic_directions=[]):
    """Gets the velocity fields at a given time-step.

    We first read the fluxes from file, then convert into velocity-components.
    """
    print('[time-step {}] get velocity fields ...'.format(time_step))
    fluxes = self.read_fluxes(time_step, periodic_directions=periodic_directions)
    dim3 = (len(self.grid) == 3)
    # get stations, cell-widths, and number of cells in x- and y-directions
    x, y = self.grid[:2]
    dx, dy = x[1:]-x[:-1], y[1:]-y[:-1]
    nx, ny = dx.size, dy.size
    if dim3:
      # get stations, cell-widths, and number of cells in z-direction
      z = self.grid[2]
      dz = z[1:]-z[:-1]
      nz = dz.size
    if dim3:
      ux = numpy.empty_like(fluxes[0].values, dtype=numpy.float64)
      for k in xrange(fluxes[0].shape[0]):
        for j in xrange(fluxes[0].shape[1]):
          for i in xrange(fluxes[0].shape[2]):
            ux[k, j, i] = fluxes[0].values[k, j, i]/dy[j]/dz[k]
      ux = Field(label='x-velocity',
                 time_step=time_step,
                 x=fluxes[0].x, y=fluxes[0].y, z=fluxes[0].z,
                 values=ux)
      uy = numpy.empty_like(fluxes[1].values, dtype=numpy.float64)
      for k in xrange(fluxes[1].shape[0]):
        for j in xrange(fluxes[1].shape[1]):
          for i in xrange(fluxes[1].shape[2]):
            uy[k, j, i] = fluxes[1].values[k, j, i]/dx[i]/dz[k]
      uy = Field(label='y-velocity',
                 time_step=time_step, 
                 x=fluxes[1].x, y=fluxes[1].y, z=fluxes[1].z,
                 values=uy)
      uz = numpy.empty_like(fluxes[2].values, dtype=numpy.float64)
      for k in xrange(fluxes[2].shape[0]):
        for j in xrange(fluxes[2].shape[1]):
          for i in xrange(fluxes[2].shape[2]):
            uz[k, j, i] = fluxes[2].values[k, j, i]/dx[i]/dy[j]
      uz = Field(label='z-velocity',
                 time_step=time_step,
                 x=fluxes[2].x, y=fluxes[2].y, z=fluxes[2].z,
                 values=uz)
      return ux, uy, uz
    else:
      ux = numpy.empty_like(fluxes[0].values, dtype=numpy.float64)
      for i in xrange(fluxes[0].values.shape[1]):
        ux[:, i] = fluxes[0].values[:, i]/dy[:]
      ux = Field(label='x-velocity',
                 time_step=time_step,
                 x=fluxes[0].x, y=fluxes[0].y,
                 values=ux)
      uy = numpy.empty_like(fluxes[1].values, dtype=numpy.float64)
      for j in xrange(fluxes[1].values.shape[0]):
        uy[j, :] = fluxes[1].values[j, :]/dx[:]
      uy = Field(label='y-velocity',
                 time_step=time_step,
                 x=fluxes[1].x, y=fluxes[1].y,
                 values=uy)
      return ux, uy

  def subtract(self, other, field_name, label=None):
    """Subtract one field to another in place.

    Parameters
    ----------
    other: Simulation object
      Simulation to subtract.
    field_name: string
      Name of the field to subtract; 
      choices: 'pressure', 'vorticity', 'x-velocity', 'y-velocity', 'x-flux', 'y-flux'.
    label: string, optional
      Name of the output subtracted field;
      default: None (will be <current name>+'-subtracted')
    """
    if not label:
      label = field_name+'-subtracted'
    self.fields[label] = self.fields[field_name].subtract(other.fields[field_name],
                                                          label=label)

  def get_difference(self, exact, name, mask=None, norm=None):
    """Returns the difference between a field and an exact solution.

    Parameters
    ----------
    exact: Simulation object
      The exact solution.
    name: string
      Name of the field to use.
    mask: Simulation object
      Simulation whose staggered grid arrangement is used to restrict the solutions;
      default: None.
    norm: string
      Norm to use to compute the difference;
      default: None.

    Returns
    -------
    error: float
      The difference between the two fields.
    """
    if mask:
      mask_field = mask.fields[name]
    return self.fields[name].get_difference(exact.fields[name],
                                            mask=mask_field, 
                                            norm=norm)

  def get_relative_differences(self, exact, mask, field_names=[]):
    """Computes the relative differences between a list of simulations 
    and an analytical solution for a given list of fields.

    Parameters
    ----------
    exact: Analytical object
      The analytical solution.
    mask: Simulation object
      Simulation whose grid is used as a mask.
    field_names: list of strings
      The fields for which the relative error is computed; default: [].

    Returns
    -------
    errors: dictionary of (string, float) items
      Relative difference for each field indicated.
    """
    errors = {}
    for name in field_names:
      field_name = field_name.replace('-', '_')
      field = getattr(self, field_name)
      exact_field = getattr(exact, field_name)
      grid = [mask.fields[name].x, mask.fields[name].y]
      errors[name] = self.fields[name].get_relative_difference(exact.fields[name], 
                                                               grid)
    self.errors = errors
    return errors

  def plot_contour(self, field_name, 
                   field_range=None,
                   filled_contour=True, 
                   view=[float('-inf'), float('-inf'), float('inf'), float('inf')],
                   bodies=[],
                   save_name=None, 
                   width=8.0, 
                   dpi=100): 
    """Plots and saves the field.

    Parameters
    ----------
    field_name: string
      Name of the field.
    field_range: list of floats
      Min, max and number of contours to plot; default: None.
    filled_contour: boolean
      Set 'True' to create a filled contour;
      default: True.
    view: list of floats
      Bottom-left and top-right coordinates of the rectangular view to plot;
      default: the whole domain.
    bodies: list of Body objects
      The immersed bodies to add to the figure; default: [] (no immersed body).
    save_name: string
      Prefix used to create the images directory and to save the .png files; default: None.
    width: float
      Width of the figure (in inches); default: 8.
    dpi: int
      Dots per inch (resolution); default: 100
    """
    # get view
    view[0] = (self.grid[0].min() if view[0] == float('-inf') else view[0])
    view[1] = (self.grid[1].min() if view[1] == float('-inf') else view[1])
    view[2] = (self.grid[0].max() if view[2] == float('inf') else view[2])
    view[3] = (self.grid[1].max() if view[3] == float('inf') else view[3])
    self.fields[field_name].plot_contour(directory='{}/images'.format(self.directory),
                                         field_range=field_range,
                                         filled_contour=filled_contour,
                                         view=view,
                                         bodies=bodies,
                                         save_name=save_name,
                                         width=width,
                                         dpi=dpi)

  def plot_gridline_values(self, field_name, 
                           x=[], y=[], 
                           boundaries=(None, None),
                           plot_settings={},
                           plot_limits=(None, None, None, None),
                           save_directory=None,
                           show=False,
                           validation_data=None,
                           validation_plot_settings={}):
    """Plots the field values along either a set of vertical gridlines or a set
    of horizontal gridlines.

    Parameters
    ----------
    field_name: string
      Name of the field to plot.
    x: list of floats, optional
      List of vertical gridlines defined by their x-position;
      default: [].
    y: list of floats, optional
      List of horizontal gridlines defined by their y-position;
      default: [].
    boundaries: 2-tuple of floats, optional
      Gridline boundaries;
      default: (None, None).
    plot_settings: dictionary of (string, object) items, optional
      Contains optional arguments to call pyplot.plot function 
      for the gridline data;
      default: empty dictionary.
    plot_limits: 4-tuple of floats, optional
      Limits of the plot (x-start, x-end, y-start, y-end);
      default: (None, None, None, None)
    save_directory: string, optional
      Directory where to save the figure;
      default: None (does not save).
    show: boolean, optional
      Set 'True' if you want to display the figure;
      default: False.
    validation_data: 2-tuple of 1d arrays of floats, optional
      Validation data to add to the figure (1st array contains the y-stations,
      2nd array contains the values at the stations);
      default: None.
    validation_plot_settings: dictionary of (string, object) items, optional
      Contains optional arguments to call pyplot.plot function 
      for the validation data;
      default: empty dictionary.
    """
    if not isinstance(x, (list, tuple)):
      x = [x]
    if not isinstance(y, (list, tuple)):
      y = [y]
    if not (x or y):
      print('[error] provide either x or y keyword arguments')
      return
    if x:
      self.fields[field_name].plot_vertical_gridline_values(x=x, 
                              boundaries=boundaries,
                              plot_settings=plot_settings,
                              save_directory=save_directory,
                              show=show,
                              validation_data=validation_data,
                              validation_plot_settings=validation_plot_settings)
    if y:
      self.fields[field_name].plot_horizontal_gridline_values(y=y, 
                              boundaries=boundaries,
                              plot_settings=plot_settings,
                              save_directory=save_directory,
                              show=show,
                              validation_data=validation_data,
                              validation_plot_settings=validation_plot_settings)

  def get_velocity_cell_centers(self):
    """Interpolates the staggered velocity field to the cell-centers of the mesh."""
    dim3 = 'z-velocity' in self.fields.keys()
    x_centers = self.fields['y-velocity'].x[1:-1] 
    y_centers = self.fields['x-velocity'].y[1:-1]
    u, v = self.fields['x-velocity'].values, self.fields['y-velocity'].values
    if dim3:
      z_centers = self.fields['x-velocity'].z[1:-1]
      w = self.fields['z-velocity'].values
      u = 0.5*(u[1:-1, 1:-1, :-1] + u[1:-1, 1:-1, 1:])
      v = 0.5*(v[1:-1, :-1, 1:-1] + v[1:-1:, 1:, 1:-1])
      w = 0.5*(w[:-1, 1:-1, 1:-1] + w[1:, 1:-1, 1:-1])
      # tests
      assert (z_centers.size, y_centers.size, x_centers.size) == u.shape
      assert (z_centers.size, y_centers.size, x_centers.size) == v.shape
      assert (z_centers.size, y_centers.size, x_centers.size) == w.shape
      u = Field(label='x-velocity', 
                time_step=self.fields['x-velocity'].time_step, 
                x=x_centers, y=y_centers, z=z_centers, 
                values=u)
      v = Field(label='y-velocity', 
                time_step=self.fields['y-velocity'].time_step, 
                x=x_centers, y=y_centers, z=z_centers, 
                values=v)
      w = Field(label='z-velocity', 
                time_step=self.fields['z-velocity'].time_step, 
                x=x_centers, y=y_centers, z=z_centers, 
                values=w)
      return u, v, w
    else:
      u = 0.5*(u[1:-1, :-1] + u[1:-1, 1:])
      v = 0.5*(v[:-1, 1:-1] + v[1:, 1:-1])
      # tests
      assert (y_centers.size, x_centers.size) == u.shape
      assert (y_centers.size, x_centers.size) == v.shape
      u = Field(label='x-velocity', 
                time_step=self.fields['x-velocity'].time_step, 
                x=x_centers, y=y_centers, 
                values=u)
      u = Field(label='y-velocity', 
                time_step=self.fields['y-velocity'].time_step, 
                x=x_centers, y=y_centers, 
                values=v)
      return u, v

  def write_vtk(self, field_name, time_step, 
                view=[[float('-inf'), float('-inf'), float('-inf')], 
                      [float('inf'), float('inf'), float('inf')]],
                stride=1):
    """Writes the field in a .vtk file.

    Parameters
    ----------
    field_names: list of strings
      Name of the field to write; choices: 'velocity', 'pressure'.
    time_step: integer
      Time-step to write.
    view: list of floats
      Bottom-left and top-right coordinates of the rectangular view to write;
      default: the whole domain.
    stride: integer
      Stride at which the field is written; default: 1.
    """
    print('[info] writing the {} field into .vtk file ...'.format(field_name))
    dim3 = (len(self.grid) == 3)
    if field_name == 'velocity':
      scalar_field = False
      field = [self.fields['x-velocity'], self.fields['y-velocity']]
      if dim3:
        field.append(self.fields['z-velocity'])
    elif field_name == 'pressure':
      scalar_field = True
      field = [self.fields['pressure']]
    # get mask for the view
    mx = numpy.where(numpy.logical_and(field[0].x > view[0][0],
                                       field[0].x < view[1][0]))[0][::stride]
    my = numpy.where(numpy.logical_and(field[0].y > view[0][1],
                                       field[0].y < view[1][1]))[0][::stride]
    if dim3:
      mz = numpy.where(numpy.logical_and(field[0].z > view[0][2],
                                         field[0].z < view[1][2]))[0][::stride]
    # create directory where .vtk file will be saved
    vtk_directory = '{}/vtk_files/{}'.format(case_directory, field_name)
    if not os.path.isdir(vtk_directory):
      print('[info] creating directory: {}'.format(vtk_directory))
      os.makedirs(vtk_directory)
    vtk_file_path = '{}/{}{:0>7}.vtk'.format(vtk_directory, field_name, time_step)
    # get coordinates within the view
    x = field[0].x[mx]
    y = field[0].y[my]
    z = (None if not dim3 else field[0].z[mz])
    nx, ny, nz = x.size, y.size, (1 if not dim3 else z.size)
    # write .vtk file
    with open(vtk_file_path, 'w') as outfile:
      outfile.write('# vtk DataFile Version 3.0\n')
      outfile.write('contains {} field\n'.format(name))
      outfile.write('ASCII\n')
      outfile.write('DATASET RECTILINEAR_GRID\n')
      outfile.write('DIMENSIONS {} {} {}\n'.format(nx, ny, nz))
      outfile.write('X_COORDINATES {} double\n'.format(nx))
      numpy.savetxt(outfile, x, fmt='%f')
      outfile.write('Y_COORDINATES {} double\n'.format(ny))
      numpy.savetxt(outfile, y, fmt='%f')
      outfile.write('Z_COORDINATES {} double\n'.format(nz))
      if dim3:
        numpy.savetxt(outfile, z, fmt='%f')
      else:
        outfile.write('0.0\n')
      outfile.write('POINT_DATA {}\n'.format(nx*ny*nz))
      if scalar_field:
        outfile.write('\nSCALARS {} double 1\nLOOKUP_TABLE default\n'.format(name))
        if dim3:
          values = field[0].values[mz[0]:mz[-1]+1, 
                                   my[0]:my[-1]+1, 
                                   mx[0]:mx[-1]+1]
        else:
          values = field[0].values[my[0]:my[-1]+1, 
                                   mx[0]:mx[-1]+1]
        numpy.savetxt(outfile, values.flatten(), 
                      fmt='%.6f', delimiter='\t')
      else:
        outfile.write('\nVECTORS {} double\n'.format(name))
        if dim3:
          values_x = field[0].values[mz[0]:mz[-1]+1, 
                                     my[0]:my[-1]+1, 
                                     mx[0]:mx[-1]+1]
          values_y = field[1].values[mz[0]:mz[-1]+1, 
                                     my[0]:my[-1]+1, 
                                     mx[0]:mx[-1]+1]
          values_z = field[2].values[mz[0]:mz[-1]+1, 
                                     my[0]:my[-1]+1, 
                                     mx[0]:mx[-1]+1]
          numpy.savetxt(outfile, 
                        numpy.c_[values_x.flatten(), 
                                 values_y.flatten(), 
                                 values_z.flatten()],
                        fmt='%.6f', delimiter='\t')
        else:
          values_x = field[0].values[my[0]:my[-1]+1, 
                                        mx[0]:mx[-1]+1]
          values_y = field[1].values[my[0]:my[-1]+1, 
                                        mx[0]:mx[-1]+1]
          numpy.savetxt(outfile, numpy.c_[values_x.flatten(),
                                          values_y.flatten()],
                        fmt='%6f', delimiter='\t')