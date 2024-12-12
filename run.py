import sys
import os
import gurobipy as gp
import pandas as pd
import re

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

    df = pd.DataFrame({'CONSTRAINT': eq, 'REGION': region, 'TIMESLICE': timeslice, 'FUEL': fuel, 'YEAR': year, 'DUAL_VALUE': value})

    path_res = os.path.dirname(path)
    if not os.path.exists(path_res):
        os.makedirs(path_res)
    
    filepath = os.path.join(path_res, "dual_values_EBa11.csv")
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
        sol.write(f"{path_gen}.ilp")
        print(f"Solution could not be written, IIS file written to {path_gen}.ilp")
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
