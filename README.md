# OSeMBE_ECEMF

This repository contains the scenarios modelled in OSeMBE throughout the H2020 project ECEMF -
European Climate and Energy Modelling Forum.

The repo contains a workflow to run OSeMOSYS models from datapackage to results file in IAMC format.

## OSeMOSYS workflow

This workflow allows to run one or multiple scenarios.
Starting from an OSeMOSYS datapackage going through all steps,
running the model with the Gurobi solver and producing the results in IAMC format.

In addition to the standard OSeMOSYS outputs, the workflow can produce CSV files containing the dual values for all constraints in the model.

### Installation

Install snakemake using conda into a new environment called `snakemake`:

```bash
conda install -c conda-forge mamba
mamba create -c bioconda -c conda-forge -n snakemake snakemake-minimal
```

The workflow manages dependencies through conda environments.
Dependencies are defined per rule and are installed upon first running the workflow.

### Configuring the workflow

3. Place the script `resultify.py` from the repo [osemosys2iamc](https://github.com/OSeMOSYS/osemosys2iamc/tree/osembe) in the root folder of the project.
4. For the `resultify.py` script to run using the `.append` method it is required to use Pandas <2, since the `.append` is no longer supported by Pandas version 2 or newer. By using pandas less than 2 (such as 1.5) one must use a Python < 3.11. After running the snakemake workflow and specifying `--use-conda` in the shell command, the `openentrance-env` will install all dependencies. When this is completed, run: pip install -e git+https://github.com/openENTRANCE/openentrance.git@main#egg=openentrance in the terminal while in the `openentrance-env` environment.

### Adding new scenarios

1. Place datapackage(s) in the folder `input_data`. Each datapackage should be placed in a folder
that is named after the scenario, e.g. `baseline`.
4. Check that the file `config.yaml`, which defines the conversion of OSeMOSYS results to IAMC format
is suitable for the model.

### Running the workflow

3. ***Optional***: To retrieve dual values from your model you need to edit the list of `constraints` in the file `run.py`.
4. Open terminal or command prompt and change to the directory of the snakefile.
5. ***Optional***: Perform a dry run to test snakemake with the command: `snakemake -n`
5. Start the scenario runs with the command `snakemake --cores <number of cores to be used> --use-conda`
