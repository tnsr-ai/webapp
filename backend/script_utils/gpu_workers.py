import sys
sys.path.append("..")

from script_utils.vast import get_listing
import pandas as pd 
import subprocess
import runpod
import numpy as np
import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()
RUNPOD_KEY = os.getenv("RUNPOD_KEY")
VAST_KEY = os.getenv("VAST_KEY")
runpod.api_key = RUNPOD_KEY


def get_gpu_listing():
    try:
        listing = get_listing()
        listing["Cloud"] = ["vast"] * len(listing)
        cmd = "runpodctl get cloud -s -c"
        ls = subprocess.run([cmd], shell=True, capture_output=True, text=True)
        runpod_listing = pd.DataFrame([[y.strip() for y in x.split('\t')] for x in ls.stdout.split('\n')])
        runpod_listing.columns = runpod_listing.iloc[0]
        runpod_listing.drop([0, len(runpod_listing)-1], inplace=True)
        runpod_listing = runpod_listing.reset_index(drop=True)
        drop_col = []
        for index, row in runpod_listing.iterrows():
            if row["MEM GB"] == "":
                runpod_listing.loc[index - 1,'GPU TYPE'] = runpod_listing.loc[index - 1]['GPU TYPE'] + " " +  row['GPU TYPE']
                drop_col.append(index)
            runpod_listing.loc[index,'GPU TYPE'] = row['GPU TYPE'].replace('1x', '').strip()
        runpod_listing.drop(drop_col, inplace=True)
        gpu_details = {}
        for x in runpod.get_gpus():
            gpu_details[x['id']] = x

        for index, row in runpod_listing.iterrows():
            if row["ONDEMAND $/HR"].lower() != "reserved":
                machine_listing = {
                    "ID": 0,
                    "N": 1,
                    "Model": row["GPU TYPE"],
                    "VRAM": gpu_details[row["GPU TYPE"]]['memoryInGb'],
                    "RAM": row["MEM GB"],
                    "vCPUs": row["VCPU"],
                    "Disk": np.inf,
                    "Price": float(row["ONDEMAND $/HR"]),
                    "Cloud": "runpod"
                }
                listing = listing._append(machine_listing, ignore_index = True)
        listing = listing.sort_values(by=["Price"], ascending=True)
        listing["ID"] = listing["ID"].astype(int)
        return listing
    except:
        return None 
    
def smart_split(s, char):
    in_quotes = False
    parts = []
    current = []

    for c in s:
        if c == char and not in_quotes:
            parts.append(''.join(current))
            current = []
        elif c == '"':
            in_quotes = not in_quotes
            current.append(c)
        else:
            current.append(c)

    parts.append(''.join(current))  # add last part

    return parts

def parse_env(envs):
    result = {}
    if (envs is None):
        return result
    env = smart_split(envs,' ')
    prev = None
    for e in env:
        if (prev is None):
          if (e in {"-e", "-p", "-h"}):
              prev = e
          else:
              return result
        else:
          if (prev == "-p"):
            if set(e).issubset(set("0123456789:tcp/udp")):
                result["-p " + e] = "1"
            else:
                return result
          elif (prev == "-e"):
            if True: 
                kv = e.split('=')
                val = kv[1].strip("'\"")
                result[kv[0]] = val
            else:
                return result
          else:
              result[prev] = e
          prev = None
    return result
    
