# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 14:51:38 2020

@author: haukeh
"""

#%%Import of required packages
import numpy as np
import pandas as pd
import os
import sys
import plotly.graph_objs as go
from plotly.offline import plot

#%% Function to read results csv files
def read_csv(scen, param):
    df = pd.read_csv('{}/results_csv/{}.csv'.format(scen,param))
    df['pathway'] = scen
    return df
#%% Function to create dictionaries containing dictionaries for each scenario that contain the results as dataframes
def build_dic(scens, params):
    dic = {}
    for scen in scens:
        dic[scen] = {}
    for scen in scens:
        for param in params:
            dic[scen][param] = read_csv(scen, param)
    return dic
#%% Function to creat a df with the production by technology annual
def build_PbTA_df(dic):
    # dic = results_dic
    df = pd.DataFrame(columns=['REGION','TECHNOLOGY','FUEL','YEAR','VALUE','pathway'])
    for i in dic:
        df_work = dic[i]['ProductionByTechnologyAnnual']
        df = df.append(df_work)
    df['region'] = df['TECHNOLOGY'].apply(lambda x: x[:2])
    df['fuel'] = df['TECHNOLOGY'].apply(lambda x: x[2:4])
    df['tech_type'] = df['TECHNOLOGY'].apply(lambda x: x[4:6])
    df['tech_spec'] = df['TECHNOLOGY'].apply(lambda x: x[2:])
    df = df[(df['fuel']!='OI')
            &(df['tech_type']!='00')
            &((df['YEAR']==2015)|(df['YEAR']==2020)|(df['YEAR']==2030)|(df['YEAR']==2040)|(df['YEAR']==2050))]
    df['unit'] = 'PJ'
    return df
#%% Function to create dictionary with information
def get_facts(df):
    facts_dic = {}
    facts_dic['pathways'] = df.loc[:,'pathway'].unique()
    facts_dic['regions'] = df.loc[:,'region'].unique()
    facts_dic['unit'] = df.loc[:, 'unit'].unique()
    facts_dic['regions'] = np.append(facts_dic['regions'],'EU28')
    return facts_dic
#%% Dictionary of dictionaries with colour schemes
colour_schemes = dict(
    dES_colours = dict(
        Coal = 'rgb(0, 0, 0)',
        Oil = 'rgb(121, 43, 41)',
        Gas = 'rgb(86, 108, 140)',
        Nuclear = 'rgb(186, 28, 175)',
        Waste = 'rgb(138, 171, 71)',
        Biomass = 'rgb(172, 199, 119)',
        Biofuel = 'rgb(79, 98, 40)',
        Hydro = 'rgb(0, 139, 188)',
        Wind = 'rgb(143, 119, 173)',
        Solar = 'rgb(230, 175, 0)',
        Geo = 'rgb(192, 80, 77)',
        Ocean ='rgb(22, 54, 92)',
        Imports = 'rgb(232, 133, 2)'),
    TIMES_PanEU_colours = dict(
        Coal = 'rgb(0, 0, 0)',
        Oil = 'rgb(202, 171, 169)',
        Gas = 'rgb(102, 77, 142)',
        Nuclear = 'rgb(109, 109, 109)',
        Waste = 'rgb(223, 134, 192)',
        Biomass = 'rgb(80, 112, 45)',
        Biofuel = 'rgb(178, 191, 225)',
        Hydro = 'rgb(181, 192, 224)',
        Wind = 'rgb(103, 154, 181)',
        Solar = 'rgb(210, 136, 63)',
        Geo = 'rgb(178, 191, 225)',
        Ocean ='rgb(178, 191, 225)',
        Imports = 'rgb(232, 133, 2)')
    )
#%% functions for returning positives and negatives
def positives(value):
    return max(value, 0)
def negatives(value):
    return min(value, 0)
#%% Function to create dfs with import and export of electricity for selected country
def impex(data, paths, selected_country):
    df_filtered = data[(data['fuel']=='EL')
                       &((data['region']==selected_country)|(data['tech_type']==selected_country))
                       &(data['tech_type']!='00')]
    countries = []
    countries = list(df_filtered['region'].unique())
    countries.extend(df_filtered['tech_type'].unique())
    countries = list(dict.fromkeys(countries))
    df_filtered = df_filtered[df_filtered['FUEL'].str.contains('|'.join(countries))]
    df_filtered = df_filtered[df_filtered['FUEL'].str.contains('E1')]
    years = pd.Series(df_filtered['YEAR'].unique(),name='YEAR').sort_values()
    #paths = list(path_names.keys())
    neighbours = []
    for i in countries:
        if i != selected_country:
            neighbours.append(i)
    dict_path = {}
    links = list(df_filtered['TECHNOLOGY'].unique())
    label_imp = []
    label_exp = []
    for n in neighbours:
        label_imp.append('Import from '+n)
        label_exp.append('Export to '+n)
    for j in paths:
        i = 0
        net_imp = pd.DataFrame(index=years)
        for link in links:
            imp = df_filtered[(df_filtered['pathway']==j)
                              &(df_filtered['TECHNOLOGY']==link)
                              &(df_filtered['FUEL']==(selected_country+'E1'))]
            if len(imp.index)<5:
                imp = imp.set_index('YEAR').reindex(years).reset_index().fillna(0)
            imp = imp.set_index(years)
            exp = df_filtered[(df_filtered['pathway']==j)
                              &(df_filtered['TECHNOLOGY']==link)
                              &(df_filtered['FUEL']==(neighbours[i]+'E1'))]
            if len(exp.index)<5:
                exp = exp.set_index('YEAR').reindex(years).reset_index().fillna(0)
            exp = exp.set_index(years) 
            net_imp[link] = imp['VALUE'] - exp['VALUE']
            i += 1
        net_imp_pos = pd.DataFrame(index=years,columns=links)
        net_imp_neg = pd.DataFrame(index=years,columns=links)
        for link in links:
            net_imp_pos[link] = net_imp[link].map(positives)
            net_imp_neg[link] = net_imp[link].map(negatives)
        net_imp_pos.columns = label_imp
        net_imp_neg.columns = label_exp
        dict_path[j] = {}
        dict_path[j]['imports']=net_imp_pos
        dict_path[j]['exports']=net_imp_neg
    path_ind = []
    year_ind = []
    df_exports = pd.DataFrame(columns=label_exp)
    df_imports = pd.DataFrame(columns=label_imp)
    for year in years:
        i=0
        for j in paths:
            df_exports = df_exports.append(dict_path[j]['exports'].loc[year])
            df_imports = df_imports.append(dict_path[j]['imports'].loc[year])
            path_ind.append(paths[i].upper())
            i+=1
    df_exports = df_exports.set_index([pd.Index(path_ind, name='paths')],append=True)
    df_imports = df_imports.set_index([pd.Index(path_ind, name='paths')],append=True)
    return df_exports, df_imports
#%% Function to create figure
def create_fig(data, paths, country_sel, countries_mod, fuels, colours):
    fig = go.Figure()
    elexp, elimp = impex(data, paths, country_sel)
    elexp = elexp.sum(axis=1)
    elimp = elimp.sum(axis=1)
    #paths = list(path_names.keys())
    years = data['YEAR'].unique()
    years.sort()
    coms = fuels['fuel_name']
    coms = coms[(coms!='EL')&(coms!='OI')]
    info_dict = {}
    info_dict['Unit'] = data.loc[:,'unit'].unique()
    info_dict['Y-Axis'] = ['{}'.format(*info_dict['Unit'])]
    countr_el1 = country_sel + 'E1'
    countr_el2 = country_sel + 'E2'
    dict_path = {}
    for path in paths:
        filtered_df = data[
        (data['pathway'] == path) 
        & (data['region'] == country_sel) 
        & ((data['FUEL']==countr_el1)|(data['FUEL']==countr_el2)) 
        & (data['fuel']!='EL') 
        & (data['tech_type']!='00')]
        filtered_df_p = filtered_df.pivot(index='YEAR', columns='tech_spec',  values='VALUE')
        df_by_com = pd.DataFrame()
        for com in coms:
            com_selec = filtered_df_p.filter(regex="\A"+com, axis=1)
            com_sum = com_selec.sum(axis=1)
            df_by_com[com] = com_sum
        dict_path[path] = df_by_com
    df_fig = pd.DataFrame(columns=coms)
    path_ind = []
    year_ind = []
    for y in years:
        i = 0
        for p in paths:
            df_fig = df_fig.append(dict_path[p].loc[y])
            path_ind.append(paths[i].upper())
            year_ind.append(y)
            i +=1
    df_fig = df_fig.set_index([pd.Index(path_ind, name='paths')],append=True)
    df_fig['EL'] = elimp
    coms = coms.append(pd.Series('EL'))
    for c in coms:
        temp = fuels.loc[fuels['fuel_name']==c,'fuel_abr']
        fuel_code = temp.iloc[0]
        fig.add_trace(go.Bar(
            y = df_fig.loc[:,c],
            x = [year_ind,path_ind],
            name = fuel_code,
            hovertemplate = 'Power generation: %{y}PJ',
            marker_color = colours[fuel_code]
            ))
    fig.add_trace(go.Bar(
    y = elexp,
    x = [year_ind,path_ind],
    name = 'Exports',
    hovertemplate = 'Exported electricity: %{y}PJ',
    marker_color = colours['Imports'],
    base=0
    ))
    fig.update_layout(
        barmode = 'stack',
        plot_bgcolor='rgba(0,0,0,0)',
        title={
            'text':'<b>Electricity generation in {}</b>'.format(countries_mod[country_sel]),
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis = {'type': 'multicategory'},
        yaxis = dict(title='Electricity in [{}]'.format(info_dict['Y-Axis'][0])),
        font_family = "Arial",
        font_color = "black",
        title_font_size = 32,
        legend_font_size = 26
        )
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='Black',title_font_size=26, tickfont_size=22)
    fig.update_xaxes(tickfont_size=22)
    return fig

#%% main function to execute the script
def main(country,scenarios):

    #scens = ['B1C0TxE0','B1C0T0E0','B1C0ToE0']
    params = ['ProductionByTechnologyAnnual']
    results_dic = build_dic(scenarios, params)
    df_PbTA = build_PbTA_df(results_dic)
    facts_dic = get_facts(df_PbTA)
    #path_names = {'B1C0TxE0':'CBS','B1C0T0E0':'REF','B1C0ToE0':'OBS'}
    countries_mod = {'AT':'Austria','BE':'Belgium','BG':'Bulgaria','CH':'Switzerland','CY':'Cyrpus','CZ':'Czech Republic','DE':'Germany','DK':'Denmark','EE':'Estonia','ES':'Spain','FI':'Finland','FR':'France','GR':'Greece','HR':'Croatia','HU':'Hungary','IE':'Ireland','IT':'Italy','LT':'Lithuania','LU':'Luxembourg','LV':'Latvia','MT':'Malta','NL':'Netherlands','NO':'Norway','PL':'Poland','PT':'Portugal','RO':'Romania','SE':'Sweden','SI':'Slovenia','SK':'Slovakia','UK':'United Kingdom','EU28':'EU28'}
    fuels = pd.DataFrame({'fuel_name':['WI','HY','BF','CO','BM','WS','HF','NU','NG','OC','OI','GO','SO','EL'],'fuel_abr':['Wind','Hydro','Biofuel','Coal','Biomass','Waste','Oil','Nuclear','Gas','Ocean','Oil','Geo','Solar','Imports']}, columns = ['fuel_name','fuel_abr'])
    fuels = fuels.sort_values(['fuel_name'])
    for region in facts_dic['regions']:
        print(region)
    # selec_region = input('Please select a country from the above listed by typing here:')
    #selec_region = 'DE'
    print(list(colour_schemes.keys()))
    # selec_scheme = input('Please select one of the above listed colour schemes by writing it here and confirming by enter:')
    selec_scheme = 'dES_colours' 
    colours = colour_schemes[selec_scheme]
    figure = create_fig(df_PbTA, scenarios, country, countries_mod, fuels, colours)
    plot(figure)
#%% If executed as script
if __name__ == '__main__':
    selec_region = sys.argv[1]
    scens = sys.argv[2:]
    main(selec_region,scens)