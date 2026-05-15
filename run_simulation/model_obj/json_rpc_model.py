from model_obj import Simulation
from set_model_params.set_model import set_model_init_json
from set_model_params.set_model import set_model_fixed_initcommands_json
from set_model_params.set_model import set_model_declarations_json
from set_model_params.set_model import run_single_simulation_json
from set_model_params.set_model import set_model_decimations
import json
import requests
from typing import override

class JsonSimulation(Simulation):

    def __init__(self, session: requests.session,
                 url: str,
                 model_name: str,
                 time_span: str,
                 max_step: str,
                 zc_step_size: str,
                 freq: float,
                 duty: float,
                 disable_output: bool):
        self.model_name = model_name
        self.url = url
        self.time_span = time_span
        self.max_step = max_step
        self.zc_step_size = zc_step_size
        self.session = session
        self.freq = freq
        self.duty = duty    
        self.id = 0
        self.disable_output = disable_output
        
    def set_model_initlization(self):
        return set_model_init_json(self)
    

    def set_model_decimation(self, n:int):
        return set_model_decimations(self, n)


    def _get_id(self):
        self.id += 1
        return self.id
    
    @override
    def set_model_fixed_initcommands(self, init_commands):
        return set_model_fixed_initcommands_json(self, init_commands)
    
    @override
    def set_model_declarations(self, freq:float, duty:float):
        return set_model_declarations_json(self, freq, duty)

    @override
    def run_single_simulation(self):
        return run_single_simulation_json(self)