import os
import pandas as pd

dp_files = pd.read_csv('config/dp_files.txt')

scenario_path = os.path.join("input_data")
SCENARIOS = [x.name for x in os.scandir(scenario_path) if x.is_dir()]

SCENARIOS = ['WP1_NetZero']
SCENARIOS = ['WP1_NetZero']

rule all:
    input:
        expand("results/{scen}.xlsx", scen=SCENARIOS)

rule convert_dp:
    message: "Coverting csv for {wildcards.scen}"
    input:
        other = expand("input_data/{{scen}}/{files}", files=dp_files),
        dp_path = "input_data/{scen}/data"
    output:
        df_path = "working_directory/{scen}.txt"
    conda:
        "envs/otoole_env.yaml"
    shell:
        "otoole convert csv datafile {input.dp_path} {output.df_path} config/config.yaml"


rule build_lp:
    input:
        df_path = "working_directory/{scen}.txt"
    params:
        model_path = "model/osemosys.txt",
    output:
        temp("working_directory/{scen}.lp")
    log:
        "working_directory/{scen}.log"
    threads: 1
    resources:
        mem_mb=62000
    shell:
        "glpsol -m {params.model_path} -d {input.df_path} --wlp {output} --check > {log}"

rule run_model:
    message: "Solving the LP for '{input}'"
    input:
        "working_directory/{scen}.lp",
    output:
        temp("working_directory/{scen}.sol"),
        #directory("working_directory/{scen}_duals")
        #Unhash if you want dual values as output 
    conda:
        "envs/gurobi_env.yaml"
    log:
        "working_directory/gurobi/{scen}.log",
    threads: 32
    resources:
        mem_mb=62000
    script:
        "run.py"

rule convert_sol:
    input:
        sol_path = "working_directory/{scen}.sol",
        dp_path = "input_data/{scen}/data"
    params:
        res_folder = "results/{scen}/results_csv"
    output:
        res_path = "results/{scen}/res-csv_done.txt"
    conda:
        "envs/otoole_env.yaml"
    shell:
        "python convert.py {input.sol_path} {params.res_folder} {input.dp_path}"

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
        "envs/openentrance_env.yaml"
    shell:
        "python resultify.py {params.inputs_folder} {params.res_folder} {input.config_file} {output.output_file}"

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