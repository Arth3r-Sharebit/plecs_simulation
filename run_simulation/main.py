import xmlrpc.client    # 用于通过 XML-RPC 协议远程控制 PLECS
import itertools        # 用于生成多参数的全组合
import time             # 用于计时
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from save_data import save_data_and_plot
from connect_server import connect_server
from model_obj import Simulation
import sys
from datetime import datetime
import math
from multi_tasks_main import multi_tasks_main
from multi_tasks_json_main import multi_tasks_json_main
from json_main import json_main

FIXED_INIT_COMMANDS = {
    "InitializationCommands":
    {
        "Tinit": 25.1,
        "Csa" : 33.5,
        "Rcs" : 0.2,
        "Rsa": 0.5,
        "Vin": 100,
        "RL" : 115,
        "k"  : 0.6,
    }
}

SINGLE_PARAMS = {
    "InitializationCommands":
    {
        "Tinit": 25.1,
        "Csa" : 33.5,
        "Rcs" : 0.2,
        "Rsa": 0.5,
        "Vin": 100,
        "RL" : 115,
        "k"  : 0.6,
        "Lt": 1.64e-6,
        "Lr": 2.79e-6,
        "M": 0.6*math.sqrt(1.64e-6*2.79e-6)
    }
}

def main():
    server, _ = connect_server(1080)
    simulation = Simulation(server, 
                            model_name = "test.v1.1", 
                            time_span  = "0.02", 
                            max_step   = "3e-7", 
                            zc_step_size = "1e-3",
                            freq       = 6.78e6,
                            duty       = 0.5)
    
    simulation.set_model_fixed_initcommands(FIXED_INIT_COMMANDS)
    simulation.set_model_declarations(simulation.freq, simulation.duty)

    
    try:
        _t = time.time()
        print(f"  [计时] simulation starts: {datetime.now()}s")
        sim_results = simulation.run_single_simulation(SINGLE_PARAMS)
        print(f"  [计时] simulation costs: {time.time()-_t:.1f}s")
        save_data_and_plot(sim_results, simulation.freq, simulation.duty,
                           FIXED_INIT_COMMANDS["InitializationCommands"]["Rcs"],
                           SINGLE_PARAMS["InitializationCommands"]["Rsa"],
                           FIXED_INIT_COMMANDS["InitializationCommands"]["Csa"],
                           SINGLE_PARAMS["InitializationCommands"]["Vin"],
                           SINGLE_PARAMS["InitializationCommands"]["RL"],
                           SINGLE_PARAMS["InitializationCommands"]["k"],
                           'Correct'
        )
    except Exception as e:
        print(e)
        raise 




if __name__ == "__main__":
    multi_tasks_json_main()
