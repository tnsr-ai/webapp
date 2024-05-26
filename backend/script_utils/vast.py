import re
import json
import sys
import argparse
import os
import time
import typing
import pandas as pd 
import hashlib
from urllib.parse import quote_plus 
from datetime import date, datetime
from dotenv import load_dotenv

import requests
import getpass
import subprocess
from subprocess import PIPE

load_dotenv()
server_url_default = "https://console.vast.ai"
VAST_KEY = os.getenv("VAST_KEY")

def apiurl(subpath: str, query_args: typing.Dict = None, api_key = VAST_KEY, server_url_default = server_url_default) -> str:
    result = None
    query_args["api_key"] = api_key

    if query_args:
        query_json = "&".join(
            "{x}={y}".format(x=x, y=quote_plus(y if isinstance(y, str) else json.dumps(y))) for x, y in
            query_args.items())
        result = server_url_default + "/api/v0" + subpath + "?" + query_json
    else:
        result = server_url_default + "/api/v0" + subpath
    return result

def get_listing():
    try:
        query = {"verified": {"eq": True}, "external": {"eq": False}, "rentable": {"eq": True}}
    except ValueError as e:
        return 1
    
    url = apiurl("/bundles", {"q": query})
    r = requests.get(url)
    r.raise_for_status()
    rows = r.json()["offers"]
    displayable_fields = (
    ("id", "ID", "{}", None, True),
    ("cuda_max_good", "CUDA", "{:0.1f}", None, True),
    ("num_gpus", "N", "{}x", None, False),
    ("gpu_name", "Model", "{}", None, True),
    ("gpu_ram", "VRAM","{:0.1f}", lambda x: int(round(x/1024, 0)), True),
    ("pcie_bw", "PCIE", "{:0.1f}", None, True),
    ("cpu_cores_effective", "vCPUs", "{:0.1f}", None, True),
    ("cpu_ram", "RAM", "{:0.1f}", lambda x: x / 1000, False),
    ("disk_space", "Disk", "{:.0f}", None, True),
    ("discounted_dph_total", "Price", "{:0.4f}", None, True),
    ("dlperf", "DLP", "{:0.1f}", None, True),
    ("dlperf_per_dphtotal", "DLP/$", "{:0.2f}", None, True),
    ("driver_version", "NV Driver", "{}", None, True),
    ("inet_up", "Net_up", "{:0.1f}", None, True),
    ("inet_down", "Net_down", "{:0.1f}", None, True),
    ("reliability2", "R", "{:0.1f}", lambda x: x * 100, True),
    ("duration", "Max_Days", "{:0.1f}", lambda x: x / (24.0 * 60.0 * 60.0), True),
    ("machine_id", "mach_id", "{}", None, True),
    ("verification", "status", "{}", None, True),
    ("direct_port_count", "ports", "{}", None, True),
    ("geolocation", "country", "{}", None, True))
    df  = pd.DataFrame(rows)
    df_ = pd.DataFrame()
    for field_name, display_name, format_string, postprocess, display in displayable_fields:
        df_[display_name] = df[field_name]
        if postprocess:
            df_[display_name] = df_[display_name].apply(postprocess)
    return df_
    