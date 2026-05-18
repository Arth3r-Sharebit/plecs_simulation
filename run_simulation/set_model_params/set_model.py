from __future__ import annotations
import xmlrpc.client
from typing import TYPE_CHECKING
import math
import json
import requests
from rich.console import Console

console = Console()    

if TYPE_CHECKING:
    from model_obj import Simulation
    from model_obj.json_rpc_model import JsonSimulation

c_template = """
#include <math.h>
static double freq = {freq_val};  /* 开关频率，用于计算周期 T = 1/freq */
static double duty = {d_val};     /* 占空比，用于计算导通时间 t1 */
double T, t1, t2;
"""


def set_model_init(simulation: Simulation):
    simulation.server.plecs.set(simulation.model_name, "TimeSpan", simulation.time_span)
    simulation.server.plecs.set(simulation.model_name, "MaxStep", simulation.max_step)
    simulation.server.plecs.set(
        simulation.model_name, "ZCStepSize", simulation.zc_step_size
    )


def set_model_init_json(jsonsimulation: JsonSimulation):
    response = jsonsimulation.session.post(
        jsonsimulation.url,
        json={
            "jsonrpc": "2.0",
            "method": "plecs.set",
            "params": [jsonsimulation.model_name, "TimeSpan", jsonsimulation.time_span],
            "id": jsonsimulation._get_id(),
        },
    )

    error = response.json().get("error")
    if error:
        console.print(response.json(), style="bold red")
        raise Exception("Model Initialization failed.")

    response = jsonsimulation.session.post(
        jsonsimulation.url,
        json={
            "jsonrpc": "2.0",
            "method": "plecs.set",
            "params": [jsonsimulation.model_name, "MaxStep", jsonsimulation.max_step],
            "id": jsonsimulation._get_id(),
        },
    )

    error = response.json().get("error")
    if error:
        console.print(response.json(), style="bold red")
        raise Exception("Initialization failed.")

    response = jsonsimulation.session.post(
        jsonsimulation.url,
        json={
            "jsonrpc": "2.0",
            "method": "plecs.set",
            "params": [
                jsonsimulation.model_name,
                "ZCStepSize",
                jsonsimulation.zc_step_size,
            ],
            "id": jsonsimulation._get_id(),
        },
    )

    error = response.json().get("error")
    if error:
        console.print(response.json(), style="bold red")
        raise Exception("Initialization failed.")

    return response.json()


def set_model_decimations(jsonsimulation: JsonSimulation, n: int):
    pass


def set_model_fixed_initcommands(simulation: Simulation, init_commands: dict):
    init_commands_set = (
        f"Tinit = {init_commands['InitializationCommands']['Tinit']};\n"
        f"Rcs = {init_commands['InitializationCommands']['Rcs']};\n"
        f"Csa = {init_commands['InitializationCommands']['Csa']};\n"
        f"Rsa = {init_commands['InitializationCommands']['Rsa']};\n"
        f"Vin = {init_commands['InitializationCommands']['Vin']};\n"
        f"RL = {init_commands['InitializationCommands']['RL']};\n"
        f"k = {init_commands['InitializationCommands']['k']};\n"
        f"Lt = {1.64e-6};\n"
        f"Lr = {2.79e-6};\n"
        f"M = {init_commands['InitializationCommands']['k'] * math.sqrt(1.64e-6 * 2.79e-6)};\n"
    )
    simulation.server.plecs.set(
        simulation.model_name, "InitializationCommands", init_commands_set
    )


