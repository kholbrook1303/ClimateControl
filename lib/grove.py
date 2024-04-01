import logging
import math
from threading import Thread
from lib.enums import RelayState
import smbus
import time

from grove_rgb_lcd import setRGB, setText
from grovepi import dht, analogRead
from sensirion_i2c_driver import LinuxI2cTransceiver, I2cConnection
from sensirion_i2c_scd import Scd4xI2cDevice

from lib.common import celsiusToFarenheit

log = logging.getLogger(__name__)

def read_dht(port, model, farenheit=True):
    while True:
        try:
            [temp,humidity] = dht(port, model)
            if math.isnan(temp) == False and math.isnan(humidity) == False:
                if farenheit:
                    return [celsiusToFarenheit(temp), humidity]

                return [temp,humidity]
        except Exception as e:
            log.error("Failed to read DHT sensor!")

def read_oxygen_voltage(sensor_port, voltage_ref):
    vsum = 0
    max_times = 32

    for tries in range(max_times):
        voltage = analogRead(sensor_port)
        if (voltage * (float(voltage_ref) / 1023.0)) > 5.0:
            max_times -= 1
        else:
            vsum += voltage
            
    vsum /= max_times
    voltage = (vsum * (float(voltage_ref) / 1023.0))
    
    if voltage > 5.0:
        return None
    
    return voltage

def calculate_oxygen_percent(sensor_port, voltage_ref):
    voltage = read_oxygen_voltage(sensor_port, voltage_ref)
    O2percent = (((voltage * .21) / 2)*100)
    return round(O2percent, 2)

class GroveRelay(object):
    def __init__(self, config):
        self.config = config
        
        self.i2c_address = self.config.general['grove_relay_bus']
        self.i2c_command = self.config.general['grove_relay_command']
        self.channel_state = 0
        
        self.bus = smbus.SMBus(self.config.general['i2c_bus'])
        self.bus.write_byte_data(self.i2c_address, self.i2c_command, self.channel_state)
        
    def _manage_sleep(self, sleep_timer):
        if sleep_timer > 0:
            time.sleep(sleep_timer)
            
    def _thread_function(self, func, *args, **kwargs):
        thread = Thread(
            target=func,
            args=args,
            kwargs=kwargs
            )
        thread.daemon = True
        thread.start()
        
        return thread
        
    def _turn_on_channel(self, channel, device, env_config, sleep_timer):
        self.channel_state |= (1 << (channel - 1))
        
        log.info('Enabling channel:{} Device:{}'.format(channel, device))
        self.bus.write_byte_data(self.i2c_address, self.i2c_command, self.channel_state)
        env_config['status'] = RelayState.On
        
        self._manage_sleep(sleep_timer)

    def _turn_off_channel(self, channel, device, env_config, sleep_timer):
        self.channel_state &= ~(1 << (channel - 1))
        
        log.info('Disabling channel:{} Device:{}'.format(channel, device))
        self.bus.write_byte_data(self.i2c_address, self.i2c_command, self.channel_state)
        env_config['status'] = RelayState.Off
        
        self._manage_sleep(sleep_timer)
        
    def turn_on_channel(self, channel, device, env_config):
        if env_config['threaded']:
            thread = self._thread_function(self._turn_on_channel, *(channel, device, env_config, env_config['thread_sleep']))
            env_config['thread'] = thread
        else:
            self._turn_on_channel(channel, device, env_config, 0)
        
    def turn_off_channel(self, channel, device, env_config):
        self._turn_off_channel(channel, device, env_config, False)
        
# https://sensirion.github.io/python-i2c-scd/
class SensirionMonitor(object):
    def __init__(self, i2c_port, altitude, calibrate=False, target_ppm=400):
        self.co2 = 0.0
        self.tempC = 0.0
        self.tempF = 0.0
        self.humidity = 0.0
        
        self.serial = None
        
        self.i2c_transceiver = LinuxI2cTransceiver(i2c_port)
        
        # Create SCD4x device
        self.scd4x = Scd4xI2cDevice(I2cConnection(self.i2c_transceiver))

        # Make sure measurement is stopped
        self.scd4x.stop_periodic_measurement()
        
        self.serial = self.scd4x.read_serial_number()
        log.debug("scd4x Serial Number: {}".format(self.serial))
        
        # Set auto-calibration mode
        sensor_auto_calibration = self.scd4x.get_automatic_self_calibration()
        if sensor_auto_calibration:
            log.info('Setting scd4x sensor self calibration mode to False')
            self.scd4x.set_automatic_self_calibration(False)
            
        # set altitude of senser for pressure compensation
        sensor_altitude = self.scd4x.get_sensor_altitude()
        if sensor_altitude != altitude:
            log.info('Setting scd4x sensor altitude to {}'.format(altitude))
            self.scd4x.set_sensor_altitude(altitude)
        
        # Start a new measurement
        self.scd4x.start_periodic_measurement()
            
        if calibrate:
            self._calibrate(target_ppm)
        
    def _calibrate(self, target_ppm):     
        elapsed = 0   
        start = time.time()
        
        # Run standard operation for 3 minutes
        while elapsed <= (60*3):
            self.read_scd4x()
            
            elapsed = time.time() - start
            time.sleep(1)
            
        # Make sure measurement is stopped
        self.scd4x.stop_periodic_measurement()
        
        # Perform forced recalibration
        self.scd4x.perform_forced_recalibration(target_ppm)
        
        # Start a new measurement
        self.scd4x.start_periodic_measurement()
    
    def get_env_vars(self, fahrenheit=True):
        temp = self.tempC
        if fahrenheit:
            temp = self.tempF
            
        return (
            round(self.co2, 2), 
            round(temp, 2),
            round(self.humidity, 2)
        )
        
    def read_scd4x(self, farenheit=True):
        # Ensure status is ready to read, then read variables
        if self.scd4x.get_data_ready_status():
            co2, temp, humidity = self.scd4x.read_measurement()
            
            self.co2 = co2.co2
            self.tempC =temp.degrees_celsius
            self.tempF = temp.degrees_fahrenheit
            self.humidity = humidity.percent_rh
            
            return True
        
        return False
    
    def read_wait_scd4x(self, max_wait=60):
        attempt = 0
        while not self.read_scd4x():
            attempt += 1
            time.sleep(1)
            
            if attempt >= max_wait:
                raise Exception("Reached max attempts of {0} reading the scd4x!".format(max_wait))
            
        return True

    def close(self):
        self.i2c_transceiver.close()

        
def process_lcd(text, max_rows, max_chars, r=255, g=0, b=0, scrolling=False):   
    # NOT IMPLEMENTED #
    return
    total_chars = len(text)
    if total_chars > (max_chars * max_rows):
        raise Exception("There are too many characters for the screen!")
        
    segments = text.split(' ')

    rows = []
    temp_text = ''
    for segment in segments:
        pad = ' ' * (max_chars - len(temp_text))
        if (len(segment) + len(temp_text)) > max_chars:
            rows.append(temp_text + pad)
            temp_text = ''
        elif (len(segment) + len(temp_text) + 1) > max_chars:
            rows.append(temp_text + pad)
            temp_text = ''

        temp_text += segment + ' '
            
    rows.append(temp_text)

    setRGB(r, g, b)
    setText(''.join(rows))