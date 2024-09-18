from enum import Enum
from threading import Thread

class RelayState(Enum):
    Off = 0
    On = 1

class SensorVariable:
    def __init__(self):
        self.name                       = None
        self.description                = None

        self.control_enabled            = False
        self.control_status             = RelayState.Off
        self.control_threaded           = False
        self.control_thread             = Thread()
        self.control_thread_interval    = 0
        self.control_thread_sleep       = 0
        self.control_min_function       = None
        self.control_min_threshold      = 0.0
        self.control_max_function       = None
        self.control_max_threshold      = 0.0
        self.control_char               = None
        self.control_on_hr              = False
        self.control_off_hr             = False

        self.chart_unit                 = None
        self.chart_range_min            = 0
        self.chart_range_max            = 0
        self.chart_color                = None

class CO2(SensorVariable):
    def __init__(self):
        super().__init__()

        self.name               = 'co2'
        self.description        = 'CO2'
        self.chart_unit         = 'ppm'
        self.chart_range_min    = 0
        self.chart_range_max    = 4000
        self.chart_color        = 'cyan'

class Humidity(SensorVariable):
    def __init__(self):
        super().__init__()

        self.name               = 'humidity'
        self.description        = 'Humidity'
        self.chart_unit         = '% RH'
        self.chart_range_min    = 35
        self.chart_range_max    = 100
        self.chart_color        = 'orangered'

class TemperatureFarenheit(SensorVariable):
    def __init__(self):
        super().__init__()

        self.name               = 'tempF'
        self.description        = 'Temp Farenheit'
        self.chart_unit         = '&deg;'
        self.chart_range_min    = 50
        self.chart_range_max    = 100
        self.chart_color        = 'lawngreen'

class TemperatureCelsius(SensorVariable):
    def __init__(self):
        super().__init__()

        self.name               = 'tempC'
        self.description        = 'Temp Celsius'
        self.chart_unit         = '&deg;'
        self.chart_range_min    = 15
        self.chart_range_max    = 40
        self.chart_color        = 'fuchsia'

class Light(SensorVariable):
    def __init__(self):
        super().__init__()

        self.name               = 'light'
        self.description        = 'Light'
    
class ClimateControlVariable(Enum):
    temp        = TemperatureFarenheit()
    tempC       = TemperatureCelsius()
    tempF       = TemperatureFarenheit()
    co2         = CO2()
    humidity    = Humidity()
    light       = Light()