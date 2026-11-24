import os
import sys
import tempfile
import threading
import time
from datetime import datetime, UTC

import requests

from chronolight.core.models import InputTuple
from chronolight.core.models_utils import state_to_str, state_to_json
from chronolight.hardware.interface import Hardware


def _is_key_pressed():
    path = "/tmp/pushed"

    if os.path.exists(path):
        os.remove(path)
        return True

    return False


def atomic_write(path, content):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))

    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp, path)

    except:
        os.unlink(tmp)
        raise


class ConsoleHardware(Hardware):
    _last_state = None
    heartbeat_tick = time.time()

    def now(self):
        return datetime.now(UTC)

    def streamed_calendar(self, url):
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    yield line.decode("utf-8")

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

        t = threading.Thread(target=_check, daemon=True)
        t.start()

    def network(self):
        pass

    def descr(self):
        return "Console Hardware"

    def render(self, state):
        if state != self._last_state:
            print("[CONSOLE HW] rendered state: " + state_to_str(state))
            # print("[CONSOLE HW] rendered state: " + state_to_json(state))
            atomic_write("/tmp/chronolight-state", state_to_json(state))
            self._last_state = state

