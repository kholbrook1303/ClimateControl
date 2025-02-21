import logging
import time

from enum import Enum
from threading import Thread

log = logging.getLogger(__name__)

class RelayState(Enum):
    Off = 0
    On  = 1

class Controller:
    def __init__(self, sensor, relay):
        self.name                       = None
        self.description                = None
        self.status                     = RelayState.Off
        self.value                      = None

        # Hardware sessions
        self.sensor                     = sensor
        self.relay                      = relay

        # Control
        self.control_enabled            = False
        self.control_method             = None
        self.control_channel            = None
        self.control_device             = None
        self.control_char               = None
        self.control_duration           = 0.0

        # Frequency control
        self.control_frequency          = 0.0
        self.control_offset             = False
        self.frequency_started          = False
        self.frequency_time             = None

        # Threshold control
        self.control_min_channel        = None
        self.control_min_device         = None
        self.control_min_threshold      = 0.0
        self.control_max_channel        = None
        self.control_max_device         = None
        self.control_max_threshold      = 0.0
        self.control_thread             = Thread()

        # Schedule control
        self.control_on_hr              = False
        self.control_off_hr             = False

        # Charts
        self.chart_unit                 = None
        self.chart_range_min            = 0
        self.chart_range_max            = 0
        self.chart_color                = None

    def _initialize(self):
        if isinstance(self.control_offset, int) and self.control_frequency < self.control_offset:
            raise Exception("The control offset {} for {} exceeds the total frequency of {}".format(self.control_offset, self.name, self.control_frequency))

        elif isinstance(self.control_offset, int):
            self.frequency_time = time.time()

    def _controllable(self, relay_state, device):
        if self.status == relay_state and device:
            return True

        return False

    def _control(self, current_time, control_val=None):
        if not self.control_enabled:
            return

        if self.control_method == 'threshold':
            if not control_val:
                log.warning('No control value was provided for {} control!'.format(self.name))
                return

            self._control_theshold(control_val)

        elif self.control_method == 'frequency':
            self._control_frequency(current_time)

        elif self.control_method == 'schedule':
            self._control_schedule(current_time)

    def _control_theshold(self, control_val):
        if control_val <= float(self.control_min_threshold):
            if self._controllable(RelayState.Off, self.control_min_device) and not self.control_thread.is_alive():
                log.warning(
                    '%s (%f%s) has dropped below the threshhold of %f%s' % (
                        self.name.title(),
                        control_val,
                        self.control_char,
                        float(self.control_min_threshold),
                        self.control_char
                        )
                    )

                self.control_thread = self.relay.turn_on_channel(
                    self.control_min_channel, self.control_min_device, True, self.control_duration
                    )
                self.status = RelayState.On

        elif control_val >= float(self.control_max_threshold):
            if self._controllable(RelayState.Off, self.control_max_device) and not self.control_thread.is_alive():
                log.warning(
                    '%s (%f%s) has raised above the threshhold of %f%s' % (
                        self.name.title(),
                        control_val,
                        self.control_char,
                        float(self.control_max_threshold),
                        self.control_char
                        )
                    )

                self.control_thread = self.relay.turn_on_channel(
                    self.control_max_channel, self.control_max_device, True, self.control_duration
                    )
                self.status = RelayState.On

        if self._controllable(RelayState.On, self.control_min_device) and not self.control_thread.is_alive():
            self.relay.turn_off_channel(
                self.control_min_channel, self.control_min_device
                )
            self.status = RelayState.Off

        elif self._controllable(RelayState.On, self.control_max_device) and not self.control_thread.is_alive():
            self.relay.turn_off_channel(
                self.control_max_channel, self.control_max_device
                )
            self.status = RelayState.Off

    def _control_frequency(self, current_time):
        if isinstance(self.control_offset, int) and not self.frequency_started and ((time.time() - self.frequency_time) > self.control_offset):
            self.frequency_started = True
            self.frequency_time = None

        if not self.frequency_time or (time.time() - self.frequency_time) > self.control_frequency:
            if self._controllable(RelayState.Off, self.control_device) and not self.control_thread.is_alive():
                self.control_thread = self.relay.turn_on_channel(
                    self.control_channel, self.control_device, 
                    threaded=True, thread_sleep=self.control_duration
                    )
                self.status = RelayState.On
                self.frequency_time = time.time()

        elif self._controllable(RelayState.On, self.control_device) and not self.control_thread.is_alive():
            self.relay.turn_off_channel(
                self.control_channel, self.control_device
                )
            self.status = RelayState.Off

    def _control_schedule(self, current_time):
        current_hour = current_time.tm_hour
        if current_hour >= self.control_on_hr and current_hour < self.control_off_hr:
            if self._controllable(RelayState.Off, self.control_device):
                self.relay.turn_on_channel(
                    self.control_channel, self.control_device
                    )
                self.status = RelayState.On

        elif self._controllable(RelayState.On, self.control_device):
            self.relay.turn_off_channel(
                self.control_channel, self.control_device
                )
            self.status = RelayState.Off

    def _close(self):
        if self.status == RelayState.On:
            self.relay.turn_off_channel(
                self.control_channel, self.control_device
                )
            self.status = RelayState.Off


