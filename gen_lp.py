"""Script to generate lp file from OSeMOSYS datafile, within a workflow and to provide output in case not possible avoiding breaking of the workflow.
"""
import os
import sys
import subprocess as sp

def gen_lp(p_df: str, p_lp: str):

    str_cmd = "glpsol -m "+os.path.join('"model','osemosys.txt"') + ' -d "%(data)s" --wlp "%(lp)s" --check' % {'data': p_df, 'lp': p_lp}
    
    try:
        sp.run(str_cmd, shell=True, capture_output=True)
    except:
        file_error = open(os.sep.join(p_lp.split('/')[:-1]+['lp-error.txt']), "w")
        file_error.close()

if __name__ == "__main__":
    
    args = sys.argv[1:]

    if len(args) != 2:
        print("Usage: python gen_lp.py <path_df> <path_lp>")
        exit(1)
    
    path_df = args[0]
    path_lp = args[1]

    gen_lp(path_df, path_lp)

    file_done = open(os.sep.join(path_lp.split('/')[:-1]+['lp_done.txt']), "w")
    file_done.close()