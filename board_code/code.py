from chronolight.app import Runtime

from chronolight.hardware.qt_pi_esp32_s3 import QTpyESP32S3Hardware

def _resolve_hardware():
    board_id = _detect_board_id()

    print("[Detecting Hardware] board_id:", board_id)

    if board_id == "adafruit_qtpy_esp32s3_nopsram":
        return QTpyESP32S3Hardware()

    raise Exception("Unknown board id: " + board_id)

def _detect_board_id():
    try:
        import board
        return getattr(board, "board_id", "unknown")
    except Exception:
        raise Exception("Could not detect board id")

runtime = Runtime(
    _resolve_hardware(),
    heartbeat_timeout=60.0,
    stream_tick=300.0,
)

runtime.run()