from model_obj.json_rpc_model import JsonSimulation
from connect_server.connect_server import connect_server_json
import sys
import math
import time
import datetime

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

def json_main():
    session, url = connect_server_json(1080)
    jsonsimulation = JsonSimulation(session, 
                                    url          = url,
                                    model_name   = "test.v1.1", 
                                    time_span    = "0.02", 
                                    max_step     = "1e-8", 
                                    zc_step_size = "1e-5", 
                                    freq         = 6.78e6, 
                                    duty         = 0.5
                                    )
    
    try:
        res_init = jsonsimulation.set_model_initlization()
        res_init_fixed = jsonsimulation.set_model_fixed_initcommands(FIXED_INIT_COMMANDS)
        res_dec = jsonsimulation.set_model_declarations(jsonsimulation.freq, jsonsimulation.duty)
        print("time: " + str(datetime.datetime.now()))
        _t = time.time()
        res_single = jsonsimulation.run_single_simulation()
        print(f"[计时] simulation costs: {time.time()-_t:.1f}s")

        

    except Exception as e:
        print(f"[-] Initialization Error: {e}")
        print("[!] Please check your model path and JSON-RPC settings.")
    # 使用 1 表示异常退出
        sys.exit(1) 





    