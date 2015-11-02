#!/usr/bin/env python

# file: plotVorticity.py
# author: Olivier Mesnard (mesnardo@gwu.edu)
# description: Plots the contour of vorticity at saved time-steps.


import os
import sys
import argparse

import numpy
from matplotlib import pyplot, cm

sys.path.append('{}/scripts/cuIBM'.format(os.environ['SCRIPTS']))
import ioCuIBM


def parse_command_line():
  """Parses the command-line."""
  # create parser
  parser = argparse.ArgumentParser(description='Plots the 2D vorticity, '
                                               'pressure and velocity fields',
                        formatter_class= argparse.ArgumentDefaultsHelpFormatter)
  # fill parser with arguments
  parser.add_argument('--directory', dest='case_directory', 
                      type=str, default=os.getcwd(), 
                      help='directory of the simulation')
  parser.add_argument('--binary', dest='binary',
                      action='store_true',
                      help='flag to set if data written in binary format')
  # arguments about view
  parser.add_argument('--bottom-left', '-bl', dest='bottom_left', 
                      type=float, nargs='+', default=[float('-inf'), float('-inf')],
                      help='coordinates of the bottom-left corner of the view')
  parser.add_argument('--top-right', '-tr', dest='top_right', 
                      type=float, nargs='+', default=[float('inf'), float('inf')],
                      help='coordinates of the top-right corner of the view')
  # arguments about data to plot
  parser.add_argument('--velocity', dest='velocity', 
                      action='store_true',
                      help='plots the velocity fields')
  parser.add_argument('--pressure', dest='pressure', 
                      action='store_true',
                      help='plots the pressure field')
  parser.add_argument('--vorticity', dest='vorticity', 
                      action='store_true',
                      help='plots the vorticity field')
  parser.add_argument('--vorticity-range', '-wr', dest='vorticity_range', 
                      type=float, nargs='+', default=[-1.0, 1.0, 11],
                      help='vorticity range (min, max, number of levels)')
  parser.add_argument('--u-range', '-ur', dest='u_range', 
                      type=float, nargs='+', default=[-1.0, 1.0, 11],
                      help='u-velocity range (min, max, number of levels)')
  parser.add_argument('--v-range', '-vr', dest='v_range', 
                      type=float, nargs='+', default=[-1.0, 1.0, 11],
                      help='v-velocity range (min, max, number of levels)')
  parser.add_argument('--pressure-range', '-pr', dest='pressure_range', 
                      type=float, nargs='+', default=[-1.0, 1.0, 11],
                      help='pressure range (min, max, number of levels)')
  # arguments about time-steps
  parser.add_argument('--time-steps', '-t', dest='time_steps', 
                      type=int, nargs='+', default=[],
                      help='time-steps to plot (initial, final, increment)')
  # arguments about figure
  parser.add_argument('--size', dest='size', 
                      type=float, nargs='+', default=[8.0, 8.0],
                      help='size (width and height) of the figure to save (in inches)')
  parser.add_argument('--dpi', dest='dpi', 
                      type=int, default=100,
                      help='dots per inch (resoltion of the figure)')
  # parse given options file
  class LoadFromFile(argparse.Action):
    """Container to read parameters from file."""
    def __call__(self, parser, namespace, values, option_string=None):
      """Fills the namespace with parameters read in file."""
      with values as f:
        parser.parse_args(f.read().split(), namespace)
  parser.add_argument('--file', 
                      type=open, action=LoadFromFile,
                      help='path of the file with options to parse')
  # parse command-line
  return parser.parse_args()


def vorticity(u, v):
  """Computes the vorticity field for a two-dimensional simulation.

  Parameters
  ----------
  u, v: ioCuIBM.Field objects
    u-velocity and v-velocity fields.

  Returns
  -------
  vorticity: ioCuIBM.Field object
    The vorticity field.
  """
  print('\tCompute the vorticity field ...')
  mask_x = numpy.where(numpy.logical_and(u.x > v.x[0], u.x < v.x[-1]))[0]
  mask_y = numpy.where(numpy.logical_and(v.y > u.y[0], v.y < u.y[-1]))[0]
  # vorticity nodes at cell vertices intersection
  xw, yw = 0.5*(v.x[:-1]+v.x[1:]), 0.5*(u.y[:-1]+u.y[1:])
  # compute vorticity
  w = ( (v.values[mask_y, 1:] - v.values[mask_y, :-1])
        / numpy.outer(numpy.ones(yw.size), v.x[1:]-v.x[:-1])
      - (u.values[1:, mask_x] - u.values[:-1, mask_x])
        / numpy.outer(u.y[1:]-u.y[:-1], numpy.ones(xw.size)) )
  return ioPetIBM.Field(x=xw, y=yw, values=w)


