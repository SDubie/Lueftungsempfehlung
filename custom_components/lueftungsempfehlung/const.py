from homeassistant.const import Platform

DOMAIN = "lueftungsempfehlung"

PLATFORMS: list[Platform] = [Platform.SENSOR]

DEFAULT_NAME = "Lüftungsempfehlung"
DEFAULT_MAX_INDOOR_HUMIDITY = 60.0
DEFAULT_MIN_INDOOR_HUMIDITY = 0.0
DEFAULT_MAX_INDOOR_TEMPERATURE = 23.0
DEFAULT_MIN_INDOOR_TEMPERATURE = 18.0
DEFAULT_CRITICAL_INDOOR_HUMIDITY = 70.0
DEFAULT_MAX_INDOOR_DEW_POINT_SPREAD = 2.0
DEFAULT_HUMIDITY_SPIKE_THRESHOLD = 5.0
DEFAULT_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES = 10
DEFAULT_MIN_TEMPERATURE_DELTA = 2.0
DEFAULT_HUMIDITY_HYSTERESIS = 0.3
DEFAULT_TEMPERATURE_HYSTERESIS = 0.5
DEFAULT_REQUIRE_OUTSIDE_COOLER = True
DEFAULT_MIN_ABSOLUTE_HUMIDITY_DELTA = 1.0
DEFAULT_REMINDER_INTERVAL_MINUTES = 60
DEFAULT_REMINDER_MAX_COUNT = 3
DEFAULT_UPDATE_INTERVAL_MINUTES = 5

CONF_NAME = "name"
CONF_INDOOR_TEMPERATURE_ENTITY = "indoor_temperature_entity"
CONF_INDOOR_HUMIDITY_ENTITY = "indoor_humidity_entity"
CONF_OUTDOOR_TEMPERATURE_ENTITY = "outdoor_temperature_entity"
CONF_OUTDOOR_HUMIDITY_ENTITY = "outdoor_humidity_entity"
CONF_WINDOW_ENTITY = "window_entity"
CONF_NOTIFY_DEVICES = "notify_devices"
CONF_MAX_INDOOR_HUMIDITY = "max_indoor_humidity"
CONF_CRITICAL_INDOOR_HUMIDITY = "critical_indoor_humidity"
CONF_MIN_INDOOR_HUMIDITY = "min_indoor_humidity"
CONF_MAX_INDOOR_TEMPERATURE = "max_indoor_temperature"
CONF_MIN_INDOOR_TEMPERATURE = "min_indoor_temperature"
CONF_MAX_INDOOR_DEW_POINT_SPREAD = "max_indoor_dew_point_spread"
CONF_HUMIDITY_SPIKE_THRESHOLD = "humidity_spike_threshold"
CONF_MIN_STRUCTURE_PROTECTION_VENTILATION_MINUTES = (
	"min_structure_protection_ventilation_minutes"
)
CONF_MIN_TEMPERATURE_DELTA = "min_temperature_delta"
CONF_HUMIDITY_HYSTERESIS = "humidity_hysteresis"
CONF_TEMPERATURE_HYSTERESIS = "temperature_hysteresis"
CONF_REQUIRE_OUTSIDE_COOLER = "require_outside_cooler"
CONF_MIN_ABSOLUTE_HUMIDITY_DELTA = "min_absolute_humidity_delta"
CONF_REMINDER_INTERVAL_MINUTES = "reminder_interval_minutes"
CONF_REMINDER_MAX_COUNT = "reminder_max_count"
CONF_UPDATE_INTERVAL_MINUTES = "update_interval_minutes"

ATTR_INDOOR_ABSOLUTE_HUMIDITY = "indoor_absolute_humidity"
ATTR_OUTDOOR_ABSOLUTE_HUMIDITY = "outdoor_absolute_humidity"
ATTR_ABSOLUTE_HUMIDITY_DELTA = "absolute_humidity_delta"
ATTR_INDOOR_DEW_POINT = "indoor_dew_point"
ATTR_OUTDOOR_DEW_POINT = "outdoor_dew_point"
ATTR_REASON = "reason"
ATTR_REASON_DETAIL = "reason_detail"
ATTR_HUMIDITY_RECOMMENDED = "humidity_recommended"
ATTR_TEMPERATURE_RECOMMENDED = "temperature_recommended"
ATTR_STRUCTURE_PROTECTION_ACTIVE = "structure_protection_active"
ATTR_WINDOW_OPEN = "window_open"

STATE_LUEFTEN_NICHT_NOETIG = "lueften_nicht_noetig"
STATE_LUEFTEN_EMPFOHLEN = "lueften_empfohlen"
STATE_LUEFTEN_NICHT_EMPFOHLEN = "lueften_nicht_empfohlen"
STATE_FENSTER_WIEDER_SCHLIESSEN = "fenster_wieder_schliessen"

REASON_TEMPERATURE = "temperatur"
REASON_HUMIDITY = "feuchtigkeit"
REASON_DRYNESS = "trockenheit"
REASON_STRUCTURE_PROTECTION_ACTIVE = "strukturschutz_aktiv"
REASON_DETAIL_CRITICAL_HUMIDITY = "kritische_feuchtigkeit"
REASON_DETAIL_DEW_POINT_RISK = "taupunkt_risiko"
REASON_DETAIL_HUMIDITY_SPIKE = "feuchtigkeits_spitze"
REASON_DETAIL_MIN_VENTILATION_DURATION = "mindestlueftungsdauer"
REASON_OUTDOOR_WARMER_AND_MORE_HUMID = "aussen_waermer_und_feuchter"
REASON_OUTDOOR_WARMER = "aussen_waermer"
REASON_OUTDOOR_MORE_HUMID = "aussen_feuchter"
REASON_INDOOR_TOO_COLD = "innen_zu_kalt"
REASON_TEMPERATURE_AND_HUMIDITY = "temperatur_und_feuchtigkeit"
REASON_TEMPERATURE_AND_DRYNESS = "temperatur_und_trockenheit"
REASON_UNKNOWN = "unbekannt"