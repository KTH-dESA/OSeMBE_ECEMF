"""This script handles the conversion of OSeMOSYS results in a workflow using otoole.
"""
import os
import sys
from otoole import convert_results

import logging
logger = logging.getLogger(__name__)

def sol2csv(path_to_solution: str, path_to_result: str, path_to_inputs: str, path_to_config: str):
    """Convert solution from Gurobi to CSV.
    """

    convert_results(path_config, 'gurobi', 'csv', path_to_solution, path_to_result, 'csv', path_to_inputs)

if __name__ == '__main__':

    args = sys.argv[1:]

    if len(args) != 4:
        print("Usage: python convert.py <path_gurobi.sol> <path_results> <path_data> <path_config>")
        exit(1)

    path_sol = args[0]
    path_res = args[1]
    path_dp = args[2]
    path_config = args[3]

    if os.path.exists(path_sol):
        sol2csv(path_sol, path_res, path_dp, path_config)
        os.remove(path_sol)

    file_done = open(os.sep.join(path_res.split('/')[:-1]+["res-csv_done.txt"]), "w")
    file_done.close()