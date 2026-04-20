class Hardware:
    """
    Abstract interface for interacting with underlying hardware and system services.

    This class defines the contract that platform-specific implementations must fulfill.
    It separates core application logic from hardware/OS concerns such as time, network,
    input, and rendering.

    Implementations may target embedded devices, desktops, or test environments.
    """

    # ------------------------------------------------------------------
    # Identity / Description
    # ------------------------------------------------------------------

    def descr(self):
        """
        Return a human-readable description of the hardware/platform.

        Examples:
            - "Raspberry Pi 4"
            - "Linux Desktop (Test Mode)"
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Time / Clock
    # ------------------------------------------------------------------

    def now(self):
        """
        Return the current time as a timezone-aware datetime in UTC.

        This is the authoritative clock used by the application.
        """
        raise NotImplementedError

    def local_timezone(self):
        """
        Return the system's local timezone.

        Used for converting Floating (no timezone specified) timestamps into UTC.
        """
        raise NotImplementedError

    def sync_clock(self):
        """
        Synchronize the system clock with an external time source (e.g., NTP).

        Implementations may block until synchronization is complete or
        perform a best-effort update.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Network
    # ------------------------------------------------------------------

    def network(self):
        """
        Ensure network connectivity is available.

        This may block until the network is ready or raise an error if
        connectivity cannot be established.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Calendar / External Data
    # ------------------------------------------------------------------

    def streamed_calendar(self, url):
        """
        Stream or retrieve calendar data from the given URL.

        Args:
            url (str): Location of the calendar (e.g., ICS feed).

        Returns:
            Iterable or stream of calendar data lines.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def get_input(self):
        """
        Retrieve user or hardware input.

        Returns:
            InputTuple from hardware input signal (e.g., button press, key event).
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Output / Rendering
    # ------------------------------------------------------------------

    def render(self, state):
        """
        Render the current application state to the hardware output.

        Args:
            state: Application state to display (format defined by caller).
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Lifecycle / System Control
    # ------------------------------------------------------------------

    def start_watchdog(self, timeout):
        """
        Start a watchdog timer that will reset or alert if not periodically serviced.

        Args:
            timeout (int | float): Timeout in seconds before the watchdog triggers.
        """
        raise NotImplementedError

    def heartbeat(self):
        """
        Signal liveness to the watchdog or external observer.

        Should be called periodically to prevent watchdog timeout.
        """
        raise NotImplementedError