class VastAI():
    def __init__(self, 
                 machine_id, 
                 run_name, 
                 image, 
                 disk_size, 
                 onstart,
                 eta,
                 env = {}, 
                 api_key = VAST_KEY):
        self.machine_id = machine_id
        self.run_name = run_name
        self.image = image 
        self.disk_size = float(disk_size)
        self.onstart = onstart
        self.env = env
        self.api_key = api_key
        self.eta = eta 
        self.run_time = None
        self.instance_id = None
        self.redis_host = None
        self.redis_port = None

    def launch_instance(self):
        self.url = f"https://console.vast.ai/api/v0/asks/{self.machine_id}/?api_key={self.api_key}"
        self.payload = {
            "client_id": "me",
            "image": self.image,
            "env": self.env,
            "price": None,
            "disk": self.disk_size,
            "label": self.run_name,
            "extra": None,
            "onstart": self.onstart,
            "runtype": "ssh_proxy",
            "image_login": None,
            "python_utf8": False,
            "lang_utf8": False,
            "use_jupyter_lab": False,
            "jupyter_dir": None,
            "force": False,
            "cancel_unavail": False,
            "template_hash_id": None,
        }

        self.r = requests.put(self.url, json = self.payload)
        if self.r.status_code == 200:
            self.instance_id = self.r.json()["new_contract"]
            return True
        return False

    def current_status(self):
        self.url = f"https://console.vast.ai/api/v0/instances/{self.instance_id}/?owner=me&api_key={self.api_key}"
        self.r = requests.get(self.url)
        if self.r.status_code != 200:
            return {"detail": "Failed"}
        self.data = self.r.json()
        if self.data["instances"] is None:
            return {"detail": "Success","data": "EXITED"}
        if self.data["instances"]["status_msg"] != None and "error" in self.data["instances"]["status_msg"].lower():
            self.terminate_instance()
            return {"detail": "Failed"}
        try:
            if self.data["instances"]["ports"] != None:
                return {"detail": "Success","data": "RUNNING"}
        except:
            return {"detail": "Success","data": "LOADING"}
    
    def redis_config(self):
        self.url = f"https://console.vast.ai/api/v0/instances/{self.instance_id}/?owner=me&api_key={self.api_key}"
        self.r = requests.get(self.url)
        if self.r.status_code != 200:
            return False
        self.instance_config = self.r.json()
        try:
            self.redis_host = self.instance_config["instances"]["public_ipaddr"]
            self.redis_port = int(self.instance_config["instances"]["ports"]["6379/tcp"][0]["HostPort"])
            return True 
        except:
            return False 
        
    def terminate_instance(self):
        try:
            self.url = f"https://console.vast.ai/api/v0/instances/{self.instance_id}/?api_key={self.api_key}"
            self.r = requests.delete(self.url)
            if self.r.status_code != 200:
                return False
            return True
        except:
            return False 
           

class RunpodIO():
    def __init__(self, 
                 gpu_model, 
                 run_name, 
                 image, 
                 disk_size, 
                 eta, 
                 cuda = "12.0",
                 env = {}, 
                 api_key = RUNPOD_KEY):
        self.gpu_model = gpu_model
        self.run_name = run_name
        self.image = image 
        self.disk_size = disk_size
        self.env = env
        self.eta = eta
        self.api_key = api_key
        self.run_time = None
        self.instance_id = None
        self.redis_host = None
        self.redis_port = None
        self.pod = None
        self.cuda = cuda
        runpod.api_key = api_key

    def launch_instance(self):
        try:
            self.pod = runpod.create_pod(
                name = self.run_name,
                image_name = self.image,
                gpu_type_id = self.gpu_model,
                gpu_count = 1,
                volume_in_gb = self.disk_size,
                ports = "8888/http,666/tcp,6379/tcp",
                allowed_cuda_versions=[self.cuda],
                env=self.env
            )
            self.instance_id = self.pod['id']
            return True 
        except:
            return False
        
    def current_status(self):
        self.data = runpod.get_pod(self.instance_id)
        if self.data == None:
            return {"detail": "Success","data": "EXITED"}
        if self.data['runtime'] == None:
            return {"detail": "Success","data": "LOADING"}
        if self.data['runtime'] != None:
            return {"detail": "Success","data": "RUNNING"}
        

    def redis_config(self):
        try:
            for x in runpod.get_pod(self.instance_id)['runtime']['ports']:
                if x["privatePort"] == 6379:
                    self.redis_port = x["publicPort"]
                    self.redis_host = x["ip"]
                    break
            return True 
        except:
            return False  
    
    def terminate_instance(self):
        try:
            runpod.terminate_pod(self.instance_id)
            return True
        except:
            return False 
        


