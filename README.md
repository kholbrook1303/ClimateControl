# ClimateControl
Climate Control for Raspberry Pi with Grove board using a Sensirion scd41 to measure temperature, humidity, and co2 concentration.  Additionally there is a Grove 4-chaneel relay connected to outlets for which you can control the environmental variables.

## Hardware Requirements
- Rasberry Pi 3b+
- [GrovePi Plus Board](https://wiki.seeedstudio.com/GrovePi_Plus/)
- [Grove - CO2 & Temperature & Humidity Sensor (SCD41)](https://wiki.seeedstudio.com/Grove-CO2_&_Temperature_&_Humidity_Sensor-SCD41/)
- [Grove - 4-Channel SPDT Relay](https://wiki.seeedstudio.com/Grove-4-Channel_SPDT_Relay/)
- [Grove - LCD RGB Backlight](https://wiki.seeedstudio.com/Grove-LCD_RGB_Backlight/) (Optional)
- 2 15 Amp Residential Grade Duplex Outlets
- 2-Gang Electrical Switch and Outlet Box
- Appliance Replacement Cord

## Software Requirements
- Raspbian for Robots - This comes with all GrovePi software fully installed.
- Sensirion python drivers (see below)

## Install requirements for Sensirion scd41
```
pip3 install sensirion_i2c_sht4x
pip3 install -r requirements.txt
```