# OSeMBE_ECEMF
This repository contains the scenarios modelled in OSeMBE throughout the H2020 project ECEMF -European Climate and Energy Modelling Forum. And the repo contains a workflow to run OSeMOSYS models from datapackage to results file in IAMC format.
# OSeMOSYS workflow
This workflow allows to run one or multiple scenarios. Starting from an OSeMOSYS datapackage going through all steps running the model with gurobi and producing the results in IAMC format.

In addition to the standard OSeMOSYS outputs, the workflow can produce csvs containing the dual values for all constrains in the model.

## Installation
Install snakemake using conda into a new environment called `snakemake`:
```bash
conda install -c conda-forge mamba
mamba create -c bioconda -c conda-forge -n snakemake snakemake-minimal
```
## Configuring the workflow
### Input: 

- datapackage(s)

### Output:

- xlsx-files with model results in IAMC format

### Usage:

1. Place datapackage(s) in the folder `data`. Each datapackage should be in a folder that is named after the scenario, e.g. `baseline`.
2. Open the snakefile in a text-editor of your choice. Replace the scenario names potentially already in the list of `SCENARIOS` in line 1 with the names of your scenarios. The line should look similar to the below:
```bash
SCENARIOS = ['baseline', 'scenario1']`
```
3. Place the script `resultify.py` from the repo [osemosys2iamc](https://github.com/OSeMOSYS/osemosys2iamc/tree/osembe) in your folder.
4. Make sure that the file `data/config.yaml`is suitable for your model. 
3. ***Optional***: To retrieve dual values from your model you need to edit the list of `constraints` in the file `run.py`.
4. Open terminal or command prompt in the directory of the snakefile.
5. ***Optional***: Perform a dry run to test snakemake with the command: `snakemake -n`
5. Start the scenario runs with the command `snakemake --cores <number of cores to be used> --use-conda`