def set_model_fixed_initcommands_json(
    jsonsimulation: JsonSimulation, init_commands: dict
):
    init_commands_set = (
        f"Tinit = {init_commands['InitializationCommands']['Tinit']};\n"
        f"Rcs = {init_commands['InitializationCommands']['Rcs']};\n"
        f"Csa = {init_commands['InitializationCommands']['Csa']};\n"
        f"Rsa = {init_commands['InitializationCommands']['Rsa']};\n"
        f"Vin = {init_commands['InitializationCommands']['Vin']};\n"
        f"RL = {init_commands['InitializationCommands']['RL']};\n"
        f"k = {init_commands['InitializationCommands']['k']};\n"
        f"Lt = {1.64e-6};\n"
        f"Lr = {2.79e-6};\n"
        f"M = {init_commands['InitializationCommands']['k'] * math.sqrt(1.64e-6 * 2.79e-6)};\n"
    )

    with jsonsimulation.session.post(
        jsonsimulation.url,
        json={
            "jsonrpc": "2.0",
            "method": "plecs.set",
            "params": [
                jsonsimulation.model_name,
                "InitializationCommands",
                init_commands_set,
            ],
            "id": jsonsimulation._get_id(),
        },
    ) as response:
        if response.json().get("error"):
            console.print(response.json(), style="bold red")
            raise Exception("Initialization failed." + str(response.json()))
        return response.json()

    return None


def set_model_declarations(simulation: Simulation, freq: float, duty: float):
    block_path = f"{simulation.model_name}/C-Script"
    simulation.server.plecs.set(
        block_path, "Declarations", c_template.format(freq_val=freq, d_val=duty)
    )


def set_model_declarations_json(
    jsonsimulation: JsonSimulation, freq: float, duty: float
):
    block_path = f"{jsonsimulation.model_name}/C-Script"
    with jsonsimulation.session.post(
        jsonsimulation.url,
        json={
            "jsonrpc": "2.0",
            "method": "plecs.set",
            "params": [
                block_path,
                "Declarations",
                c_template.format(freq_val=freq, d_val=duty),
            ],
            "id": jsonsimulation._get_id(),
        },
    ) as response:
        if response.json().get("error"):
            console.print(response.json(), style="bold red")
            raise Exception("Declarations failed. " + str(response.json()))

        return response.json()

    return None


def run_batch_simulation(simulation: Simulation, params: list):
    return simulation.server.plecs.simulate(simulation.model_name, params)


def run_single_simulation(simulation: Simulation, params: dict):
    return simulation.server.plecs.simulate(simulation.model_name)


def run_single_simulation_json(jsonsimulation: JsonSimulation):
    if jsonsimulation.disable_output:
        with jsonsimulation.session.post(
            jsonsimulation.url,
            json={
                "jsonrpc": "2.0",
                "method": "plecs.simulate",
                "params": [jsonsimulation.model_name],
                "id": jsonsimulation._get_id(),
            },
            stream=True,
        ) as response:
            if response.status_code == 200:
                pass
                # print("Simulation running finished.")
            else:
                raise Exception("Simulation failed. ")

            peek = response.raw.read(200).decode("utf-8")
            console.print(peek, style="yellow")
            # rich.inspect(response.json())

            if '"error"' in peek:
                raise Exception("Simulation failed: Server returned an error.")
            else:
                console.print("Simluation running finised", style="green")
        return None

    else:
        response = jsonsimulation.session.post(
            jsonsimulation.url,
            json={
                "jsonrpc": "2.0",
                "method": "plecs.simulate",
                "params": [jsonsimulation.model_name],
                "id": jsonsimulation._get_id(),
            },
        )
        if response.json().get("error"):
            raise Exception("Simulation failed. " + str(response.json()))

        return response.json()

    # print(response.json()['result']['Time'].__len__())
    # if response.json().get('error'):
    #    raise Exception("Simulation failed. " + str(response.json()))
    # return response.json()


def set_model_filepath_json(jsonsimulation: JsonSimulation, filepath: str):
    blockpath = f"{jsonsimulation.model_name}/To File"
    with jsonsimulation.session.post(
        jsonsimulation.url,
        json={
            "jsonrpc": "2.0",
            "method": "plecs.set",
            "params": [blockpath, "Filename", filepath],
            "id": jsonsimulation._get_id(),
        },
    ) as response:
        if response.json().get("error"):
            raise Exception("Filepath failed. " + str(response.json()))
        return response.json()

    return None
