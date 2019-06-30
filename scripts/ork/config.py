# persistent configuration

import json

def load(configpath):
    inpstr = ""
    load_dict = dict()
    ########################
    try:
        with open(str(configpath),"r") as f:
            inpstr = f.read()
            load_dict = json.loads(inpstr)
    except:
        pass
    ########################
    return load_dict


def merge(configpath,defaults):
    inpstr = ""
    overlay_dict = dict()
    ########################
    try:
        with open(str(configpath),"r") as f:
            inpstr = f.read()
            overlay_dict = json.loads(inpstr)
    except:
        pass
    ########################
    config_dict = dict(defaults, **overlay_dict)
    with open(str(configpath),"w") as f:
        f.write(json.dumps(config_dict, sort_keys=True, indent=4 ))
    return config_dict
