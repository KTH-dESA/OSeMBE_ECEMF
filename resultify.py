"""Create an IAMC dataset from a package of OSeMOSYS results

Run the command::

    python resultify.py <results_path> <config_path> <output_path>"

where:

    ``results_path`` is the path to the folder of CSV files holding OSeMOSYS results
    ``config_path`` is the path to the ``config.yaml`` file containing the results mapping
    ``output_path`` is the path to the csv file written out in IAMC format

"""
import pandas as pd
import pyam
from openentrance import iso_mapping
import sys
import os
from typing import List, Dict, Union
from yaml import load, SafeLoader
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def read_file(filename) -> pd.DataFrame:

    df = pd.read_csv(filename)

    return df

def filter_dual_values(df: pd.DataFrame, emission: str, region: str):
    """Return dataframe with dual value for provided emissionlimit in provided region"""

    df = df[df['set_1']==emission]

    df['value'] = df['value'] * (-1)

    df = df.rename(columns={'value': 'VALUE', 'set_0': 'REGION', 'set_1': 'EMISSION', 'set_2': 'YEAR'})

    df = df.loc[:, ~df.columns.str.contains('^set')]
    df = df.drop(columns=['constraint'])

    df['REGION'] = region
    df['EMISSION'] = emission

    return df

def filter_var_cost(df: pd.DataFrame, technologies: List) -> pd.DataFrame:
    """Return rows that match the ``technologies``
    """
    mask = df['TECHNOLOGY'].str.contains(technologies[0])

    df['REGION'] = df['TECHNOLOGY'].str[0:2]
    df = df.drop(columns=['TECHNOLOGY', 'MODE_OF_OPERATION'])

    df = df[mask]

    return df[df.VALUE != 0]

def filter_fuel(df: pd.DataFrame, technologies: List, fuels: List) -> pd.DataFrame:
    """Return rows which match ``technologies`` and ``fuels``
    """
    mask = df.TECHNOLOGY.isin(technologies)
    fuel_mask = df.FUEL.isin(fuels)

    return df[mask & fuel_mask]

def filter_emission(df: pd.DataFrame, emission: List) -> pd.DataFrame:
    """Return rows which match ``emission`` and fill region name from technology
    """

    mask = df.EMISSION.isin(emission)

    # First two characters in technology match ISO2 country name
    df['REGION'] = df['TECHNOLOGY'].str[0:2]
    df = df.drop(columns='TECHNOLOGY')

    return df[mask]

def filter_emission_tech(df: pd.DataFrame, tech: List, emission: List) -> pd.DataFrame:
    """Return a dataframe with annual emissions or captured emissions by one or several technologies.
    """

    mask_emi = df.EMISSION.isin(emission)
    df = df[mask_emi]

    df_f = pd.DataFrame(columns=['REGION','TECHNOLOGY','EMISSION','YEAR','VALUE'])

    for t in range(len(tech)):
        mask_tech = df['TECHNOLOGY'].str.contains(tech[t])
        df_t = df[mask_tech]
        df_f = df_f.append(df_t)

    df_f['REGION'] = df_f['TECHNOLOGY'].str[:2]
    df = df_f.drop(columns='TECHNOLOGY')

    df['VALUE'] = df['VALUE']*(-1)

    return df

def filter_capacity(df: pd.DataFrame, technologies: List) -> pd.DataFrame:
    """Return rows that indicate the installed power generation capacity.
    """
    df['REGION'] = df['TECHNOLOGY'].str[:2]
    df_f = pd.DataFrame(columns=['REGION','TECHNOLOGY','YEAR','VALUE'])
    for t in range(len(technologies)):
        mask = df['TECHNOLOGY'].str.contains(technologies[t])
        df_t = df[mask]
        df_f = df_f.append(df_t)

    df = pd.DataFrame(columns=["REGION","YEAR","VALUE"])
    for r in df_f["REGION"].unique():
        for y in df_f["YEAR"].unique():
            df = df.append({"REGION": r, "YEAR": y, "VALUE": df_f.loc[(df_f["REGION"]==r)&(df_f["YEAR"]==y),["VALUE"]].sum(axis=0).VALUE},ignore_index=True).sort_values(by=['REGION','YEAR'])
    return df[df.VALUE != 0].reset_index(drop=True)

