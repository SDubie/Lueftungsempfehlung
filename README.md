# Lüftungsempfehlung (Home Assistant)

Diese Custom-Integration hilft dir dabei, das Lüften nicht nach Bauchgefühl, sondern datenbasiert zu steuern. Der Sensor bewertet Temperatur und Luftfeuchte innen/außen und gibt dir eine klare Handlungsempfehlung.

Ziel der Logik:
- Innen nicht zu warm werden lassen
- Innen nicht zu feucht werden lassen
- Innen nicht zu kalt werden lassen
- Ungünstiges Lüften (außen wärmer und feuchter) vermeiden

## Funktionsumfang

- 1 Sensor-Entity mit Klartext-Status
- Status- und Grund-Codes als Attribute für Automationen
- Kurze und lange Grundtexte (`reason_short` und `reason`)
- Optionale Einbindung eines Fenster-/Türkontakts
- Optionale Push-Benachrichtigungen über mobile_app-Geräte
- Erinnerungen für "Lüften empfohlen"
- Konfigurierbares Ruhezeitfenster für Benachrichtigungen (`HH:MM`)
- Externe Stummschaltung über Entität (z. B. `schedule.*`, `input_boolean.*`)
- Hysterese für stabilere Entscheidungen (weniger Hin- und Herwechsel)
- Mehrstufige Konfiguration in Home Assistant (Basis, Benachrichtigungen, Erweitert)

## Konfiguration über config.yaml (optional)

Wenn du den Sensor lieber per YAML anlegst, kannst du ihn in deiner `config.yaml` (oder in einer eingebundenen Datei) so definieren:

```yaml
lueftungsempfehlung:
  name: "Lüftung Wohnbereich"
  indoor_temperature_entity: sensor.wohnzimmer_temperatur
  indoor_humidity_entity: sensor.wohnzimmer_luftfeuchte
  outdoor_temperature_entity: sensor.aussentemperatur
  outdoor_humidity_entity: sensor.aussen_luftfeuchte

  # Optional
  window_entity: binary_sensor.wohnzimmer_fenster
  notify_devices:
    - 0123456789abcdef0123456789abcdef
  reminder_interval_minutes: 60
  reminder_max_count: 3
  notification_silence_start: "22:00"
  notification_silence_end: "07:00"
  notification_silence_entity: schedule.notification_quiet_hours
  require_outside_cooler: true
  min_absolute_humidity_delta: 1.0
  max_indoor_humidity: 60
  critical_indoor_humidity: 70
  min_indoor_humidity: 0
  max_indoor_temperature: 23
  min_indoor_temperature: 18
  max_indoor_dew_point_spread: 2.0
  humidity_spike_threshold: 5.0
  min_temperature_delta: 2.0
  humidity_hysteresis: 0.3
  temperature_hysteresis: 0.5
  update_interval_minutes: 5
  min_structure_protection_ventilation_minutes: 10
```

Danach Home Assistant neu starten. Die Integration wird beim Start importiert und als Config Entry angelegt.

### Mögliche Variablen in YAML

