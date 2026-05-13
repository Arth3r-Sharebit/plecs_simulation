
import pyplecs
from pyplecs import PlecsServer
def main():
    with PlecsServer("/Users/young/Downloads/Plecs_Simulation_v1.1_test_2/test.v1.1.plecs") as server:
        params_list = [
            {"vin": 10},
            {"vin": 48.0},
        ]
        results = server.simulate_batch(params_list)

if __name__ == "__main__":
    main()
