import os
import sys
import time
import traceback

from chronolight.core.ics import find_near_events
from chronolight.core.models import StateTuple
from chronolight.core.classification import ScheduleClassification
from chronolight.platform import resolve_hardware

ENV_CAL_PREFIX = "CAL_URL"

# -------------------------------------------------
# Runtime framework (no hardware knowledge)
# -------------------------------------------------
class Runtime:
    TICK_RATE = 0.05
    classifier = ScheduleClassification()

    def __init__(
        self,
        hardware=None,
        heartbeat_timeout=5.0,
        stream_tick=300.0,
    ):
        self.local_tz = None
        self.calendars = None
        self.state = None
        self.hardware = hardware

        self.heartbeat_timeout = heartbeat_timeout
        self.stream_tick = stream_tick

        self._running = False

        self.last_stream = None

    def initialize(self):
        print("[RUNTIME] Finding Calendars")
        self.calendars = []

        i = 0
        while True:
            key = f"{ENV_CAL_PREFIX}_{i:02d}"
            print("looking for " + key)
            value = os.getenv(key)

            if value is None:
                break

            self.calendars.append(value)
            i += 1

        if len(self.calendars) == 0:
            print("[RUNTIME] No Calendars found")
            sys.exit(-1)

        print("[RUNTIME] Calendars Found:" + str(len(self.calendars)))

        print("[RUNTIME] Finding Hardware")

        self.hardware = resolve_hardware(self.hardware)

        print("[RUNTIME] Found Hardware: " + self.hardware.descr())

        print("[RUNTIME] Init Network")

        self.hardware.network()

        print("[RUNTIME] Network Initialized")

        print("[RUNTIME] Sync Clock")

        self.hardware.sync_clock()

        print("[RUNTIME] Clock Synced")

        print("[RUNTIME] Find TimeZone")

        self.local_tz = self.hardware.local_timezone()

        print("[RUNTIME] TimeZone Found")

        print("[RUNTIME] Init Watchdog")

        self.hardware.start_watchdog(self.heartbeat_timeout)

        print("[RUNTIME] Watchdog Initialized")

        pass

    # -----------------------------
    # Main loop
    # -----------------------------
    def run(self):
        print("[RUNTIME] Initiating...")
        self.initialize()

        self._running = True
        print("[RUNTIME] Running")

        while self._running:
            # Clock sync (delegated)
            # print("[RUNTIME] Syncing Clock")
            self.hardware.sync_clock()

            # Collect input
            self.state = self.handle_input(self.state)

            # Stream Calendars
            if self.should_stream():
                print("[RUNTIME] Computing State")
                try:
                    self.state = self.stream_calendars(
                        self.hardware.now(),
                        self.state
                    )
                    self.last_stream = time.monotonic()
                    print("[RUNTIME] State calendars and found near events: " + str(len(self.state.near_events)) )
                except Exception as e:
                    print("[RUNTIME] State Computation Failed: " + str(e))

                    #  CircuitPython don't have traceback
                    if hasattr(sys, "print_exception"):
                        sys.print_exception(e)
                    else:
                        import traceback
                        traceback.print_exception(type(e), e, e.__traceback__)

                    continue
            else:
                classification, uid = ScheduleClassification.classify_events(
                    self.classifier,
                    self.hardware.now(),
                    self.state.near_events
                )

                self.state = StateTuple(
                    classification,
                    uid,
                    self.state.ignored_uids,
                    self.state.near_events
                )
                # Render state
                self.hardware.render(self.state)

                # Heartbeat
                self.hardware.heartbeat()

            # Yield
            time.sleep(self.TICK_RATE)

    def should_stream(self):
        return self.last_stream is None or (time.monotonic() - self.last_stream >= self.stream_tick)

    def stream_calendars(self, now, state):
        rtn_state = StateTuple(
            ScheduleClassification.IDLE,
            "",
            state.ignored_uids if state is not None else [],
            []
        )

        for calendar in self.calendars:
            streamed_cal = self.hardware.streamed_calendar(calendar)
            near_cal_events = find_near_events(now, streamed_cal, self.local_tz)

            rtn_state = StateTuple(
                rtn_state.classification,
                rtn_state.uid,
                rtn_state.ignored_uids,
                rtn_state.near_events + near_cal_events
            )
        return rtn_state

    def handle_input(self, state):
        input_val = self.hardware.get_input()
        if input_val.ignore:
            print("[RUNTIME] " + str(input_val))
            print("[RUNTIME] Input ignoring current event")
            if state.uid is not None:
                state.ignored_uids.append(state.uid)
                self.last_stream = None
        return state

    def classify(self, state, now):
        classification, uid = ScheduleClassification.classify_events(self.classifier, now, state.near_events)
        return StateTuple(
                classification,
                uid,
                state.ignored_uids,
                state.near_events
            )

# -------------------------------------------------
# Entry point
# -------------------------------------------------
if __name__ == "__main__":
    from chronolight.platform.console import ConsoleHardware

    runtime = Runtime(
        hardware=ConsoleHardware(),
        heartbeat_timeout=30.0,
        stream_tick=60,
    )

    runtime.run()