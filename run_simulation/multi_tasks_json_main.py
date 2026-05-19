from save_data import save_data_and_plot_json
from connect_server import connect_server_json
from model_obj import JsonSimulation
import time
from datetime import datetime
import numpy as np
from scipy.stats.qmc import LatinHypercube
import sys
import math
from tqdm import tqdm
import pathlib

PATH = pathlib.Path.cwd() / "Output" / "Data"


def multi_tasks_json_main():
    session, url = connect_server_json(1080)
    jsonsimulation = JsonSimulation(
        session,
        url=url,
        model_name="test.v1.1",
        time_span="0.02",
        max_step="1e-8",
        zc_step_size="1e-5",
        freq=6.78e6,
        duty=0.5,
        disable_output=False,
    )
    jsonsimulation.set_model_initlization()

    # Freq(10) Duty(7), Vin(5) k(5)(from 0.2) RL(4), Rsa(2), Rcs(2)
    bounds = {
        #         710    540
        "Freq": (5.78e6, 7.78e6),
        "Duty": (0.2, 0.5),
        "Rsa": (0.2, 6.0),
        "Vin": (50.0, 400.0),
        "RL": (50.0, 200.0),
        "k": (0.1, 0.6),
        "Rcs": (0.1, 0.5),
    }
    dim = len(bounds)
    ranges = np.array(list(bounds.values()))  # shape (6, 2)

    # 生成 N 个 LHS 样本（例如 200 个）
    sampler = LatinHypercube(d=dim)
    sample_01 = sampler.random(n=200)  # 值在 [0,1]
    lhs_samples = sample_01 * (ranges[:, 1] - ranges[:, 0]) + ranges[:, 0]

    # print(lhs_samples)

    # 1. 先将 zip 迭代器转为列表（LHS 样本量通常几十到几百，内存完全无压力）

    # 💡 批次级操作可放在这里：如保存结果、释放内存、触发并行任务等
    # save_batch(batch_results)

    for sample in tqdm(lhs_samples, desc="进度"):
        dynamic_params = {
            "InitializationCommands": {
                "Tinit": 25.1,
                "Csa": 33.5,
                "Rcs": sample[6],
                "Rsa": sample[2],
                "Vin": sample[3],
                "RL": sample[4],
                "k": sample[5],
                "Lt": 1.64e-6,
                "Lr": 2.79e-6,
                "M": sample[5] * math.sqrt(1.64e-6 * 2.79e-6),
            }
        }

        jsonsimulation.set_model_fixed_initcommands(dynamic_params)
        jsonsimulation.set_model_declarations(sample[0], sample[1])

        if jsonsimulation.disable_output == True:
            jsonsimulation.set_model_filepath(
                str(
                    PATH
                    / str(
                        "freq="
                        + f"{sample[0] / 1e6:.3f}"
                        + "_duty="
                        + str(sample[1])
                        + "_vin="
                        + str(sample[3])
                        + "_k="
                        + str(sample[5])
                        + "_rl="
                        + str(sample[4])
                        + "_rsa="
                        + str(sample[2])
                        + "_rcs="
                        + str(sample[6])
                    )
                )
            )
        try:
            _t = time.time()
            print(f"  [计时] simulation starts: {datetime.now()}s")
            sim_results = jsonsimulation.run_single_simulation()
            print(f"  [计时] simulation costs: {time.time() - _t:.1f}s")

            if jsonsimulation.disable_output == False:
                save_data_and_plot_json(
                    sim_results,
                    sample[0],
                    sample[1],
                    dynamic_params["InitializationCommands"]["Rcs"],
                    dynamic_params["InitializationCommands"]["Rsa"],
                    dynamic_params["InitializationCommands"]["Csa"],
                    dynamic_params["InitializationCommands"]["Vin"],
                    dynamic_params["InitializationCommands"]["RL"],
                    dynamic_params["InitializationCommands"]["k"],
                    "Correct",
                )

        except Exception as e:
            print(e)
            continue
