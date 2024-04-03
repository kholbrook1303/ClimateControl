#!/usr/bin/env python
import os
import logging
import time

from threading import Thread

from lib.config import Config
from lib.enums import RelayState
from lib.log import log_init
from lib.grove import SensirionMonitor, GroveRelay, GroveLCD

log = logging.getLogger("ClimateControl")

class ClimateControlMain():

    def __init__(self,log, config):
        self.config = config
        
        self.lcd = GroveLCD(self.config)
        
        self.env_vars = dict()
        
        log.info('Initializing ClimateControl... Please be patient')
        self.lcd.process_lcd('Initializing ClimateControl...')

        # Initialize relay board
        self.relay = GroveRelay(self.config)
        
        # Initialize scd4x
        self.scd4x = SensirionMonitor(self.config)

        log.info('ClimateControl initialized!  Starting climate control automation')
        self.lcd.process_lcd('ClimateControl Initialized!')
        
        self.co2 = None
        self.temp = None
        self.humidity = None

    def run(self):
        # Set the starting hour
        previous_hour = -1
        
        for env_var in self.config.general['env_variables']:
            env_config = getattr(self.config, env_var)
            
            self.env_vars[env_var] = env_config
            self.env_vars[env_var]['status'] = RelayState.Off
            self.env_vars[env_var]['thread'] = Thread()

        self.scd4x.read_wait_scd4x()
        self.co2, self.temp, self.humidity = self.scd4x.get_env_vars()
        
        while True:
            self.scd4x.read_wait_scd4x()
                
            deviations = 0
            current_time = time.localtime(time.time())
            current_hour = current_time.tm_hour
                
            for env, env_config in self.env_vars.items():
                try:
                    enable_min_function = False
                    enable_max_function = False
                
                    # Check environment variable for deviations
                    if env_config.get('on_hr'):
                        if current_hour >= env_config['on_hr'] and current_hour < env_config['off_hr']:
                            enable_min_function = True
                        
                    else:
                        comparative = None
                        if env == 'env_temp':
                            comparative = self.temp
                            
                            if self.temp != self.scd4x.tempF:
                                deviations += 1
                                self.temp = self.scd4x.tempF
                                
                        elif env == 'env_humidity':
                            comparative = self.humidity
                            
                            if self.humidity != self.scd4x.humidity:
                                deviations += 1
                                self.humidity = self.scd4x.humidity
                                
                        elif env == 'env_co2':
                            comparative = self.co2
                            
                            if self.co2 != self.scd4x.co2:
                                deviations += 1
                                self.co2 = self.scd4x.co2
                        
                        if comparative <= float(env_config['min_threshold']):
                            enable_min_function = True
                            if env_config['status'] == RelayState.Off:
                                log.warning(
                                    '%s (%f%s) has dropped below the threshhold of %f%s' % (
                                        env.title(),
                                        comparative,
                                        env_config['char'],
                                        float(env_config['min_threshold']),
                                        env_config['char']
                                        )
                                    )
                        
                        elif comparative >= float(env_config['max_threshold']):
                            enable_max_function = True
                            if env_config['status'] == RelayState.On:
                                log.warning(
                                    '%s (%f%s) has raised above the threshhold of %f%s' % (
                                        env.title(),
                                        comparative,
                                        env_config['char'],
                                        float(env_config['max_threshold']),
                                        env_config['char']
                                        )
                                    )
                                
                    if not env_config['enable']:
                        continue

                    min_function = getattr(self.config, env_config['min_function'], None)
                    max_function = getattr(self.config, env_config['max_function'], None)
                    
                    # Manage environment variable power
                    if env_config['status'] == RelayState.Off:
                        if enable_min_function and min_function:
                            self.relay.turn_on_channel(
                                min_function['channel'], min_function['device'], env_config
                                )
                        elif enable_max_function and max_function:
                            self.relay.turn_on_channel(
                                max_function['channel'], max_function['device'], env_config
                                )
                            
                    elif env_config['status'] == RelayState.On:
                        if env_config['threaded'] and not env_config['thread'].is_alive():
                            if min_function:
                                self.relay.turn_off_channel(
                                    min_function['channel'], min_function['device'], env_config
                                    )
                            if max_function:
                                self.relay.turn_off_channel(
                                    max_function['channel'], max_function['device'], env_config
                                    )
                                
                        elif not env_config['threaded'] and not enable_min_function and not enable_max_function:
                            if min_function:
                                self.relay.turn_off_channel(
                                    min_function['channel'], min_function['device'], env_config
                                    )
                            if max_function:
                                self.relay.turn_off_channel(
                                    max_function['channel'], max_function['device'], env_config
                                    )
                        
                except:
                    log.exception('Failed to process environment variable: {}'.format(env))
            
            if deviations > 0 or previous_hour != current_hour:
                self.lcd.process_lcd(
                    '{}ppm {}F {}%RH'.format(self.co2, self.temp, self.humidity),
                    0, 0, 100
                    )
                log.info(
                    '{}ppm {}F {}%RH'.format(
                        self.co2, self.temp, self.humidity
                        )
                    )
                
                if previous_hour != current_hour:
                    previous_hour = current_hour

    def close(self):
        self.lcd.process_lcd('De-initializing ClimateControl...', 255, 0, 0)
        log.info('De-initializing ClimateControl... Please be patient')
        
        self.scd4x.close()
        
        self.lcd.process_lcd('ClimateControl De-initialized', 255, 0, 0)
        time.sleep(2)
        
        self.lcd.process_lcd('ClimateControl is offline', 255, 0, 0)

def main ():
    config = Config()
    log_init('climate_control.log', config.general['log_level'])
    log_init('console', config.general['log_level'])
    mphdl = ClimateControlMain(log, config)
            
    try:
        mphdl.run()
    except KeyboardInterrupt:
        log.info('User exited ClimateControl!')
    except:
        log.exception('Unhandled exception!')
    finally:
        mphdl.close()
    
if __name__ == "__main__":
    main()