from chronolight.app import Runtime
from chronolight.platform.qt_pi_esp32_s3 import QTpyESP32S3Hardware
import supervisor

supervisor.runtime.autoreload = False

runtime = Runtime(
    hardware=QTpyESP32S3Hardware(),
    heartbeat_timeout=60.0,
    stream_tick=300.0,
)

runtime.run()