#!/usr/bin/env python

# file: generateGrid.py
# author: Anush Krishnan (anush@bu.edu), Olivier Mesnard (mesnardo@gwu.edu)
# description: Generates the cartesianMesh.yaml file for stretched grids.


import argparse
import sys
import os
import re
import math


def read_inputs():
  """Parses the command-line."""
  # create parser
  parser = argparse.ArgumentParser(description='Generates cartesianMesh.yaml '
                                               'file for a uniform region '
                                               'surrounded by a stretched grid',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  # fill parser with arguments
  parser.add_argument('--parameters', dest='parameters_path', type=str, 
                      default=os.path.dirname(os.path.realpath(__file__))+'/gridParameters',
                      help='path of the file containing grid parameters')
  parser.add_argument('--case', dest='case_directory', type=str,
                      default=os.getcwd(),
                      help='directory of the simulation')
  parser.add_argument('--precision', dest='precision', type=int, default=2,
                      help='precision of the aspect ratio computed')
  # parse command-line
  return parser.parse_args()


def read_parameters_file(parameters):
  """Creates a database with all grid parameters read from file.

  Parameters
  ----------
  parameters: Namespace
    Database with command-line arguments.

  Returns
  -------
  database: dict
    Database as a dictionary.
  """
  database = {'file_path': parameters.parameters_path,
              'case_directory': parameters.case_directory,
              'precision': parameters.precision}
  with open(database['file_path'], 'r') as infile:
    lines = filter(None, (line.rstrip() for line in infile if not line.startswith('#')))
    for line in lines:
      line = filter(None, re.split('\[|\]|\n|:|,|\s+', line))
      direction, values = line[0], [float(value) for value in line[1:]]
      database[direction] = {'min': values[0],
                             'min uniform': values[1],
                             'max uniform': values[2],
                             'max': values[3],
                             'spacing': values[4],
                             'aspect ratio': [values[5], values[6]]}
  return database


def get_ratios(database):
  """Computes stretching ratio and number of cells 
  in each direction for each subdomain.

  Parameters
  ----------
  database: dict
    Dictionary containing the grid parameters.
  """
  compute_ratio('x', database)
  compute_ratio('y', database)
  try:
    compute_ratio('z', database)
  except:
    pass


def compute_ratio(direction, database):
  """Computes the aspect ratio for each sub-domain.

  Parameters
  ----------
  direction: str
    Direction name ('x', 'y' or 'z').
  database: dict
    Dictionary with the grid parameters.
  """
  def compute_stretched_ratio():
    """Computes the stretching ratio and number of cells."""
    precision = database['precision']
    current_precision = 1
    next_ratio = 2.0
    while current_precision <= precision:
      r = next_ratio
      n = int(round(math.log(1.0 - l/h*(1.0-r))/math.log(r)))
      ar = r**(n-1)
      if ar < max_ar:
        next_ratio += (0.1)**current_precision
        current_precision += 1
      else:
        next_ratio -= (0.1)**current_precision
    return r, n
  
  h = database[direction]['spacing']

  # before uniform region
  l = database[direction]['min uniform'] - database[direction]['min']
  max_ar = database[direction]['aspect ratio'][0]
  r, n = compute_stretched_ratio()
  database[direction]['stretch1'] = {'end': database[direction]['min uniform'], 
                                     'stretching ratio': 1.0/r, 
                                     'number cells': n}

  # uniform region
  l = database[direction]['max uniform']-database[direction]['min uniform']
  n = int(round(l/h))
  if abs(n-l/h) > 1.0E-08:
    print('Choose a mesh spacing such that the uniform region is an '
          'integral multiple of it')
    print('{}-direction: length l={} \t spacing h={} \t l/h={}'.format(direction, 
                                                                       l, h, l/h))
    sys.exit()
  database[direction]['uniform'] = {'end': database[direction]['max uniform'], 
                                    'stretching ratio': 1.0, 
                                    'number cells': n}

  # after uniform region
  l = database[direction]['max'] - database[direction]['max uniform']
  max_ar = database[direction]['aspect ratio'][1]
  r, n = compute_stretched_ratio()
  database[direction]['stretch2'] = {'end': database[direction]['max'], 
                                     'stretching ratio': r, 
                                     'number cells': n}


def write_yaml_file(database):
  """Writes the file cartesianMesh.yaml into the case directory.

  Parameters
  ----------
  database: dict
    Dictionary with all grid parameters.
  """
  file_path = '{}/cartesianMesh.yaml'.format(database['case_directory'])
  with open(file_path, 'w') as outfile:
    directions = [d for d in ['x', 'y', 'z'] if d in list(database.keys())]
    for direction in directions:
      outfile.write('- direction: {}\n'.format(direction))
      outfile.write('  start: {}\n'.format(database[direction]['min']))
      outfile.write('  subDomains:\n')
      for region in ['stretch1', 'uniform', 'stretch2']: 
        outfile.write('    - end: {}\n'.format(database[direction][region]['end']))
        outfile.write('      cells: {}\n'.format(database[direction][region]['number cells']))
        outfile.write('      stretchRatio: {}\n'.format(database[direction][region]['stretching ratio']))
      outfile.write('\n')
  print('cartesianMesh.yaml written into {}'.format(database['case_directory']))


def main():
  """Creates cartesianMesh.yaml file for stretched grid."""
  args = read_inputs()
  database = read_parameters_file(args)
  get_ratios(database)
  write_yaml_file(database)


if __name__ == '__main__':
  print('\n[{}] START\n'.format(os.path.basename(__file__)))
  main()
  print('\n[{}] END\n'.format(os.path.basename(__file__)))