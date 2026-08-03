import sys
import os

sys.path.append(os.path.abspath('src'))
from core.config import AppConfig

def run_test():
    # Load config from JSON directly through load method
    config = AppConfig.load()
    
    print("Loaded CA Firm Name:", config.ca_firm_name)
    assert config.ca_firm_name == "Persistent Firm Name"
    assert config.ca_frn == "999999W"
    print("Persistence test passed.")

if __name__ == "__main__":
    run_test()
