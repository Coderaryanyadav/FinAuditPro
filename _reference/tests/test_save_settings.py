import sys
import os
import json

sys.path.append(os.path.abspath('src'))
from core.config import config, get_default_data_dir

def run_test():
    # 1. Update settings
    config.ca_firm_name = "Persistent Firm Name"
    config.ca_frn = "999999W"
    config.ca_membership_no = "123456"
    config.ca_name = "Persistent Partner"

    settings_path = os.path.join(get_default_data_dir(), "settings.json")
    user_settings = {
        "ca_firm_name": config.ca_firm_name,
        "ca_frn": config.ca_frn,
        "ca_membership_no": config.ca_membership_no,
        "ca_name": config.ca_name
    }
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(user_settings, f, indent=4)
        
    print("Settings written directly to JSON to simulate UI save.")

if __name__ == "__main__":
    run_test()
