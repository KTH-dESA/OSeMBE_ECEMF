"""This script runs OSeMOSYS models using gurobi. It takes as input an lp-file and produces a sol-file.
"""
import sys
import os
import gurobipy
import pandas as pd

def sol_gurobi(lp_path: str):
    m = gurobipy.read(lp_path)
    m.optimize()

    return m

def del_lp(p_lp: str):
    os.remove(p_lp)
    return

def get_duals(model):
    constraints = ['Constr E8_AnnualEmissionsLimit']
    try:
        dual = model.Pi
        constr = model.getConstrs()
        df_dual = pd.DataFrame(data= {'info': constr, 'value': dual})
        df_dual = df_dual.astype({'info': 'str'})
        meta = df_dual['info'].str.split('.', expand=True)
        meta = meta[1].str.split('(', expand=True)
        df_dual['constraint'] = meta[0]
        df_dual['sets'] = meta[1].str[:-2]
        df_dual = df_dual.drop(columns=['info'])
    except:
        df_dual = pd.DataFrame(columns=['value', 'constraint', 'sets'])
    dic_duals = {}
    if not df_dual.empty:
        for c in constraints:
            dic_duals[c] = df_dual[df_dual['constraint']==c]
            if not dic_duals[c].empty:
                sets = dic_duals[c]['sets'].str.split(',', expand=True).add_prefix('set_')
                dic_duals[c] = pd.concat([dic_duals[c], sets], axis=1)
                dic_duals[c] = dic_duals[c].drop(columns=['sets'])
    return dic_duals

def write_duals(dict_duals: dict, path: str):
    path_res = os.sep.join(path.split('/')[:-1]+['results_csv'])
    os.mkdir(path_res)
    for df in dict_duals:
        dict_duals[df].to_csv('%(path)s/Dual_%(constr)s.csv' % {'path': path_res, 'constr': df}, index=False)
    return

def write_sol(sol, path_out: str, path_gen: str):
    try:
        sol.write(path_out)
    except:
        sol.computeIIS()
        sol.write("%(path)s.ilp" % {'path': path_gen})
    return

if __name__ == "__main__":
    
    args = sys.argv[1:]

    if len(args) != 2:
        print("Usage: python run.py <lp_path> <generic_out_path>")
        exit(1)

    lp_path = args[0]
    gen_path = args[1]

    outpath = gen_path + ".sol"
    
    model = sol_gurobi(lp_path)
    del_lp(lp_path)
    dic_duals = get_duals(model)
    write_duals(dic_duals, gen_path)
    write_sol(model, outpath, gen_path)

    file_done = open(gen_path+"-sol_done.txt", "w")
    file_done.close()