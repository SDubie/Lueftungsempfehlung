from homeassistant.const import Platform

DOMAIN = "lueftungsempfehlung"

PLATFORMS: list[Platform] = [Platform.SENSOR]

DEFAULT_NAME = "Lüftungsempfehlung"
DEFAULT_REQUIRE_OUTSIDE_COOLER = True
DEFAULT_MIN_ABSOLUTE_HUMIDITY_DELTA = 1.0
DEFAULT_UPDATE_INTERVAL_MINUTES = 5

CONF_NAME = "name"
CONF_INDOOR_TEMPERATURE_ENTITY = "indoor_temperature_entity"
CONF_INDOOR_HUMIDITY_ENTITY = "indoor_humidity_entity"
CONF_OUTDOOR_TEMPERATURE_ENTITY = "outdoor_temperature_entity"
CONF_OUTDOOR_HUMIDITY_ENTITY = "outdoor_humidity_entity"
CONF_REQUIRE_OUTSIDE_COOLER = "require_outside_cooler"
CONF_MIN_ABSOLUTE_HUMIDITY_DELTA = "min_absolute_humidity_delta"
CONF_UPDATE_INTERVAL_MINUTES = "update_interval_minutes"

ATTR_INDOOR_ABSOLUTE_HUMIDITY = "indoor_absolute_humidity"
ATTR_OUTDOOR_ABSOLUTE_HUMIDITY = "outdoor_absolute_humidity"
ATTR_ABSOLUTE_HUMIDITY_DELTA = "absolute_humidity_delta"
ATTR_INDOOR_DEW_POINT = "indoor_dew_point"
ATTR_OUTDOOR_DEW_POINT = "outdoor_dew_point"
ATTR_REASON = "reason"

STATE_RECOMMENDED = "recommended"
STATE_NOT_RECOMMENDED = "not_recommended"