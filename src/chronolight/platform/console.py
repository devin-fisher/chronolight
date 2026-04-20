import os
import sys
import threading
import time
from datetime import datetime, UTC

import requests

from chronolight.core.classification import ScheduleClassification
from chronolight.core.models import InputTuple
from chronolight.core.models_utils import state_to_str
from chronolight.platform.interface import Hardware


def _is_key_pressed():
    path = "/tmp/pushed"

    if os.path.exists(path):
        os.remove(path)
        return True

    return False


class ConsoleHardware(Hardware):
    _last_state = None

    def now(self):
        return datetime.now(UTC)

    def streamed_calendar(self, url):
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    yield line.decode("utf-8")

    heartbeat_tick = time.time()

    def local_timezone(self):
        url = "http://ipinfo.io/json"

        response = requests.get(url, timeout=5)
        response.raise_for_status()  # raise error if request failed

        data = response.json()

        return data.get("timezone")

    def get_input(self):
        return InputTuple(_is_key_pressed())

    def heartbeat(self):
        self.heartbeat_tick = time.time()

    def sync_clock(self):
        pass

    def start_watchdog(self, timeout):
        def _check():
            while True:
                time.sleep(timeout / 2)
                # print("[CONSOLE HW] checking heartbeat")
                heartbeat = time.time() - self.heartbeat_tick
                print("[CONSOLE HW] heartbeat time: " + str(heartbeat))
                if heartbeat > timeout:
                    print("[CONSOLE HW] heartbeat timeout")
                    print("[CONSOLE HW] exiting now")
                    sys.exit(-1) # FIXME don't exit correctly

        t = threading.Thread(target=_check)
        t.start()

    def network(self):
        pass

    def descr(self):
        return "Console Hardware"

    def render(self, state):
        if state != self._last_state:
            print("[CONSOLE HW] rendered state: " + state_to_str(state))
            self._last_state = state


