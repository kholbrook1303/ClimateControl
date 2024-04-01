

def is_str_bool(value):
    """Check if string is an integer.
    @param value: object to be verified.
    """
    if value.lower() == 'true':
        return True
    elif value.lower() == 'false':
        return True

    return False

def is_str_int(value):
    """Check if string is an integer.
    @param value: object to be verified.
    """
    try:
        int(value)
        return True
    except:
        return False

def celsiusToFarenheit(tempC):
    "This converts celcius to fahrenheit"
    tempF = round((tempC * 1.8) + 32, 2);
    return tempF;

def farenheitToCelsius(tempF):
    "This converts fahrenheit to celcius"
    tempC = round((tempF - 32) / 1.8, 2)
    return tempC;