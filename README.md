# Chronolight

Chronolight is a lightweight embedded system for displaying upcoming and current meetings from calendar (ICS) feeds on an ESP32-S3.

It is designed to render meeting state onto a single NeoPixel LED, providing a minimal always-on visual indicator of schedule status.

## Features

- Displays upcoming calendar events from ICS feeds
- Indicates current meeting state
- Simple visual output using a single NeoPixel
- Designed for low-power, always-on embedded use
- Built for CircuitPython on ESP32-S3

## Hardware Target

- ESP32-S3 only
- Single WS2812 / NeoPixel LED

## Display Model

Chronolight reduces calendar state into a single LED output:

- Idle / no upcoming meeting → steady color 
- Upcoming meeting → pulsing or warming indicator
- Active meeting → solid alert color
- Transition states → optional pulse/fade animations

## Status

Early development / experimental

## Future Ideas

- Configurable color themes
- Meeting urgency scaling (time-to-event)
- WiFi sync intervals optimization
- Offline caching of calendar data

## License

MIT License
