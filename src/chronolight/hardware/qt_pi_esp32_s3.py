import board

from chronolight.hardware.embedded import Embedded

class QTpyESP32S3Hardware(Embedded):
    __LOG_NAME__ = "QT_PI_EPS32"

    def descr(self):
        return board.board_id

    def buttonPin(self):
        return board.D0

    def neoPixelPin(self):
        return board.NEOPIXEL

    def neoPixelCount(self):
        return 1