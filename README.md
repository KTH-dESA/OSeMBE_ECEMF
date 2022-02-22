# OSeMBE_ECEMF
This repository contains the scenarios modelled in OSeMBE throughout the H2020 project ECEMF -European Climate and Energy Modelling Forum. And it contains a snakemake workflow to run OSeMOSYS models from datapackaget to results in IAMC format. On the workflow more below.
# OSeMOSYS workflow
This repo contains a workflow that allows to run one or multiple scenarios. Starting from an OSeMOSYS datapackage going through all steps running the model with gurobi and producing the results in csv format.

In addition to the standard OSeMOSYS outputs, the workflow produces a csv containing the dual values for all constrains in the model. The csv is safed to the results_csv folder.

Input: 

- datapackage(s)

Output:

- folder with csv files

Prerequisits:

Usage:

1. Place datapackage(s) in the folder `data`. Each datapackage should be in folder that is named after the scenario, e.g. `baseline`.
2. Open the snakefile in a text-editor of your choice. Replace the scenario names potentially already in the list of `SCENARIOS` in line 1 with the names of your scenarios.
3. Open terminal or command prompt in the directory of the snakefile.
4. Perform a dry run to test snakemake with the command: `snakemake -n` [optional]
5. Start the scenario runs with the command `snakemake --cores <number of cores to be used>`