def plot_contour(field, field_range, image_path, 
                 view=[float('-inf'), float('-inf'), float('inf'), float('inf')],
                 size=[8.0, 8.0], dpi=100): 
  """Plots and saves the field.

  Parameters
  ----------
  field: ioPetIBM.Field instance
    Nodes and values of the field.
  field_range: list(float)
    Min, max and number of countours to plot.
  image_path: str
    Path of the image to save.
  view: list(float)
    Bottom-left and top-right coordinates of the rectangular view to plot;
    default: the whole domain.
  size: list(float)
    Size (width and height) of the figure to save (in inches); default: [8, 8].
  dpi: int
    Dots per inch (resolution); default: 100
  """
  print('\tPlot the {} contour ...'.format(field.label))
  fig, ax = pyplot.subplots(figsize=(size[0], size[1]), dpi=dpi)
  pyplot.xlabel('$x$')
  pyplot.ylabel('$y$')
  if field_range:
    levels = numpy.linspace(field_range[0], field_range[1], field_range[2])
    colorbar_ticks = numpy.linspace(field_range[0], field_range[1], 5)
  else:
    levels = numpy.linspace(field.values.min(), field.values.max(), 101)
    colorbar_ticks = numpy.linspace(field.values.min(), field.values.max(), 5)
  X, Y = numpy.meshgrid(field.x, field.y)
  color_map = {'pressure': cm.jet, 'vorticity': cm.RdBu_r,
               'u-velocity': cm.RdBu_r, 'v-velocity': cm.RdBu_r}
  cont = ax.contourf(X, Y, field.values, 
                     levels=levels, extend='both', 
                     cmap=color_map[field.label])
  cont_bar = fig.colorbar(cont, label=field.label, 
                          orientation='horizontal', format='%.02f', 
                          ticks=colorbar_ticks)
  x_start, x_end = max(view[0], field.x.min()), min(view[2], field.x.max())
  y_start, y_end = max(view[1], field.y.min()), min(view[3], field.y.max())
  ax.axis([x_start, x_end, y_start, y_end])
  ax.set_aspect('equal')
  pyplot.savefig(image_path, dpi=dpi)
  pyplot.close()


def main():
  """Plots the the velocity, pressure and vorticity fields at saved time-steps
  for a two-dimensional simulation.
  """
  args = parse_command_line()
  print('[case directory] {}'.format(args.case_directory))

  time_steps = ioCuIBM.get_time_steps(args.case_directory, args.time_steps)
 
  # create directory where images will be saved
  images_directory = '{}/images'.format(args.case_directory)
  print('[images directory] {}'.format(images_directory))
  if not os.path.isdir(images_directory):
    os.makedirs(images_directory)

  # read the grid nodes
  coords = ioCuIBM.read_grid(args.case_directory)

  # load default style of matplotlib figures
  pyplot.style.use('{}/styles/mesnardo.mplstyle'.format(os.environ['SCRIPTS']))

  for time_step in time_steps:
    if args.velocity or args.vorticity:
      # get velocity fields
      u, v = ioCuIBM.read_velocity(args.case_directory, time_step, coords, 
                                   binary=args.binary)
      if args.velocity:
        # plot u-velocity field
        image_path = '{}/uVelocity{:0>7}.png'.format(images_directory, time_step)
        plot_contour(u, args.u_range, image_path, 
                     view=args.bottom_left+args.top_right,
                     size=args.size, dpi=args.dpi)
        # plot v-velocity field
        image_path = '{}/vVelocity{:0>7}.png'.format(images_directory, time_step)
        plot_contour(v, args.v_range, image_path, 
                     view=args.bottom_left+args.top_right,
                     size=args.size, dpi=args.dpi)
      if args.vorticity:
        # compute vorticity field
        w = compute_vorticity(u, v)
        # plot vorticity field
        image_path = '{}/vorticity{:0>7}.png'.format(images_directory, time_step)
        plot_contour(w, args.vorticity_range, image_path, 
                     view=args.bottom_left+args.top_right,
                     size=args.size, dpi=args.dpi)
    if args.pressure:
      # get pressure field
      p = ioCuIBM.read_pressure(args.case_directory, time_step, coords)
      # plot pressure field
      image_path = '{}/pressure{:0>7}.png'.format(images_directory, time_step)
      plot_contour(p, args.pressure_range, image_path, 
                   view=args.bottom_left+args.top_right,
                   size=args.size, dpi=args.dpi)


if __name__ == '__main__':
  print('\n[{}] START\n'.format(os.path.basename(__file__)))
  main()
  print('\n[{}] END\n'.format(os.path.basename(__file__)))