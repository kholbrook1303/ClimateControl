import configparser
import os

from lib.common import is_str_bool, is_str_int

APP_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),'..'
        )
    )

class Config:
    def __init__(self, testing=False):
        self.testing = testing
        
        config_path = os.path.join(
            APP_ROOT, 'conf', 'ClimateControl.conf'
            )
        self._process_config(config_path)
        
        profile = getattr(self, 'general')['profile']
        if not profile:
            raise Exception("Environment profile is invalid!")
        
        env_config_path = os.path.join(
            APP_ROOT, 'conf', 'profiles', profile + '.conf'
            )
        self._process_config(env_config_path)
        
    def _process_config(self, config_path):
        try:
            config = configparser.ConfigParser(allow_no_value=True, interpolation=None)
            config.read(config_path)  
            self._process_config_sections(config)

        except Exception as e:
            raise Exception("Error loading configuration file: {0}".format(e))
        
    def _process_config_sections(self, config):
        for section in config.sections():
            setattr(self, section, dict())

            for name, str_value in config.items(section):
                if str_value.startswith('0x'):
                    value = int(str_value, 16)
                elif name == 'outlets':
                    value = config.get(section, name).split(',')
                elif name == 'env_variables':
                    value = config.get(section, name).split(',')
                elif is_str_bool(str_value):
                    value = config.getboolean(section, name)
                elif is_str_int(str_value):
                    value = config.getint(section, name)
                else:
                    value = config.get(section, name)

                getattr(self, section)[name] = value