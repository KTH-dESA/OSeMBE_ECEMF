import os

scenario_path = os.path.join("input_data", "diagnostic_scen")
SCENARIOS = [x.path for x in os.scandir(scenario_path) if x.is_dir()]

rule all:
    input:
        expand("results/{scen}/{scen}.xlsx", scen=SCENARIOS) #for testing, to be changed during development

rule convert_dp:
    input:
        dp_path = "{scen}/datapackage.json"
    output:
        df_path = "{scen}/{scen}.txt"
    conda:
        "envs/otoole_env.yaml"
    shell:
        "otoole convert datapackage datafile {input.dp_path} {output.df_path}"

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
        df_path = "{scen}/{scen}.txt"
    params:
        model_path = "model/osemosys.txt",
        lp_path = "{scen}/{scen}.lp"
    output:
        lp_complete_path = "{scen}/lp_done.txt"
    shell:
        "python gen_lp.py {input.df_path} {params.lp_path}"

rule run_model:
    input:
        lp_complete_path = "{scen}/lp_done.txt"
    params:
        lp_path = "{scen}/{scen}.lp",
        path = "results/{scen}/{scen}"
    output:
        done_path = "results/{scen}/{scen}-sol_done.txt"
    conda:
        "envs/gurobi_env.yaml"
    shell:
        "python run.py {params.lp_path} {params.path}"

rule convert_sol:
    input:
        sol_complete_path = "results/{scen}/{scen}-sol_done.txt",
        dp_path = "{scen}/datapackage.json"
    params:
        sol_path = "results/{scen}/{scen}.sol",
        res_folder = "results/{scen}/results_csv"
    output:
        res_path = "results/{scen}/res-csv_done.txt"
    conda:
        "envs/otoole_env.yaml"
    shell:
        "python convert.py {params.sol_path} {params.res_folder} {input.dp_path}"

rule create_configs:
    input:
        config_tmpl = "config.yaml"
    output:
        config_scen = "config_{scen}.yaml"
    conda:
        "envs/yaml_env.yaml"
    shell:
        "python ed_config.py {wildcards.scen} {input.config_tmpl} {output.config_scen}"

rule res_to_iamc:
    input:
        res_path = "results/{scen}/res-csv_done.txt",
        config_file = "config_{scen}.yaml"
    params:
        inputs_folder = "{scen}/data",
        res_folder = "results/{scen}/results_csv"
    output:
        output_file = "results/{scen}/{scen}.xlsx"
    conda:
        "envs/openentrance_env.yaml"
    shell:
        "python resultify.py {params.inputs_folder} {params.res_folder} {input.config_file} {output.output_file}"