SCENARIOS = ['NetZero-LimNuclear']
rule all:
    input:
        expand("results/{scen}/res-csv_done.txt", scen=SCENARIOS) #for testing, to be changed during development

rule convert_dp:
    input:
        dp_path = "input_data/NetZero_scen/{scen}/data"
    output:
        df_path = "input_data/NetZero_scen/{scen}/{scen}.txt"
    shell:
        "otoole convert csv datafile {input.dp_path} {output.df_path}"

rule build_lp:
    input:
        df_path = "input_data/NetZero_scen/{scen}/{scen}.txt"
    params:
        model_path = "model/osemosys.txt",
        lp_complete_path = "input_data/NetZero_scen/{scen}/lp_done.txt"
    output:
        lp_path = "input_data/NetZero_scen/{scen}/{scen}.lp"
    shell:
        "glpsol -m {params.model_path} -d {input.df_path} --wlp {output.lp_path} --check"

rule run_model:
    input:
        lp_path = "input_data/NetZero_scen/{scen}/{scen}.lp",
    params:
        path = "results/{scen}/{scen}"
    output:
        done_path = "results/{scen}/{scen}-sol_done.txt"
    shell:
        "python run.py {input.lp_path} {params.path}"

rule convert_sol:
    input:
        sol_complete_path = "results/{scen}/{scen}-sol_done.txt",
        dp_path = "input_data/NetZero_scen/{scen}/data"
    params:
        sol_path = "results/{scen}/{scen}.sol",
        res_folder = "results/{scen}/results_csv"
    output:
        res_path = "results/{scen}/res-csv_done.txt"
    shell:
        "python convert.py {params.sol_path} {params.res_folder} {input.dp_path}"