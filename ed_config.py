"""Add current scenario from workflow into config.yaml for osemosys2iamc
"""
import sys
import yaml

def read_config(path: str):
    with open(path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.SafeLoader)
    return cfg

def scen2cfg(conf, scen: str):
    conf['scenario'] = scen
    return conf

def write_cfg(conf, path: str):
    with open(path, 'w') as file:
        output = yaml.dump(conf, file)

def main(scen: str, path_in: str, path_out: str):
    orig_config = read_config(path_in)
    new_config = scen2cfg(orig_config, scen)
    write_cfg(new_config, path_out)

if __name__ == "__main__":
    
    args = sys.argv[1:]

    scenario = args[0]
    path_orig_config = args [1]
    path_new_config = args[2]

    if len(args) != 3:
        print("Usage: python ed_config.py <scenario> <input_config> <output_path_config>")
        exit(1)
    
    main(scenario, path_orig_config, path_new_config)