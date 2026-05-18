from connect_server import connect_server_json
from model_obj import JsonSimulation
import numpy as np
import itertools
from tqdm import tqdm
import sys
import math
import time
import datetime
import pathlib
import os
import rich


PATH = pathlib.Path.cwd() / "Output" / "Data"

console = rich.console.Console()
def multi_full_tasks_main():
    


    sess, url = connect_server_json(port=1080)
    jsonsimulation = JsonSimulation(
        sess,
        url=url,
        model_name="test.v1.1",
        time_span="0.00002",
        max_step="1e-8",
        zc_step_size="1e-5",
        freq=6.78e6,
        duty=0.5,
        disable_output=True,
    )
    try:
        jsonsimulation.set_model_initlization()
    except Exception as e:
        console.print(e, style="bold red")
        sys.exit()

    duty_list = np.linspace(0.2, 0.5, 7)
    vin_list = np.linspace(50.0, 400.0, 5)
    k_list = np.linspace(0.2, 0.6, 5)
    rl_list = np.linspace(50.0, 200.0, 4)
    rsa_list = np.linspace(0.2, 6.0, 2)
    rcs_list = np.linspace(0.1, 0.5, 2)

    params = itertools.product(duty_list, vin_list, k_list, rl_list, rsa_list, rcs_list)
    total = (
        len(duty_list)
        * len(vin_list)
        * len(k_list)
        * len(rl_list)
        * len(rsa_list)
        * len(rcs_list)
    )

    for duty, vin, k, rl, rsa, rcs in tqdm(params, desc="进度", total=total):
        freq = np.abs(np.random.normal(loc=6.78e6, scale=3.88e6))
        dynamic_params = {
            "InitializationCommands": {
                "Tinit": 25.1,
                "Csa": 33.5,
                "Rcs": rcs,
                "Rsa": rsa,
                "Vin": vin,
                "RL": rl,
                "k": k,
                "Lt": 1.64e-6,
                "Lr": 2.79e-6,
                "M": k * math.sqrt(1.64e-6 * 2.79e-6),
            }
        }

        if not PATH.exists():
            console.print("[错误] 找不到输出目录, 请检查是否正确配置了输出目录", "bold red")
            raise FileNotFoundError("Output/Data does not exist")

        try:
            jsonsimulation.set_model_fixed_initcommands(dynamic_params)
            jsonsimulation.set_model_declarations(freq=freq, duty=duty)
            jsonsimulation.set_model_filepath(
                str(
                    PATH
                    / str(
                        "freq="
                        + f"{freq / 1e6:.3f}"
                        + "_duty="
                        + str(duty)
                        + "_vin="
                        + str(vin)
                        + "_k="
                        + str(k)
                        + "_rl="
                        + str(rl)
                        + "_rsa="
                        + str(rsa)
                        + "_rcs="
                        + str(rcs)
                    )
                )
            )

            _t = time.time()
            console.print(f"  [计时] simulation starts: {datetime.datetime.now()}s", style="blue")
            jsonsimulation.run_single_simulation()
            console.print(f"  [计时] simulation costs: {time.time() - _t:.1f}s", style="blue")

        except Exception as e:
            console.print(e, style="bold red")
