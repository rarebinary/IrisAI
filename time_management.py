import time
from utils import load_toml_as_dict
from config_loader import get_config


class TimeManagement:
    def __init__(self):
        self.thresholds = load_toml_as_dict("cfg/time_tresholds.toml") or {}
        self.states = {key: time.time() for key in self.thresholds.keys()}

    def start(self):
        current_time = time.time()
        self.states = {key: current_time for key in self.thresholds}

    def check_time(self, check_type):
        current_time = time.time()
        threshold = self.thresholds.get(check_type)
        if threshold is None:
            return False
        last_check = self.states.get(check_type, 0)
        if (current_time - last_check) >= threshold:
            self.states[check_type] = current_time
            return True
        return False

    def state_check(self):
        return self.check_time('state_check')

    def no_detections_check(self):
        return self.check_time('no_detections')

    def idle_check(self):
        return self.check_time("idle")
