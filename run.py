"""
This script runs OSeMOSYS models utilizing the Gurobi Optimizer. 
It requires an LP file as input and generates a SOL file as output.
"""
import sys
import os
import gurobipy as gp
import pandas as pd
import re

"""
Choose a constraint based on the 'dual value' or 'shadow price' you wish to extract.
"""
CONSTRAINTS = ['Constr EBa11_EnergyBalanceEachTS5']

def sol_gurobi(lp_path: str, environment, log_path: str, threads: int):
    m = gp.read(lp_path, environment)
    m.Params.LogToConsole = 0  # don't send log to console
    m.Params.Method = 2  # 2 = barrier
    m.Params.Threads = threads  # limit solve to use max {threads}
    m.Params.NumericFocus = 0  # 0 = automatic; 3 = slow and careful
    m.Params.LogFile = log_path  # don't write log to file
    m.optimize()
    return m

def get_duals(model, path):
    dual_v = {constr.ConstrName: constr.Pi for constr in model.getConstrs() }
    eq = []
    region = []
    timeslice = []
    fuel = []
    year = []
    value = []

    for key, val in dual_v.items():
        if "EBa11" in key:  # Adjust the filter as needed
            match = re.search(r'(.+)\((.+),(.+),(.+),(\d+)\)', key)
            if match:
                eq.append(match.group(1))
                region.append(match.group(2))
                timeslice.append(match.group(3))
                fuel.append(match.group(4))
                year.append(match.group(5))
                value.append(val)

    df = pd.DataFrame({'CONSTRAINT': eq, 'REGION': region, 'TIMESLICE': timeslice, 'FUEL': fuel, 'YEAR': year, 'VALUE': value})
    df = df.drop('CONSTRAINT',axis=1)
    path_res = os.path.dirname(path)
    if not os.path.exists(path_res):
        os.makedirs(path_res)
    
    filepath = os.path.join(path_res, "dual_values_EBa.csv")
    df.to_csv(filepath, index=False)
    print(f"Dual values saved to {filepath}")

def write_sol(sol, path_out: str, path_gen: str):
    try:
        if os.path.exists(path_out):
            os.remove(path_out)
        sol.write(path_out)
        print(f"Solution file written to {path_out}")
    except:
        sol.computeIIS()
        sol.write("%(path)s.ilp" % {'path': path_gen})
    return

if __name__ == "__main__":

    lp_path = snakemake.input[0]
    outpath = snakemake.output[0]
    log_path = snakemake.log[0]
    dual_path = snakemake.output[1]
    threads = snakemake.threads

    env = gp.Env(log_path)

    model = sol_gurobi(lp_path, env, log_path, threads)
    
    write_sol(model, outpath, outpath)
    get_duals(model, dual_path)

    print("Model optimization and output writing completed.")