def filter_ProdByTechAn(df: pd.DataFrame, technologies: List) -> pd.DataFrame:
    """Return rows that indicate Primary Energy use/generation
    """
    df['REGION'] = df['TECHNOLOGY'].str[:2]
    df_f = pd.DataFrame(columns=['REGION','TECHNOLOGY','FUEL','YEAR','VALUE'])
    for t in range(len(technologies)):
        mask = df['TECHNOLOGY'].str.contains(technologies[t])
        df_t = df[mask]
        df_f = df_f.append(df_t)

    df = pd.DataFrame(columns=["REGION","YEAR","VALUE"])
    for r in df_f["REGION"].unique():
        for y in df_f["YEAR"].unique():
            df = df.append({"REGION": r, "YEAR": y, "VALUE": df_f.loc[(df_f["REGION"]==r)&(df_f["YEAR"]==y),["VALUE"]].sum(axis=0).VALUE},ignore_index=True).sort_values(by=['REGION','YEAR'])
    return df[df.VALUE != 0].reset_index(drop=True)

def filter_final_energy(df: pd.DataFrame, fuels: List) -> pd.DataFrame:
    """Return dataframe that indicate the final energy demand/use per country and year.
    """
    for f in fuels:
        if len(f)!=2:
            print("Fuel %s from config.yaml doesn't comply with expected format." % f)
            exit(1)

    df['REGION'] = df['FUEL'].str[:2]
    df['FUEL'] = df['FUEL'].str[2:]
    df_f = pd.DataFrame(columns=['REGION','TIMESLICE','FUEL','YEAR','VALUE'])

    for f in range(len(fuels)):
        mask = df['FUEL'].str.contains(fuels[f])
        df_t = df[mask]
        df_f = df_f.append(df_t)

    df = pd.DataFrame(columns=['REGION','YEAR','VALUE'])
    for r in df_f['REGION'].unique():
        for y in df_f['YEAR'].unique():
            df = df.append({"REGION": r, "YEAR": y, "VALUE": df_f.loc[(df_f["REGION"]==r)&(df_f["YEAR"]==y),["VALUE"]].sum(axis=0).VALUE},ignore_index=True).sort_values(by=['REGION','YEAR'])
    return df[df.VALUE != 0].reset_index(drop=True)

def calculate_trade(results: dict, techs: List) -> pd.DataFrame:
    """Return dataframe with the net exports of a commodity
    """

    countries = pd.Series(dtype='object')
    years = pd.Series()
    for p in results:
        df = results[p]
        df_f = pd.DataFrame(columns=df.columns)
        for t in techs:
            mask = df['TECHNOLOGY'].str.contains(t)
            df_t = df[mask]
            df_f = df_f.append(df_t)

        df_f['REGION'] = df_f['FUEL'].str[:2]
        df_f = df_f.drop(columns='FUEL')
        df_f = df_f.groupby(by=['REGION', 'YEAR']).sum()
        df_f = df_f.reset_index(level=['REGION', 'YEAR'])

        countries = countries.append(df_f.loc[:,'REGION'])
        years = years.append(df_f.loc[:,'YEAR'])
        results[p] = df_f

    countries = countries.unique()
    years = years.unique()
    exports = results['UseByTechnology']
    imports = results['ProductionByTechnologyAnnual']

    df = pd.DataFrame(columns=['REGION','YEAR','VALUE'])
    for country in countries:
        for year in years:
            if not exports[(exports['REGION']==country)&(exports['YEAR']==year)].empty:
                if not imports[(imports['REGION']==country)&(imports['YEAR']==year)].empty:
                    value = exports[(exports['REGION']==country)&(exports['YEAR']==year)].iloc[0]['VALUE']-imports[(imports['REGION']==country)&(imports['YEAR']==year)].iloc[0]['VALUE']
                    df = df.append({'REGION': country, 'YEAR': year, 'VALUE': value}, ignore_index=True)
                else:
                    value = exports[(exports['REGION']==country)&(exports['YEAR']==year)].iloc[0]['VALUE']
                    df = df.append({'REGION': country, 'YEAR': year, 'VALUE': value}, ignore_index=True)
            else:
                if not imports[(imports['REGION']==country)&(imports['YEAR']==year)].empty:
                    value = -imports[(imports['REGION']==country)&(imports['YEAR']==year)].iloc[0]['VALUE']
                    df = df.append({'REGION': country, 'YEAR': year, 'VALUE': value}, ignore_index=True)


    return df

