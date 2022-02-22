SCENARIOS = ['utopia1', 'utopia2']
rule all:
    input:
        expand("results/{scen}/res-csv_done.txt", scen=SCENARIOS) #for testing, to be changed during development

rule convert_dp:
    input:
        dp_path = "data/{scen}/datapackage.json"
    output:
        df_path = "data/{scen}/{scen}.txt"
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
    shell:
        "python convert.py {params.sol_path} {params.res_folder} {input.dp_path}"