| Variable | Pflicht | Standard | Bedeutung |
| --- | --- | --- | --- |
| `name` | Nein | `Lüftungsempfehlung` | Anzeigename der Integration |
| `indoor_temperature_entity` | Ja | - | Innen-Temperatursensor |
| `indoor_humidity_entity` | Ja | - | Innen-Feuchtesensor |
| `outdoor_temperature_entity` | Ja | - | Außen-Temperatursensor |
| `outdoor_humidity_entity` | Ja | - | Außen-Feuchtesensor |
| `window_entity` | Nein | leer | Fenster-/Türkontakt (binary_sensor) |
| `notify_devices` | Nein | `[]` | Liste von mobile_app-Geräte-IDs für Push |
| `reminder_interval_minutes` | Nein | `60` | Intervall für Erinnerungen bei "Lüften empfohlen" |
| `reminder_max_count` | Nein | `3` | Max. Erinnerungen pro Empfehlungsphase (`0` = aus) |
| `notification_silence_start` | Nein | leer | Start der Ruhezeit für Benachrichtigungen (`HH:MM`) |
| `notification_silence_end` | Nein | leer | Ende der Ruhezeit für Benachrichtigungen (`HH:MM`) |
| `notification_silence_entity` | Nein | leer | Externe Entität für Stummschaltung (`on`/`active` unterdrückt Push) |
| `require_outside_cooler` | Nein | `true` | Temperaturbedingt nur empfehlen, wenn außen kühler ist |
| `min_absolute_humidity_delta` | Nein | `1.0` | Mind. Differenz absolute Feuchte (g/m³) für Feuchte-Lüften |
| `max_indoor_humidity` | Nein | `60` | Obere Feuchtegrenze innen in % |
| `critical_indoor_humidity` | Nein | `70` | Kritische Innenfeuchte für Strukturschutz |
| `min_indoor_humidity` | Nein | `0` | Untere Feuchtegrenze innen in % (`0` deaktiviert "zu trocken") |
| `max_indoor_temperature` | Nein | `23` | Obere Temperaturgrenze innen in °C |
| `min_indoor_temperature` | Nein | `18` | Untere Temperaturgrenze innen in °C (Kälteschutz) |
| `max_indoor_dew_point_spread` | Nein | `2.0` | Max. Abstand Innen-Temperatur zu Innen-Taupunkt (Strukturschutz) |
| `humidity_spike_threshold` | Nein | `5.0` | Schwelle für schnellen Feuchteanstieg (Strukturschutz) |
| `min_temperature_delta` | Nein | `2.0` | Mind. Temperaturdifferenz innen-außen in °C |
| `humidity_hysteresis` | Nein | `0.3` | Hysterese für Feuchteentscheidung (g/m³) |
| `temperature_hysteresis` | Nein | `0.5` | Hysterese für Temperaturentscheidung (°C) |
| `min_structure_protection_ventilation_minutes` | Nein | `10` | Mindestlüftungsdauer, wenn Strukturschutz aktiv war |
| `update_interval_minutes` | Nein | `5` | Aktualisierungsintervall der Berechnung |

## Ausgegebene Stati

Der Sensor gibt genau diese vier Stati aus:

- Lüften nicht nötig
- Lüften empfohlen
- Lüften nicht empfohlen
- Fenster wieder schließen

Zusätzlich im Attribut `status_code`:

- `lueften_nicht_noetig`
- `lueften_empfohlen`
- `lueften_nicht_empfohlen`
- `fenster_wieder_schliessen`

## Wie die Logik entscheidet

### 1) Berechnete Größen

Aus Temperatur und relativer Luftfeuchte werden berechnet:
- absolute Feuchte innen/außen (g/m³)
- Taupunkt innen/außen (nur als Zusatzinfo im Attribut)

Die absolute Feuchte ist die zentrale Größe für die Feuchtebewertung.

### 2) Feuchtebedarf

**Zu feucht innen** (`too_humid`), wenn:
- Innenfeuchte >= `max_indoor_humidity`
- und absolute Feuchte innen - außen >= `min_absolute_humidity_delta` (mit Hysterese)

**Zu trocken innen** (`too_dry`), wenn:
- `min_indoor_humidity` > 0
- und Innenfeuchte <= `min_indoor_humidity`
- und absolute Feuchte außen - innen >= `min_absolute_humidity_delta` (mit Hysterese)

`humidity_recommended = too_humid or too_dry`

### 3) Temperaturbedarf

**Temperaturbedingt lüften empfohlen** (`temperature_recommended`), wenn:
- Innentemperatur >= `max_indoor_temperature`
- und (innen - außen) >= `min_temperature_delta` (mit Hysterese)
- und optional: außen ist kühler als innen (`require_outside_cooler = true`)

### 4) Lüften nicht empfohlen (Sperrbedingungen)

Lüften wird als nicht empfehlenswert eingestuft, wenn mindestens eine Bedingung gilt:

- Außen ist in **absoluter Feuchte** höher als innen
- Außen ist wärmer als innen und es gibt **keinen** Entfeuchtungsvorteil
- Innen ist bereits zu kalt:
  - innen <= `min_indoor_temperature`
  - und außen ist kühler als innen
  - und es gibt **keinen** Entfeuchtungsvorteil

### 5) Finale Statusauswahl

Reihenfolge der Entscheidung:

1. Wenn Sperrbedingung aktiv:
   - Fenster offen -> **Fenster wieder schließen**
   - Fenster geschlossen/kein Fensterkontakt -> **Lüften nicht empfohlen**