def extract_results(df: pd.DataFrame, technologies: List) -> pd.DataFrame:
    """Return rows which match ``technologies``
    """

    mask = df.TECHNOLOGY.isin(technologies)

    return df[mask]

def aggregate(data: pd.DataFrame):
    """Sums rows while grouping regions and years
    """

    return data.groupby(by=['REGION', 'YEAR']).sum()

def make_iamc(data: pd.DataFrame,
              iam_model: str,
              iam_scenario: str,
              iam_variable: str,
              iam_unit: str
              ) -> pyam.IamDataFrame:
    """Creates an IAM Dataframe from raw data

    Arguments
    ---------
    data: pd.DataFrame
        Contains columns for region, year and value
    iam_model: str
        The model name to insert into the IAMC dataframe
    iam_scenario: str
        The scenario name to insert into the IAMC dataframe
    iam_variable: str
        The IAMC variable name to insert into the IAMC dataframe
    iam_unit: str
        The unit to insert into the IAMC dataframe

    """
    data = data.reset_index()
    data = data.rename(columns={
        'REGION': 'region',
        'YEAR': 'year'
    })
    # Add required columns
    data['model'] = iam_model
    data['scenario'] = iam_scenario
    data['variable'] = iam_variable
    data['unit'] = iam_unit

    iamc = pyam.IamDataFrame(data)
    return iamc

def load_config(filepath: str) -> Dict:
    """Reads the configuration file

    Arguments
    ---------
    filepath : str
        The path to the config file
    """
    with open(filepath, 'r') as configfile:
        config = load(configfile, Loader=SafeLoader)
    return config

def make_plots(df, model: str, scenario: str, regions: list):
    """Creates standard plots

    Arguments
    ---------
    model: str
    scenario: str
    """

    # df = all_data #for testing
    # model = config['model'] #for testing
    # scenario = config['scenario'] #for testing
    # regions = config['region']#for testing

    args = dict(model=model, scenario=scenario)
    print(args)

    for region in regions:

    # Plot primary energy
        fig, ax = plt.subplots()
        print(ax)
        pe = df.filter(**args, variable='Primary Energy|*', region=region)
        if pe:
            locator = mdates.AutoDateLocator(minticks=10)
            #locator.intervald['YEARLY'] = [10]
            pe.plot.bar(ax=ax, stacked=True, title='Primary energy mix %s' % region)
            plt.legend(bbox_to_anchor=(0.,-0.5), loc='upper left')
            plt.tight_layout()
            ax.xaxis.set_major_locator(locator)
            fig.savefig('primary_energy_%s.pdf' % region, bbox_inches='tight', transparent=True, pad_inches=0)

    # Plot secondary energy (electricity generation)
        fig, ax = plt.subplots()
        print(ax)
        se = df.filter(**args, variable='Secondary Energy|Electricity|*', region=region)
        if se:
            locator = mdates.AutoDateLocator(minticks=10)
            #locator.intervald['YEARLY'] = [10]
            pe.plot.bar(ax=ax, stacked=True, title='Power generation mix %s' % region)
            plt.legend(bbox_to_anchor=(0.,-0.5), loc='upper left')
            plt.tight_layout()
            ax.xaxis.set_major_locator(locator)
            fig.savefig('electricity_generation_%s.pdf' % region, bbox_inches='tight', transparent=True, pad_inches=0)

    # Create generation capacity plot
        fig, ax = plt.subplots()
        cap = df.filter(**args, variable='Capacity|Electricity|*', region=region)
        if cap:
            cap.plot.bar(ax=ax, stacked=True, title='Generation Capacity %s' % region)
            plt.legend(bbox_to_anchor=(0.,-0.25),loc='upper left')
            plt.tight_layout()
            fig.savefig('capacity_%s.pdf' % region, bbox_inches='tight', transparent=True, pad_inches=0)

    # Create emissions plot
    emi = df.filter(**args, variable="Emissions|CO2*").filter(region="World", keep=False)
    print(emi)
    if emi:
        fig, ax = plt.subplots()
        emi.plot.bar(ax=ax,
            bars="region", stacked=True, title="CO2 emissions by region", cmap="tab20"
            )
        plt.legend(bbox_to_anchor=(1.,1.05),loc='upper left', ncol=2)
        fig.savefig('emission.pdf', bbox_inches='tight', transparent=True, pad_inches=0)



