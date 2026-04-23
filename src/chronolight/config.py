import os

class ConfigError(Exception):
    pass

ENV_CAL_PREFIX = "CAL_URL"

KNOWN_PARAMETERS = {
    "WIFI_SSID": {
        "type": str,
        "description": "WiFi SSID",
    },
    "WIFI_PASSWORD": {
        "type": str,
        "description": "WiFi password",
    },
    "CAL_URL_##": {
        "type": str,
        "description": "iCal URL",
    },
    "NEOPIXEL_BRIGHTNESS": {
        "type": float,
        "description": "LED brightness",
    }
}

def _lenient_boolean(value):
    return str(value).lower() in ("1", "true", "yes")


def get_config(name, default=None, env=None):
    print(f"[CONFIG] Asked for {name} with default {default}")

    # 1. must be known
    if name not in KNOWN_PARAMETERS:
        raise ConfigError(f"Unknown config key: {name}")

    meta = KNOWN_PARAMETERS[name]
    raw = os.getenv(name) if env is None else env.get(name)
    # 2. handle missing
    if raw is None:
        if default is not None:
            print(f"[CONFIG] returning default '{default}'")
            return default

        raise ConfigError(
            f"Missing required config: {name}"
        )

    print(f"[CONFIG] returning found value")
    # 3. type conversion
    if "type" in meta:
        try:
            return meta["type"](raw)
        except Exception as e:
            raise ConfigError(
                f"Invalid value for {name}: {raw}\nError: {e}"
            )

    return raw

def get_calendars(env=None):
    rtn = []

    i = 0
    while True:
        key = f"{ENV_CAL_PREFIX}_{i:02d}"
        print("looking for " + key)
        value = os.getenv(key) if env is None else env.get(key)

        if value is None:
            break

        rtn.append(value)
        i += 1

    return rtn