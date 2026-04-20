import time
import os

import wifi
import socketpool
import microcontroller
import board
import digitalio
import neopixel
import ssl
import rtc

import adafruit_requests
from adafruit_ntp import NTP
from adafruit_debouncer import Debouncer
from adafruit_datetime import datetime, timezone

from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.solid import Solid
from adafruit_led_animation.color import BLUE


from chronolight.core.classification import ScheduleClassification, Colors
from chronolight.core.models import InputTuple
from chronolight.core.models_utils import state_to_str

UTC = timezone.utc


def _log(msg):
    print(f"[QT_PI_EPS32 HW] {msg}")


class QTpyESP32S3Hardware:
    """
    CircuitPython implementation of the Hardware interface for QT Py ESP32-S3.
    """

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self):
        _log("Initializing hardware")

        # Network / time
        self._pool = None
        self._session = None

        # Cached timezone
        self._timezone = None

        # BOOT button (GPIO0, active low)
        self._button_pin = digitalio.DigitalInOut(board.D0)
        self._button_pin.direction = digitalio.Direction.INPUT
        self._button_pin.switch_to_input(pull=digitalio.Pull.UP)
        self._button = Debouncer(self._button_pin)

        # NeoPixel (onboard, GPIO39)
        self._pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.25, auto_write=False)

        self._animation = Solid(self._pixel, color=(0, 0, 255))
        self._animation = Pulse(
                self._pixel,
                speed=0.02,
                color=BLUE,
            )
        self.tick()

        # Blink state
        self._last_blink = 0
        self._blink_on = False

        _log("Init complete (button + neopixel ready)")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Identity / Description
    # ------------------------------------------------------------------

    def descr(self):
        return "QT Py ESP32-S3 (CircuitPython)"

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
            _log(f"Using cached timezone: {self._timezone}")
            return self._timezone

        if not self._session:
            raise RuntimeError("Network not initialized")

        _log("Fetching timezone from ipinfo.io")

        try:
            response = self._session.get("http://ipinfo.io/json")

            try:
                data = response.json()
                tz = data.get("timezone")

                if not tz:
                    raise RuntimeError("No timezone in response")

                self._timezone = tz
                _log(f"Detected timezone: {tz}")
                return tz

            finally:
                response.close()

        except Exception as e:
            _log(f"Timezone fetch failed, defaulting to UTC: {e}")
            self._timezone = "UTC"
            return self._timezone

    _last_ntp_sync = None

    def sync_clock(self):
        if not self._pool:
            raise RuntimeError("Network not initialized")

        if self._last_ntp_sync is not None:
            if time.monotonic() - self._last_ntp_sync < 86400:
                return

        _log("Syncing clock via NTP...")

        try:
            ntp = NTP(self._pool, tz_offset=0)

            # fetch once
            t = ntp.datetime

            # set system clock
            rtc.RTC().datetime = t

            self._last_ntp_sync = time.monotonic()
            _log("Clock sync successful")

        except Exception as e:
            _log(f"Clock sync failed: {e}")

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
            _log("WiFi already connected")
            return

        ssid = os.getenv("WIFI_SSID")
        password = os.getenv("WIFI_PASSWORD")

        if not ssid or not password:
            raise RuntimeError("Missing WIFI_SSID / WIFI_PASSWORD")

        _log("Connecting to WiFi...")
        wifi.radio.connect(ssid, password)
        _log(f"Connected: {wifi.radio.ipv4_address}")

        _log("Creating socket pool + HTTP session")
        self._pool = socketpool.SocketPool(wifi.radio)
        self._session = adafruit_requests.Session(self._pool, ssl.create_default_context())

    # ------------------------------------------------------------------
    # Calendar / External Data
    # ------------------------------------------------------------------

    def streamed_calendar(self, url):
        if not self._session:
            raise RuntimeError("Network not initialized")

        _log(f"Downloading calendar: {url}")
        _log("Processing calendar")

        response = self._session.get(url, stream=True)

        try:
            buffer = b""

            chunk_count = 0
            for chunk in response.iter_content(chunk_size=128):
                chunk_count += 1
                if chunk_count % 120 == 0:
                    _log("Processing chunk")

                if not chunk:
                    continue

                buffer += chunk

                # try decode safely
                try:
                    text = buffer.decode("utf-8")
                except UnicodeError:
                    # wait for more bytes if split UTF-8 char
                    continue

                lines = text.split("\n")

                # keep last partial line as bytes
                buffer = lines.pop().encode("utf-8") if lines else b""

                for line in lines:
                    self.tick()
                    yield line

            # flush remaining buffer
            if buffer:
                try:
                    yield buffer.decode("utf-8", "ignore")
                except UnicodeError:
                    pass

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
            _log("Button pressed")
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
            self.tick()
            return

        # -------------------------------------------------
        # Only only update animation if state has changed
        # -------------------------------------------------

        _log(state_to_str(state))
        self._last_state = state
        classification = getattr(state, "classification", 0)

        # -------------------------------------------------
        # State → Animation mapping
        # -------------------------------------------------

        if classification == 0:  # IDLE
            self._animation = Solid(self._pixel, color=Colors.IDLE)

        elif classification == 1:  # UPCOMING
            self._animation = Solid(self._pixel, color=Colors.UPCOMING)


        elif classification == 2:  # SOON (slow pulse fade)
            self._animation = Pulse(
                self._pixel,
                speed=0.02,
                color=Colors.SOON,
            )

        elif classification == 3:  # STARTING (faster pulse fade)
            self._animation = Pulse(
                self._pixel,
                speed=0.08,
                color=Colors.STARTING,
            )

        elif classification == 4:  # STARTED
            self._animation = Solid(self._pixel, color=Colors.STARTED)

        else:
            self._animation = Solid(self._pixel, color=Colors.OFF)


    def tick(self):
        """
        Must be called in main loop.
        """
        if self._animation:
            self._animation.animate()

    # ------------------------------------------------------------------
    # Lifecycle / System Control
    # ------------------------------------------------------------------

    def start_watchdog(self, timeout):
        """
        Start hardware watchdog timer.
        """
        _log(f"Starting watchdog (timeout={timeout}s)")

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