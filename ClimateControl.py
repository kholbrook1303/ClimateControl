#!/usr/bin/env python
import logging
import signal
import time

import lib.controllers

from lib.config import Config
from lib.controllers import RelayState
from lib.log import log_init
from lib.grove import SensirionMonitor, GroveRelay, GroveLCD

log = logging.getLogger("ClimateControl")

class SignalMonitor:
    exit = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.set_exit)
        signal.signal(signal.SIGTERM, self.set_exit)

    def set_exit(self, signum, frame):
        self.exit = True

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

    def run(self):
        sm = SignalMonitor()

        # Set the starting hour
        previous_hour = -1
        
        for var in self.config.general['env_variables']:
            try:
                controller = getattr(lib.controllers, var)(self.scd4x, self.relay)

                for key, val in getattr(self.config, var).items():
                    setattr(controller, key, val)

                self.env_vars[var] = controller

            except:
                log.exception('Unable to load {} as there is no ClimateControlVariable for it'.format(var))

        self.scd4x.read_wait_scd4x()

        for var, controller in self.env_vars.items():
            controller._initialize()
            controller.update_sensor_output()
        
        while not sm.exit:
            self.scd4x.read_wait_scd4x()
                
            deviations = 0
            current_time = time.localtime(time.time())
            current_hour = current_time.tm_hour
                
            for var, controller in self.env_vars.items():
                try:
                    controller.control(current_time)
                        
                except:
                    log.exception('Failed to process environment variable: {}'.format(var))

            self.lcd.process_lcd(
                '{}ppm {}F {}%RH'.format(self.scd4x.co2, self.scd4x.tempF, self.scd4x.humidity),
                0, 0, 100
                )
            log.info(
                '{}ppm {}F {}%RH'.format(
                    self.scd4x.co2, self.scd4x.tempF, self.scd4x.humidity
                    )
                )

    def close(self):
        self.lcd.process_lcd('De-initializing ClimateControl...', 255, 0, 0)
        log.info('De-initializing ClimateControl... Please be patient')

        for var, controller in self.env_vars.items():
            log.info('Shutting down {} relay'.format(var))
            controller.close()
        
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