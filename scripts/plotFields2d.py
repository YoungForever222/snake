# file: plotFields2d.py
# author: Olivier Mesnard (mesnardo@gwu.edu)
# description: Plots the contour of vorticity at saved time-steps.


import os
import sys
import argparse

sys.path.append(os.environ['SCRIPTS'])
from library import miscellaneous
from library.simulation import Simulation
from library.body import Body


def parse_command_line():
  """Parses the command-line."""
  print('[info] parsing the command-line ...'),
  # create parser
  parser = argparse.ArgumentParser(description='Plots the 2D vorticity, '
                                               'pressure and velocity fields',
                        formatter_class= argparse.ArgumentDefaultsHelpFormatter)
  # fill parser with arguments
  parser.add_argument('--software', dest='software',
                      type=str, choices=['cuibm', 'petibm'],
                      help='software used for the simulation')
  parser.add_argument('--directory', dest='directory', 
                      type=str, default=os.getcwd(), 
                      help='directory of the simulation')
  # arguments about view
  parser.add_argument('--bottom-left', '-bl', dest='bottom_left', 
                      type=float, nargs='+', default=[float('-inf'), float('-inf')],
                      help='coordinates of the bottom-left corner of the view')
  parser.add_argument('--top-right', '-tr', dest='top_right', 
                      type=float, nargs='+', default=[float('inf'), float('inf')],
                      help='coordinates of the top-right corner of the view')
  # arguments about data to plot
  parser.add_argument('--field', dest='field_name',
                      type=str, choices=['vorticity', 'x-velocity', 'y-velocity', 'pressure'],
                      help='name of the fieldto plot')
  parser.add_argument('--range', dest='range',
                      type=float, nargs='+', default=(None, None, None),
                      help='field range to plot (min, max, number of levels)')
  parser.add_argument('--periodic', dest='periodic_directions',
                      type=str, nargs='+', 
                      default=[],
                      help='For PetIBM solutions: list of directions with '
                           'periodic boundary conditions')
  # arguments about the immersed-boundary
  parser.add_argument('--bodies', dest='body_paths', 
                      nargs='+', type=str, default=[],
                      help='path of each body file to add to plots')
  # arguments about time-steps
  parser.add_argument('--time-steps', '-t', dest='time_steps_range', 
                      type=int, nargs='+', default=[],
                      help='time-steps to plot (initial, final, increment)')
  
  parser.add_argument('--subtract-simulation', dest='subtract_simulation',
                      nargs='+', default=[],
                      help='adds another simulation to subtract the field '
                           '(software, directory, binary) '
                           'to subtract fields.')

  # arguments about figure
  parser.add_argument('--save-name', dest='save_name',
                      type=str, default=None,
                      help='prefix used to create the save directory '
                           'and used as a generic file name')
  parser.add_argument('--width', dest='width', 
                      type=float, default=8.0,
                      help='width of the figure (in inches)')
  parser.add_argument('--dpi', dest='dpi', 
                      type=int, default=100,
                      help='dots per inch (resolution of the figure)')
  # parse given options file
  parser.add_argument('--options', 
                      type=open, action=miscellaneous.ReadOptionsFromFile,
                      help='path of the file with options to parse')
  print('done')
  # parse command-line
  return parser.parse_args()


def main():
  """Plots the the velocity, pressure, or vorticity fields at saved time-steps
  for a two-dimensional simulation.
  """
  args = parse_command_line()
  
  simulation = Simulation(directory=args.directory, software=args.software)
  time_steps = simulation.get_time_steps(time_steps_range=args.time_steps_range)
  simulation.read_grid()
  bodies = [Body(path) for path in args.body_paths]

  for time_step in time_steps:
    simulation.read_fields([args.field_name], time_step, 
                           periodic_directions=args.periodic_directions)
    if args.subtract_simulation:
      info = dict(zip(['software', 'directory'], 
                      args.subtract_simulation))
      other = Simulation(**info)
      other.read_grid()
      other.read_fields([args.field_name], time_step, 
                        periodic_directions=args.periodic_directions)
      simulation.subtract(other, args.field_name)

    simulation.plot_contour(args.field_name,
                            field_range=args.range,
                            view=args.bottom_left+args.top_right,
                            bodies=bodies,
                            save_name=args.save_name,
                            width=args.width, 
                            dpi=args.dpi)


if __name__ == '__main__':
  print('\n[{}] START\n'.format(os.path.basename(__file__)))
  main()
  print('\n[{}] END\n'.format(os.path.basename(__file__)))