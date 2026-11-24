import ssl
import time

import adafruit_requests
import digitalio
import microcontroller
import neopixel
import rtc
import socketpool
import wifi
import supervisor
from adafruit_datetime import datetime, timezone
from adafruit_debouncer import Debouncer
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.solid import Solid
from adafruit_led_animation.color import BLUE
from adafruit_ntp import NTP

from chronolight.config import get_config
from chronolight.core.classification import Colors
from chronolight.core.models import InputTuple
from chronolight.core.models_utils import state_to_str

UTC = timezone.utc

class Embedded:
    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    __LOG_NAME__ = "UNKNOWN"

    def _log(self, msg):
        print(f"[{self.__LOG_NAME__} HW] {msg}")

    """
    CircuitPython implementation of the Hardware interface
    """

    def buttonPin(self):
        raise NotImplementedError

    def neoPixelPin(self):
        raise NotImplementedError

    def neoPixelCount(self):
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self):
        supervisor.runtime.autoreload = False

        self._log("Initializing hardware")

        # Network / time
        self._pool = None
        self._session = None

        # Cached timezone
        self._timezone = None

        # BOOT button (GPIO0, active low)
        self._button_pin = digitalio.DigitalInOut(self.buttonPin())
        self._button_pin.direction = digitalio.Direction.INPUT
        self._button_pin.switch_to_input(pull=digitalio.Pull.UP)
        self._button = Debouncer(self._button_pin)

        # NeoPixel (onboard, GPIO39)
        self._pixel = neopixel.NeoPixel(self.neoPixelPin(),
                                        self.neoPixelCount(),
                                        brightness=get_config("NEOPIXEL_BRIGHTNESS", 0.5),
                                        auto_write=False)

        self._animation = Solid(self._pixel, color=(0, 0, 255))

        self._log("Init complete (button + neopixel ready)")

    # ------------------------------------------------------------------
    # Identity / Description
    # ------------------------------------------------------------------

    def descr(self):
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Time / Clock
    # ------------------------------------------------------------------

    def now(self):
        """
        Return current UTC time as a datetime object.
        """
        t = rtc.RTC().datetime  # already UTC
        return datetime(
            t.tm_year,
            t.tm_mon,
            t.tm_mday,
            t.tm_hour,
            t.tm_min,
            t.tm_sec,
            tzinfo=timezone.utc
        )

    def local_timezone(self):
        """
        Return local timezone as IANA string (e.g., 'America/Denver').
        Uses IP geolocation once, then caches result.
        """
        if self._timezone:
            self._log(f"Using cached timezone: {self._timezone}")
            return self._timezone

        if not self._session:
            raise RuntimeError("Network not initialized")

        self._log("Fetching timezone from ipinfo.io")

        try:
            response = self._session.get("http://ipinfo.io/json")

            try:
                data = response.json()
                tz = data.get("timezone")

                if not tz:
                    raise RuntimeError("No timezone in response")

                self._timezone = tz
                self._log(f"Detected timezone: {tz}")
                return tz

            finally:
                response.close()

        except Exception as e:
            self._log(f"Timezone fetch failed, defaulting to UTC: {e}")
            self._timezone = "UTC"
            return self._timezone

    _last_ntp_sync = None

    def sync_clock(self):
        if not self._pool:
            raise RuntimeError("Network not initialized")

        if self._last_ntp_sync is not None:
            if time.monotonic() - self._last_ntp_sync < 86400:
                return

        self._log("Syncing clock via NTP...")

        try:
            ntp = NTP(self._pool, tz_offset=0)

            # fetch once
            t = ntp.datetime

            # set system clock
            rtc.RTC().datetime = t

            self._last_ntp_sync = time.monotonic()
            self._log("Clock sync successful")

        except Exception as e:
            self._log(f"Clock sync failed: {e}")

    # ------------------------------------------------------------------
    # Network
    # ------------------------------------------------------------------

    def network(self):
        """
        Connect to WiFi using environment variables:
            WIFI_SSID
            WIFI_PASSWORD
        """
        if wifi.radio.connected:
            self._log("WiFi already connected")
            return

        ssid = get_config("WIFI_SSID")
        password = get_config("WIFI_PASSWORD")

        if not ssid or not password:
            raise RuntimeError("Missing WIFI_SSID / WIFI_PASSWORD")

        self._log("Connecting to WiFi...")
        wifi.radio.connect(ssid, password)
        self._log(f"Connected: {wifi.radio.ipv4_address}")

        self._log("Creating socket pool + HTTP session")
        self._pool = socketpool.SocketPool(wifi.radio)
        self._session = adafruit_requests.Session(self._pool, ssl.create_default_context())

    # ------------------------------------------------------------------
    # Calendar / External Data
    # ------------------------------------------------------------------

    def streamed_calendar(self, url):
        self._log("Connected:" + str(wifi.radio.connected))
        self._log("IP:" + str(wifi.radio.ipv4_address))

        if not self._session:
            raise RuntimeError("Network not initialized")

        self._log("Requesting calendar")

        response = self._session.get(url, stream=True)

        self._log("Streaming calendar")

        try:
            buffer = bytearray()

            chunk_count = 0

            for chunk in response.iter_content(chunk_size=256):
                chunk_count += 1

                if chunk_count % 50 == 0:
                    self._log(f"Processing chunk: {chunk_count}")

                if not chunk:
                    continue

                buffer.extend(chunk)

                while True:
                    newline = buffer.find(b"\n")
                    if newline < 0:
                        break

                    # Extract one complete line.
                    line = bytes(buffer[:newline])

                    # Keep only the unprocessed bytes.
                    buffer = bytearray(buffer[newline + 1:])

                    # ICS uses CRLF line endings.
                    if line.endswith(b"\r"):
                        line = line[:-1]

                    yield line.decode("utf-8")

            # Flush any remaining partial line.
            if buffer:
                line = bytes(buffer)
                if line.endswith(b"\r"):
                    line = line[:-1]
                yield line.decode("utf-8")

        finally:
            response.close()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def get_input(self):
        """
        Return True once when BOOT button is pressed (debounced).
        """
        self._button.update()

        if self._button.fell:
            self._log("Button pressed")
            return InputTuple(True)

        return InputTuple(False)

    # ------------------------------------------------------------------
    # Output / Rendering
    # ------------------------------------------------------------------
    _last_state = None
    def render(self, state):
        """
        Render state to onboard NeoPixel using LED animations.
        """

        if state == self._last_state:
            self._last_state = state
            if self._animation:
                self._animation.animate()
            return

        # -------------------------------------------------
        # Only only update animation if state has changed
        # -------------------------------------------------

        self._log(state_to_str(state))
        self._last_state = state
        classification = state.classification

        # -------------------------------------------------
        # State → Animation mapping
        # -------------------------------------------------

        if classification == 0:  # IDLE
            self._animation = Solid(self._pixel, color=Colors.IDLE)

        elif classification == 1:  # UPCOMING
            self._animation = Solid(self._pixel, color=Colors.UPCOMING)


        elif classification == 2:  # SOON (slow pulse fade)
            self._animation = Blink(self._pixel, speed=0.75, color=Colors.SOON)

        elif classification == 3:  # STARTING (faster pulse fade)
            self._animation = self._animation = Blink(self._pixel, speed=0.5, color=Colors.STARTING)

        elif classification == 4:  # STARTED
            self._animation = Solid(self._pixel, color=Colors.STARTED)

        else:
            self._animation = Solid(self._pixel, color=Colors.OFF)

    # ------------------------------------------------------------------
    # Lifecycle / System Control
    # ------------------------------------------------------------------

    def start_watchdog(self, timeout):
        """
        Start hardware watchdog timer.
        """
        self._log(f"Starting watchdog (timeout={timeout}s)")

        w = microcontroller.watchdog
        w.timeout = timeout

    # noinspection PyMethodMayBeStatic
    # Must override parent class
    def heartbeat(self):
        """
        Feed watchdog to prevent reset.
        """
        try:
            microcontroller.watchdog.feed()

        except Exception:
            pass