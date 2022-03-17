"""This script handles the conversion of OSeMOSYS results in a workflow using otoole.
"""
import os
import sys
from otoole import ReadGurobi
from otoole import ReadDatapackage
from otoole import WriteCsv
from otoole import Context

def sol2csv(p_sol: str, p_res: str, p_dp: str):
    reader = ReadGurobi()
    writer = WriteCsv()

    input_data, _ = ReadDatapackage().read(p_dp)
    converter = Context(read_strategy=reader, write_strategy=writer)
    converter.convert(p_sol, p_res, input_data=input_data)

if __name__ == '__main__':
    
    args = sys.argv[1:]

    if len(args) != 3:
        print("Usage: python convert.py <path_gurobi.sol> <path_results> <path_data>")
        exit(1)

    path_sol = args[0]
    path_res = args[1]
    path_dp = args[2]

    if os.path.exists(path_sol):
        sol2csv(path_sol, path_res, path_dp)
        os.remove(path_sol)

    file_done = open(os.sep.join(path_res.split('/')[:-1]+["res-csv_done.txt"]), "w")
    file_done.close()