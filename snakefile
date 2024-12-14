import os
import pandas as pd

dp_files = pd.read_csv('config/dp_files.txt')

scenario_path = os.path.join("input_data")
SCENARIOS = [x.name for x in os.scandir(scenario_path) if x.is_dir()]

SCENARIOS = []

"""
Scenario selection.

Copy the names of scenarios that you wish to run into the SCENARIO list. 

WP1: 'WP1_NetZero','WP1_NetZero-LimBio','WP1_NetZero-LimCCS','WP1_NetZero-LimNuc','WP1_NPI'
WP5: 'WP5_OPT-MIX','WP5_OPT-MIX-LimBio','WP5_OPT-MIX-LimCCS','WP5_OPT-MIX-LimNuc','WP5_OPT-MIX-LimRES'
"""

rule all:
    input:
        expand("results/{scen}.xlsx", scen=SCENARIOS)

rule convert_dp:
    message: "Converting csv for {wildcards.scen}"
    input:
        other = expand("input_data/{{scen}}/data/{files}", files=dp_files),
        dp_path = "input_data/{scen}/data"
    output:
        df_path = "working_directory/{scen}.txt"
    log:
        "working_directory/otoole_{scen}.log"
    conda:
        "envs/otoole_env.yaml"
    shell:
        "otoole -v convert csv datafile {input.dp_path} {output.df_path} config/config.yaml > {log} 2>&1"

rule pre_process:
    input:
        "working_directory/{scen}.txt"
    output:
        temporary("working_directory/{scen}.pre")
    conda:
        "envs/otoole_env.yaml"
    shell:
        "python pre_process.py otoole {input} {output}"

rule build_lp:
    input:
        df_path = "working_directory/{scen}.pre"
    params:
        model_path = "model/osemosys.txt",
    output:
        "working_directory/{scen}.lp"
    log:
        "working_directory/{scen}.log"
    threads: 1
    """
    Specify the RAM resources (in MB) based on RAM availability of your machine.
    """
    resources:
        mem_mb=62000
    shell:
        "glpsol -m {params.model_path} -d {input.df_path} --wlp {output} --check > {log}"

rule run_model:
    message: "Solving the LP for '{input}'"
    input:
        "working_directory/{scen}.lp",
    output:
        "working_directory/{scen}.sol",
        "results/{scen}/results_csv/dual_values_EBa11.csv"
    conda:
        "envs/gurobi_env.yaml"
    log:
        "working_directory/gurobi/{scen}.log",
    """
    Threads correspond to the core count.
    
    It can differ from the number of physical cores of the CPU if 
    the CPU supports hyperthreading or multithreading. 
    """
    threads: 32
    """
    Specify the RAM resources (in MB) based on RAM availability of your machine.
    """
    resources:
        mem_mb=62000
    script:
        "run.py"

rule convert_sol:
    input:
        sol_path = "working_directory/{scen}.sol",
        dp_path = "input_data/{scen}/data"
    params:
        res_folder = "results/{scen}/results_csv",
        config = "config/config.yaml"
    output:
        res_path = "results/{scen}/res-csv_done.txt"
    conda:
        "envs/otoole_env.yaml"
    shell:
        "python convert.py {input.sol_path} {params.res_folder} {input.dp_path} {params.config}"

rule create_configs:
    input:
        config_tmpl = "config.yaml"
    output:
        config_scen = "working_directory/config_{scen}.yaml"
    conda:
        "envs/yaml_env.yaml"
    shell:
        "python ed_config.py {wildcards.scen} {input.config_tmpl} {output.config_scen}"

rule res_to_iamc:
    input:
        res_path = "results/{scen}/res-csv_done.txt",
        config_file = "working_directory/config_{scen}.yaml"
    params:
        inputs_folder = "input_data/{scen}/data",
        res_folder = "results/{scen}/results_csv"
    output:
        output_file = "results/{scen}.xlsx"
    conda:
        "envs/iamc.yaml"
    shell:
        "osemosys2iamc {params.inputs_folder} {params.res_folder} {input.config_file} {output.output_file}"

rule make_dag:
    output: pipe("dag.txt")
    shell:
        "snakemake --dag > {output}"

rule plot_dag:
    input: "dag.txt"
    output: "dag.png"
    conda: "envs/dag.yaml"
    shell:
        "dot -Tpng {input} > dag.png && open dag.png"

rule clean:
    shell:
        "rm -rf results/* && rm -rf working_directory/*"