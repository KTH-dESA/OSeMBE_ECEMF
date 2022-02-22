SCENARIOS = ['utopia1', 'utopia2']
rule all:
    input:
        expand("results/{scen}/{scen}.xlsx", scen=SCENARIOS) #for testing, to be changed during development

rule convert_dp:
    input:
        dp_path = "data/{scen}/datapackage.json"
    output:
        df_path = "data/{scen}/{scen}.txt"
    conda:
        "envs/otoole_env.yaml"
    shell:
        "otoole convert datapackage datafile {input.dp_path} {output.df_path}"

rule build_lp:
    input:
        df_path = "data/{scen}/{scen}.txt"
    params:
        model_path = "model/osemosys.txt",
        lp_path = "data/{scen}/{scen}.lp"
    output:
        lp_complete_path = "data/{scen}/lp_done.txt"
    shell:
        "python gen_lp.py {input.df_path} {params.lp_path}"

rule run_model:
    input:
        lp_complete_path = "data/{scen}/lp_done.txt"
    params:
        lp_path = "data/{scen}/{scen}.lp",
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
        dp_path = "data/{scen}/datapackage.json"
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
        config_tmpl = "data/config.yaml"
    output:
        config_scen = "data/config_{scen}.yaml"
    conda:
        "envs/yaml_env.yaml"
    shell:
        "python ed_config.py {wildcards.scen} {input.config_tmpl} {output.config_scen}"

rule res_to_iamc:
    input:
        res_path = "results/{scen}/res-csv_done.txt",
        config_file = "data/config_{scen}.yaml"
    params:
        inputs_folder = "data/{scen}/data",
        res_folder = "results/{scen}/results_csv"
    output:
        output_file = "results/{scen}/{scen}.xlsx"
    conda:
        "envs/openentrance_env.yaml"
    shell:
        "python resultify.py {params.inputs_folder} {params.res_folder} {input.config_file} {output.output_file}"