class CO2(Controller):
    def __init__(self, sensor, relay):
        super().__init__(sensor, relay)

        self.name               = 'co2'
        self.description        = 'CO2'
        self.chart_unit         = 'ppm'
        self.chart_range_min    = 0
        self.chart_range_max    = 4000
        self.chart_color        = 'cyan'

    def update_sensor_output(self):
        self.value = self.sensor.get_variable('co2')

    def control(self, current_time):
        current_val = self.sensor.get_variable('co2')
        self._control(current_time, current_val)
        self.value = current_val

    def close(self):
        self._close()

class Humidity(Controller):
    def __init__(self, sensor, relay):
        super().__init__(sensor, relay)

        self.name               = 'humidity'
        self.description        = 'Humidity'
        self.chart_unit         = '% RH'
        self.chart_range_min    = 35
        self.chart_range_max    = 100
        self.chart_color        = 'orangered'

    def update_sensor_output(self):
        self.value = self.sensor.get_variable('humidity')

    def control(self, current_time):
        current_val = self.sensor.get_variable('humidity')
        self._control(current_time, current_val)
        self.value = current_val

    def close(self):
        self._close()

class TemperatureFarenheit(Controller):
    def __init__(self, sensor, relay):
        super().__init__(sensor, relay)

        self.name               = 'tempF'
        self.description        = 'Temp Farenheit'
        self.chart_unit         = '&deg;'
        self.chart_range_min    = 50
        self.chart_range_max    = 100
        self.chart_color        = 'lawngreen'

    def update_sensor_output(self):
        self.value = self.sensor.get_variable('tempF')

    def control(self, current_time):
        current_val = self.sensor.get_variable('tempF')
        self._control(current_time, current_val)
        self.value = current_val

    def close(self):
        self._close()

class TemperatureCelsius(Controller):
    def __init__(self, sensor, relay):
        super().__init__(sensor, relay)

        self.name               = 'tempC'
        self.description        = 'Temp Celsius'
        self.chart_unit         = '&deg;'
        self.chart_range_min    = 15
        self.chart_range_max    = 40
        self.chart_color        = 'fuchsia'

    def update_sensor_output(self):
        self.value = self.sensor.get_variable('tempC')

    def control(self, current_time):
        current_val = self.sensor.get_variable('tempC')
        self._control(current_time, current_val)
        self.value = current_val

    def close(self):
        self._close()

class Light(Controller):
    def __init__(self, sensor, relay):
        super().__init__(sensor, relay)

        self.name               = 'light'
        self.description        = 'Light'

    def update_sensor_output(self):
        pass

    def control(self, current_time):
        self._control(current_time, None)

    def close(self):
        self._close()