2. Sonst, wenn Feuchte- oder Temperaturbedarf aktiv:
   - **Lüften empfohlen**
3. Sonst:
   - Fenster offen -> **Fenster wieder schließen**
   - Fenster geschlossen/kein Fensterkontakt -> **Lüften nicht nötig**

Hinweis: Ist kein Fensterkontakt konfiguriert, wird intern von "Fenster geschlossen" ausgegangen.

## Benachrichtigungen

Wenn `notify_devices` konfiguriert ist:

- Bei Wechsel auf **Lüften empfohlen** wird eine Benachrichtigung gesendet
- Solange der Status gleich bleibt, können Erinnerungen gesendet werden:
  - Intervall: `reminder_interval_minutes`
  - maximale Anzahl: `reminder_max_count`
- Bei Wechsel auf **Fenster wieder schließen** wird ebenfalls benachrichtigt
- Für **Lüften nicht nötig** und **Lüften nicht empfohlen** gibt es keine automatische Push-Meldung bei Statusgleichheit
- Während Ruhezeitfenster (`notification_silence_start`/`notification_silence_end`) werden Benachrichtigungen unterdrückt
- Wenn `notification_silence_entity` auf `on`, `active`, `open`, `home` oder `true` steht, werden Benachrichtigungen ebenfalls unterdrückt

Format der Meldung:
- Nutzt den kurzen Grundtext (`reason_short`), z. B. "Zu feucht"
- Bei Feuchte-Gründen werden absolute Feuchten (g/m³) angezeigt
- Bei anderen Gründen wird weiterhin relative Feuchte (%) angezeigt

Die Ziel-Notify-Services werden aus den mobile_app-Gerätenamen gebildet:
- `notify.mobile_app_<slug_des_geraetenamens>`

## Konfiguration und Wirkung

### Pflichtfelder

- `indoor_temperature_entity`: Innen-Temperatursensor
- `indoor_humidity_entity`: Innen-Feuchtesensor
- `outdoor_temperature_entity`: Außen-Temperatursensor
- `outdoor_humidity_entity`: Außen-Feuchtesensor

### Optionale Felder

- `name` (Standard: `Lüftungsempfehlung`)
  - Anzeigename der Integration/Device

- `window_entity`
  - Fenster-/Türkontakt (binary_sensor)
  - beeinflusst, ob "Fenster wieder schließen" statt "Lüften nicht empfohlen"/"Lüften nicht nötig" ausgegeben wird

- `notify_devices`
  - mobile_app-Geräte für Push-Benachrichtigungen

- `notification_silence_start` und `notification_silence_end`
  - Optionales Ruhezeitfenster im Format `HH:MM`
  - Funktioniert auch über Mitternacht (z. B. `22:00` bis `07:00`)

- `notification_silence_entity`
  - Externe Stummschaltung, z. B. per Schedule-Helper
  - Bei aktivem Zustand (`on`/`active`) werden Push-Benachrichtigungen pausiert

- `update_interval_minutes` (Standard: `5`)
  - Aktualisierungsintervall der Berechnung

### Feuchteparameter

- `max_indoor_humidity` (Standard: `60`)
  - obere Feuchtegrenze innen

- `min_indoor_humidity` (Standard: `0`)
  - untere Feuchtegrenze innen
  - bei `0` ist die "zu trocken"-Logik praktisch deaktiviert

- `min_absolute_humidity_delta` (Standard: `1.0` g/m³)
  - Mindestabstand der absoluten Feuchte, damit Lüften als wirksam gilt

- `humidity_hysteresis` (Standard: `0.3` g/m³)
  - reduziert die Schaltschwelle, wenn zuvor bereits "Lüften empfohlen" aktiv war
  - verhindert zu häufiges Umschalten

### Temperaturparameter

- `max_indoor_temperature` (Standard: `23` °C)
  - ab hier kann temperaturbedingt Lüften empfohlen werden

- `min_indoor_temperature` (Standard: `18` °C)
  - Schutzgrenze gegen weiteres Auskühlen
  - bei Unterschreitung wird Lüften (bei kühlerer Außenluft) nicht empfohlen

- `min_temperature_delta` (Standard: `2.0` °C)
  - minimale Differenz innen-außen für temperaturbedingte Lüftungsempfehlung

