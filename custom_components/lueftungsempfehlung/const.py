from homeassistant.const import Platform

DOMAIN = "lueftungsempfehlung"

PLATFORMS: list[Platform] = [Platform.SENSOR]

DEFAULT_NAME = "Lüftungsempfehlung"
DEFAULT_MAX_INDOOR_HUMIDITY = 60.0
DEFAULT_MIN_INDOOR_HUMIDITY = 0.0
DEFAULT_MAX_INDOOR_TEMPERATURE = 23.0
DEFAULT_MIN_TEMPERATURE_DELTA = 2.0
DEFAULT_HUMIDITY_HYSTERESIS = 0.3
DEFAULT_TEMPERATURE_HYSTERESIS = 0.5
DEFAULT_REQUIRE_OUTSIDE_COOLER = True
DEFAULT_MIN_ABSOLUTE_HUMIDITY_DELTA = 1.0
DEFAULT_UPDATE_INTERVAL_MINUTES = 5

CONF_NAME = "name"
CONF_INDOOR_TEMPERATURE_ENTITY = "indoor_temperature_entity"
CONF_INDOOR_HUMIDITY_ENTITY = "indoor_humidity_entity"
CONF_OUTDOOR_TEMPERATURE_ENTITY = "outdoor_temperature_entity"
CONF_OUTDOOR_HUMIDITY_ENTITY = "outdoor_humidity_entity"
CONF_WINDOW_ENTITY = "window_entity"
CONF_MAX_INDOOR_HUMIDITY = "max_indoor_humidity"
CONF_MIN_INDOOR_HUMIDITY = "min_indoor_humidity"
CONF_MAX_INDOOR_TEMPERATURE = "max_indoor_temperature"
CONF_MIN_TEMPERATURE_DELTA = "min_temperature_delta"
CONF_HUMIDITY_HYSTERESIS = "humidity_hysteresis"
CONF_TEMPERATURE_HYSTERESIS = "temperature_hysteresis"
CONF_REQUIRE_OUTSIDE_COOLER = "require_outside_cooler"
CONF_MIN_ABSOLUTE_HUMIDITY_DELTA = "min_absolute_humidity_delta"
CONF_UPDATE_INTERVAL_MINUTES = "update_interval_minutes"

ATTR_INDOOR_ABSOLUTE_HUMIDITY = "indoor_absolute_humidity"
ATTR_OUTDOOR_ABSOLUTE_HUMIDITY = "outdoor_absolute_humidity"
ATTR_ABSOLUTE_HUMIDITY_DELTA = "absolute_humidity_delta"
ATTR_INDOOR_DEW_POINT = "indoor_dew_point"
ATTR_OUTDOOR_DEW_POINT = "outdoor_dew_point"
ATTR_REASON = "reason"
ATTR_HUMIDITY_RECOMMENDED = "humidity_recommended"
ATTR_TEMPERATURE_RECOMMENDED = "temperature_recommended"
ATTR_WINDOW_OPEN = "window_open"

STATE_JETZT_LUEFTEN = "jetzt_lueften"
STATE_WEITER_LUEFTEN = "weiter_lueften"
STATE_NICHT_MEHR_LUEFTEN = "nicht_mehr_lueften"
STATE_ALLES_OK = "alles_ok"

REASON_TEMPERATURE = "temperatur"
REASON_HUMIDITY = "feuchtigkeit"
REASON_DRYNESS = "trockenheit"
REASON_TEMPERATURE_AND_HUMIDITY = "temperatur_und_feuchtigkeit"
REASON_TEMPERATURE_AND_DRYNESS = "temperatur_und_trockenheit"
REASON_UNKNOWN = "unbekannt"