import sys
import time

from chronolight.config import get_calendars
from chronolight.core.classification import ScheduleClassification
from chronolight.core.ics import find_near_events
from chronolight.core.models import StateTuple
from chronolight.core.models_utils import state_to_str

TICK_RATE = 0.05

# -------------------------------------------------
# Runtime framework (no hardware knowledge)
# -------------------------------------------------
class Runtime:
    def __init__(
        self,
        hardware,
        heartbeat_timeout=5.0,
        stream_tick=300.0,
    ):
        self.classifier = None
        self.local_tz = None
        self.calendars = None
        self.state = StateTuple(
            ScheduleClassification.IDLE,
            "",
            [],
            []
        )
        self.hardware = hardware

        self.heartbeat_timeout = heartbeat_timeout
        self.stream_tick = stream_tick

        self._running = False

        self.last_stream = None

    # -----------------------------
    # Main Loop
    # -----------------------------
    def run(self):
        print("[RUNTIME] Initiating...")
        self.initialize()

        self._running = True
        print("[RUNTIME] Running")

        while self._running:
            if self._should_stream():
                print("[RUNTIME] Starting Calendar Streams")
                self.stream()
            else:
                self.update()

            # Yield
            time.sleep(TICK_RATE)

    # -----------------------------
    # Initialize Hardware (using config)
    # -----------------------------
    def initialize(self):
        print("[RUNTIME] Hardware: " + self.hardware.descr())

        self.classifier = ScheduleClassification()

        print("[RUNTIME] Finding Calendars")

        self.calendars = get_calendars()

        if len(self.calendars) == 0:
            print("[RUNTIME] No Calendars found")
            sys.exit(-1)

        print("[RUNTIME] Calendars Found:" + str(len(self.calendars)))

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

    # -----------------------------
    # Stream Calendars
    # -----------------------------
    def stream(self):
        try:
            near_events = []

            print("[RUNTIME] Finding near events")
            for calendar in self.calendars:
                print(f"[RUNTIME] Streaming calendar: {calendar}")
                streaming_cal = self._stream_with_updates(
                    self.hardware.streamed_calendar(calendar)
                )

                near_cal_events = find_near_events(
                    self.hardware.now(),
                    streaming_cal,
                    self.local_tz
                )
                near_events.extend(near_cal_events)

            self.state = StateTuple(
                ScheduleClassification.IDLE,
                "",
                self.state.ignored_uids,
                near_events
            )
            self.last_stream = time.monotonic()
            print("[RUNTIME] found near events: " + str(len(self.state.near_events)))
        except Exception as e:
            print("[RUNTIME] State Computation Failed: " + str(e))

            #  CircuitPython don't have traceback
            if hasattr(sys, "print_exception"):
                sys.print_exception(e)
            else:
                import traceback
                traceback.print_exception(type(e), e, e.__traceback__)

    # -----------------------------
    # Update and render state
    # -----------------------------
    def update(self):
        # Clock sync (delegated)
        self.hardware.sync_clock()

        # Collect input
        self.state = self._handle_input(self.state)

        # Classify near event against now (current clock)
        classification, uid = ScheduleClassification.classify_events(
            self.classifier,
            self.hardware.now(),
            self.state.near_events,
            ignore_uids=self.state.ignored_uids
        )

        # Set latest classification to current state
        self.state = StateTuple(
            classification,
            uid,
            self.state.ignored_uids,
            self.state.near_events
        )

        # Render state
        self.hardware.render(self.state)

        # Have a heartbeat
        self.hardware.heartbeat()

    def _should_stream(self):
        return self.last_stream is None or (time.monotonic() - self.last_stream >= self.stream_tick)

    def _stream_with_updates(self, iterable, max_ms=10):
        start = time.monotonic()

        for line in iterable:
            yield line

            if (time.monotonic() - start) * 1000 >= max_ms:
                self.update()
                start = time.monotonic()

    def _handle_input(self, state):
        input_val = self.hardware.get_input()
        if input_val.ignore:
            print("[RUNTIME] " + str(input_val))
            print(f"[RUNTIME] Input ignoring current event: [{state.uid}]")
            if state.uid is not None:
                state.ignored_uids.append(state.uid)
                print("[RUNTIME] Input updated state: " + state_to_str(state))
        return state

# -------------------------------------------------
# Entry point
# -------------------------------------------------
if __name__ == "__main__":
    from chronolight.hardware.console import ConsoleHardware

    runtime = Runtime(
        ConsoleHardware(),
        heartbeat_timeout=30.0,
        stream_tick=60,
    )

    runtime.run()