def main(config: Dict) -> pyam.IamDataFrame:
    """Create the IAM data frame from results

    Loops over each entry in the configuration file, extracts the data from
    the relevant result file and puts this into the IAMC data format

    Arguments
    ---------
    config : dict
        The configuration dictionary
    """
    blob = []
    for input in config['inputs']:

        inpathname = os.path.join(inputs_path, input['osemosys_param'] + '.csv')
        inputs = read_file(inpathname)

        unit = input['unit']

        technologies = input['variable_cost']
        data = filter_var_cost(inputs, technologies)

        aggregated = aggregate(data)

        if not aggregated.empty:
            iamc = make_iamc(aggregated, config['model'], config['scenario'], input['iamc_variable'], unit)
            blob.append(iamc)

    for result in config['results']:

        if type(result['osemosys_param']) == str:
            inpathname = os.path.join(results_path, result['osemosys_param'] + '.csv')
            results = read_file(inpathname)

            try:
                technologies = result['technology']
            except KeyError:
                pass
            unit = result['unit']
            if 'fuel' in result.keys():
                fuels = result['fuel']
                data = filter_fuel(results, technologies, fuels)
            elif 'emission' in result.keys():
                emission = result['emission']
                data = filter_emission(results, emission)
            elif 'tech_emi' in result.keys():
                emission = result['emissions']
                technologies = result['tech_emi']
                data = filter_emission_tech(results, technologies, emission)
            elif 'capacity' in result.keys():
                technologies = result['capacity']
                data = filter_capacity(results, technologies)
            elif 'primary_technology' in result.keys():
                technologies = result['primary_technology']
                data = filter_ProdByTechAn(results, technologies)
            elif 'excluded_prod_tech' in result.keys():
                technologies = result['excluded_prod_tech']
                data = filter_ProdByTechAn(results, technologies)
            elif 'el_prod_technology' in result.keys():
                technologies = result['el_prod_technology']
                data = filter_ProdByTechAn(results, technologies)
            elif 'demand' in result.keys():
                demands = result['demand']
                data = filter_final_energy(results, demands)
            elif 'dual_emission' in result.keys():
                emission = result['dual_emission']
                region = result['region']
                data = filter_dual_values(results, emission, region)
            else:
                data = extract_results(results, technologies)

        else:
            results = {}
            for p in result['osemosys_param']:
                inpathname = os.path.join(results_path, p + '.csv')
                results[p] = read_file(inpathname)
            if 'trade_tech' in result.keys():
                technologies = result['trade_tech']
                data = calculate_trade(results, technologies)

        aggregated = aggregate(data)

        if not aggregated.empty:
            iamc = make_iamc(aggregated, config['model'], config['scenario'], result['iamc_variable'], unit)
            blob.append(iamc)

    all_data = pyam.concat(blob)

    all_data = all_data.convert_unit('PJ/yr', to='EJ/yr').timeseries()
    all_data = pyam.IamDataFrame(all_data)
    all_data = all_data.convert_unit('ktCO2/yr', to='Mt CO2/yr', factor=0.001).timeseries()
    all_data = pyam.IamDataFrame(all_data)
    all_data = all_data.convert_unit('MEUR_2015/PJ', to='EUR_2020/GJ', factor=1.05).timeseries()
    all_data = pyam.IamDataFrame(all_data)
    all_data = all_data.convert_unit('kt CO2/yr', to='Mt CO2/yr').timeseries()
    all_data.index = all_data.index.set_levels(all_data.index.levels[2].map(iso_mapping), level=2)
    all_data = pyam.IamDataFrame(all_data)
    all_data = all_data.convert_unit('M€_2015/kt CO2', to='EUR_2020/t CO2', factor=1050).timeseries()
    all_data = pyam.IamDataFrame(all_data)
    return all_data

if __name__ == "__main__":

    args = sys.argv[1:]

    if len(args) != 4:
        print("Usage: python resultify.py <inputs_path> <results_path> <config_path> <output_path>")
        exit(1)

    inputs_path = args[0]
    results_path = args[1]
    configpath = args[2]
    outpath = args[3]

    config = load_config(configpath)

    all_data = main(config)

    model = config['model']
    scenario = config['scenario']
    regions = config['region']
    #make_plots(all_data, model, scenario, regions)

    all_data.to_excel(outpath,sheet_name='data')