- `temperature_hysteresis` (Standard: `0.5` °C)
  - reduziert die Temperaturdifferenz-Schwelle, wenn "Lüften empfohlen" bereits aktiv war

- `require_outside_cooler` (Standard: `true`)
  - wenn aktiv, gibt es temperaturbedingt nur dann eine Empfehlung, wenn außen kühler ist

### Erinnerungsparameter

- `reminder_interval_minutes` (Standard: `60`)
  - Zeit bis zur nächsten Erinnerung bei dauerhaftem Status "Lüften empfohlen"

- `reminder_max_count` (Standard: `3`)
  - maximale Anzahl Erinnerungen pro Empfehlungsphase
  - bei `0` werden keine Erinnerungen gesendet

### Strukturschutz-Parameter

- `critical_indoor_humidity` (Standard: `70`)
  - kritische Innenfeuchte; kann Lüften unabhängig von Komfortbedarf empfehlen

- `max_indoor_dew_point_spread` (Standard: `2.0` °C)
  - aktiviert Strukturschutz bei hohem Taupunkt-/Kondensationsrisiko

- `humidity_spike_threshold` (Standard: `5.0` %)
  - erkennt schnellen Feuchteanstieg im Innenraum

- `min_structure_protection_ventilation_minutes` (Standard: `10`)
  - hält Strukturschutz-Lüftung für eine Mindestdauer aufrecht

## Sensor-Attribute

Wichtige Attribute für Dashboards/Automationen:

- `status_code`
- `reason` (lokalisierter Klartext)
- `reason_short` (kurzer Klartext)
- `reason_code`
- `reason_detail` und `reason_detail_code`
- `indoor_temperature`, `indoor_humidity`
- `outdoor_temperature`, `outdoor_humidity`
- `indoor_absolute_humidity`, `outdoor_absolute_humidity`
- `absolute_humidity_delta`
- `indoor_dew_point`, `outdoor_dew_point`
- `humidity_recommended`
- `temperature_recommended`
- `structure_protection_active`
- `window_open`

## Installation

### Über HACS

Diese Integration ist aktuell nicht direkt im HACS Store gelistet.
Bitte füge sie als benutzerdefiniertes Repository hinzu:

1. HACS öffnen und oben rechts die drei Punkte auswählen.
2. Benutzerdefinierte Repositories wählen.
3. Repository-URL eintragen.
4. Kategorie auf Integration setzen.
5. Repository speichern.
6. Zurück zu HACS -> Integrationen gehen.
7. Nach "Lüftungsempfehlung" suchen, installieren und Home Assistant neu starten.
8. Danach unter "Einstellungen -> Geräte & Dienste -> Integration hinzufügen" einrichten.

Hinweis: Als Repository-URL verwendest du die URL dieses GitHub-Repositories.

### Manuell

1. Ordner `custom_components/lueftungsempfehlung` in deine Home-Assistant-`config`-Struktur kopieren.
2. Home Assistant neu starten.
3. Entweder die Integration über "Einstellungen -> Geräte & Dienste -> Integration hinzufügen" einrichten oder per `config.yaml` importieren (siehe oben).

## Entwicklung und Tests

Eine ausführliche Anleitung für lokale Entwicklungsumgebung, venv-Setup und Testausführung findest du in CONTRIBUTING.md.

## Hinweise für Automationen

- Verwende bevorzugt `status_code` und `reason_code` statt Klartext, damit Automationen sprachunabhängig stabil bleiben.
- Falls bereits Automationen auf ältere Statuscodes gebaut wurden, bitte auf die aktuellen vier Codes umstellen.

## Konfiguration später ändern

Die einmal eingerichtete Konfiguration kannst du jederzeit nachträglich anpassen:

1. In Home Assistant zu "Einstellungen -> Geräte & Dienste" gehen.
2. Die Integration "Lüftungsempfehlung" öffnen.
3. Auf "Konfigurieren" oder das Zahnrad-Menü klicken.
4. Die mehrstufige Konfiguration durchlaufen:
  - Basis
  - Benachrichtigungen
  - Erweiterte Werte

Nach dem Speichern lädt Home Assistant die Integration mit den neuen Werten neu.

## Version

Aktuell laut `manifest.json`: `0.3.0`
