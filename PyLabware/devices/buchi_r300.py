"""PyLabware driver for Buchi R300 rotavap."""
import json
import urllib3
from typing import Dict, Union, Optional, Any

# Core imports
from ..controllers import (
    AbstractRotavap, AbstractPressureController, in_simulation_device_returns)
from ..exceptions import PLDeviceReplyError, PLDeviceCommandError
from ..models import ConnectionParameters, LabDeviceCommands, LabDeviceReply


class R300RotovapCommands(LabDeviceCommands):
    """Collection of command definitions for Buchi R300 rotavap.
    """
    DEFAULT_SYSTEM_LINE = "R-300"

    # !!! THESE VALUES ARE AUTO-GENERATED FROM API SPECIFICATIONS !!!
    # ######################### Process parameters #########################

    GET_SYSTEMCLASS = {'name': 'GET_SYSTEMCLASS', 'method': 'GET', 'endpoint': '/api/v1/info', 'path': ['systemClass'], 'reply': {'type': str}}
    GET_SYSTEMLINE = {'name': 'GET_SYSTEMLINE', 'method': 'GET', 'endpoint': '/api/v1/info', 'path': ['systemLine'], 'reply': {'type': str}}
    GET_SYSTEMNAME = {'name': 'GET_SYSTEMNAME', 'method': 'GET', 'endpoint': '/api/v1/info', 'path': ['systemName'], 'reply': {'type': str}}
    GET_HEATING_SET = {'name': 'GET_HEATING_SET', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['heating', 'set'], 'reply': {'type': float}}
    GET_HEATING_ACT = {'name': 'GET_HEATING_ACT', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['heating', 'act'], 'reply': {'type': float}}
    GET_HEATING_RUNNING = {'name': 'GET_HEATING_RUNNING', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['heating', 'running'], 'reply': {'type': bool}}
    GET_COOLING_SET = {'name': 'GET_COOLING_SET', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['cooling', 'set'], 'reply': {'type': float}}
    GET_COOLING_ACT = {'name': 'GET_COOLING_ACT', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['cooling', 'act'], 'reply': {'type': float}}
    GET_COOLING_RUNNING = {'name': 'GET_COOLING_RUNNING', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['cooling', 'running'], 'reply': {'type': bool}}
    GET_VACUUM_SET = {'name': 'GET_VACUUM_SET', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['vacuum', 'set'], 'reply': {'type': float}}
    GET_VACUUM_ACT = {'name': 'GET_VACUUM_ACT', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['vacuum', 'act'], 'reply': {'type': float}}
    GET_VACUUM_AERATEVALVEOPEN = {'name': 'GET_VACUUM_AERATEVALVEOPEN', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['vacuum', 'aerateValveOpen'], 'reply': {'type': bool}}
    GET_VACUUM_AERATEVALVEPULSE = {'name': 'GET_VACUUM_AERATEVALVEPULSE', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['vacuum', 'aerateValvePulse'], 'reply': {'type': bool}}
    GET_VACUUM_VACUUMVALVEOPEN = {'name': 'GET_VACUUM_VACUUMVALVEOPEN', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['vacuum', 'vacuumValveOpen'], 'reply': {'type': bool}}
    GET_VACUUM_VAPORTEMP = {'name': 'GET_VACUUM_VAPORTEMP', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['vacuum', 'vaporTemp'], 'reply': {'type': float}}
    GET_VACUUM_AUTODESTIN = {'name': 'GET_VACUUM_AUTODESTIN', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['vacuum', 'autoDestIn'], 'reply': {'type': float}}
    GET_VACUUM_AUTODESTOUT = {'name': 'GET_VACUUM_AUTODESTOUT', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['vacuum', 'autoDestOut'], 'reply': {'type': float}}
    GET_VACUUM_POWERPERCENTACT = {'name': 'GET_VACUUM_POWERPERCENTACT', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['vacuum', 'powerPercentAct'], 'reply': {'type': int}}
    GET_ROTATION_SET = {'name': 'GET_ROTATION_SET', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['rotation', 'set'], 'reply': {'type': float}}
    GET_ROTATION_ACT = {'name': 'GET_ROTATION_ACT', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['rotation', 'act'], 'reply': {'type': float}}
    GET_ROTATION_RUNNING = {'name': 'GET_ROTATION_RUNNING', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['rotation', 'running'], 'reply': {'type': bool}}
    GET_LIFT_SET = {'name': 'GET_LIFT_SET', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['lift', 'set'], 'reply': {'type': float}}
    GET_LIFT_ACT = {'name': 'GET_LIFT_ACT', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['lift', 'act'], 'reply': {'type': float}}
    GET_LIFT_LIMIT = {'name': 'GET_LIFT_LIMIT', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['lift', 'limit'], 'reply': {'type': float}}
    GET_GLOBALSTATUS_TIMESTAMP = {'name': 'GET_GLOBALSTATUS_TIMESTAMP', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['globalStatus', 'timeStamp'], 'reply': {'type': str}}
    GET_GLOBALSTATUS_PROCESSTIME = {'name': 'GET_GLOBALSTATUS_PROCESSTIME', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['globalStatus', 'processTime'], 'reply': {'type': int}}
    GET_GLOBALSTATUS_RUNID = {'name': 'GET_GLOBALSTATUS_RUNID', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['globalStatus', 'runId'], 'reply': {'type': int}}
    GET_GLOBALSTATUS_ONHOLD = {'name': 'GET_GLOBALSTATUS_ONHOLD', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['globalStatus', 'onHold'], 'reply': {'type': bool}}
    GET_GLOBALSTATUS_FOAMACTIVE = {'name': 'GET_GLOBALSTATUS_FOAMACTIVE', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['globalStatus', 'foamActive'], 'reply': {'type': bool}}
    GET_GLOBALSTATUS_CURRENTERROR = {'name': 'GET_GLOBALSTATUS_CURRENTERROR', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['globalStatus', 'currentError'], 'reply': {'type': int}}
    GET_GLOBALSTATUS_RUNNING = {'name': 'GET_GLOBALSTATUS_RUNNING', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['globalStatus', 'running'], 'reply': {'type': bool}}
    GET_MODE = {'name': 'GET_MODE', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['program', 'type'], 'reply': {'type': str}}
    GET_TIMER_SET_TIME = {'name': 'GET_TIMER_SET_TIME', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['program', 'set'], 'reply': {'type': int}}
    GET_SOLVENT_NAME = {'name': 'GET_SOLVENT_NAME', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['program', 'solventName'], 'reply': {'type': str}}
    GET_METHOD_NAME = {'name': 'GET_METHOD_NAME', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['program', 'methodName'], 'reply': {'type': str}}
    GET_TIMER_REMAINING_TIME = {'name': 'GET_TIMER_REMAINING_TIME', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['program', 'remaining'], 'reply': {'type': int}}
    GET_CLOUDDEST_MODE = {'name': 'GET_CLOUDDEST_MODE', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['program', 'mode'], 'reply': {'type': str}}
    GET_CLOUDDEST_FLASK_SIZE = {'name': 'GET_CLOUDDEST_FLASK_SIZE', 'method': 'GET', 'endpoint': '/api/v1/process', 'path': ['program', 'flaskSize'], 'reply': {'type': int}}
    SET_HEATING_SET = {'name': 'SET_HEATING_SET', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': float, 'check': {'min': 0, 'max': 220}, 'path': ['heating', 'set']}
    SET_HEATING_RUNNING = {'name': 'SET_HEATING_RUNNING', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': bool, 'check': None, 'path': ['heating', 'running']}
    SET_COOLING_SET = {'name': 'SET_COOLING_SET', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': float, 'check': {'min': -10, 'max': 25}, 'path': ['cooling', 'set']}
    SET_COOLING_RUNNING = {'name': 'SET_COOLING_RUNNING', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': bool, 'check': None, 'path': ['cooling', 'running']}
    SET_VACUUM_SET = {'name': 'SET_VACUUM_SET', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': float, 'check': {'min': 0, 'max': 1300}, 'path': ['vacuum', 'set']}
    SET_VACUUM_AERATEVALVEOPEN = {'name': 'SET_VACUUM_AERATEVALVEOPEN', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': bool, 'check': None, 'path': ['vacuum', 'aerateValveOpen']}
    SET_VACUUM_AERATEVALVEPULSE = {'name': 'SET_VACUUM_AERATEVALVEPULSE', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': bool, 'check': None, 'path': ['vacuum', 'aerateValvePulse']}
    SET_ROTATION_SET = {'name': 'SET_ROTATION_SET', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': float, 'check': {'min': 0, 'max': 280}, 'path': ['rotation', 'set']}
    SET_ROTATION_RUNNING = {'name': 'SET_ROTATION_RUNNING', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': bool, 'check': None, 'path': ['rotation', 'running']}
    SET_LIFT_SET = {'name': 'SET_LIFT_SET', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': float, 'check': {'min': 0, 'max': 220}, 'path': ['lift', 'set']}
    SET_GLOBALSTATUS_ONHOLD = {'name': 'SET_GLOBALSTATUS_ONHOLD', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': bool, 'check': None, 'path': ['globalStatus', 'onHold']}
    SET_GLOBALSTATUS_RUNNING = {'name': 'SET_GLOBALSTATUS_RUNNING', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': bool, 'check': None, 'path': ['globalStatus', 'running']}
    SET_MODE = {'name': 'SET_MODE', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': str, 'check': {'values': ['Manual', 'Timer', 'AutoDest', 'CloudDest', 'Dry', 'Solvent', 'Method', 'Calibration', 'TightnessTest']}, 'path': ['program', 'type']}
    SET_TIMER_TIME = {'name': 'SET_MODE', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': int, 'check': {'min': 0, 'max': 65520}, 'path': ['program', 'set']}
    SET_SOLVENT_NAME = {'name': 'SET_SOLVENT_NAME', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': str, 'path': ['program', 'solventName']}
    SET_METHOD_NAME = {'name': 'SET_METHOD_NAME', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': str, 'path': ['program', 'methodName']}
    SET_CLOUDDEST_MODE = {'name': 'SET_CLOUDDEST_MODE', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': str, 'check': {'values': ['fullControl', 'endDetection']}, 'path': ['program', 'mode']}
    SET_CLOUDDEST_FLASK_SIZE = {'name': 'SET_CLOUDDEST_FLASK_SIZE', 'method': 'PUT', 'endpoint': '/api/v1/process', 'type': int, 'check': {'values': [1, 2, 3]}, 'path': ['program', 'flaskSize']}

    # !!! THESE VALUES ARE AUTO-GENERATED FROM API SPECIFICATIONS !!!
    # ######################### System settings #########################

    GET_NETWORK_DHCP = {'name': 'GET_NETWORK_DHCP', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['network', 'dhcp'], 'reply': {'type': bool}}
    GET_NETWORK_IP = {'name': 'GET_NETWORK_IP', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['network', 'ip'], 'reply': {'type': str}}
    GET_NETWORK_SUBNET = {'name': 'GET_NETWORK_SUBNET', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['network', 'subnet'], 'reply': {'type': str}}
    GET_NETWORK_GATEWAY = {'name': 'GET_NETWORK_GATEWAY', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['network', 'gateway'], 'reply': {'type': str}}
    GET_NETWORK_DNS = {'name': 'GET_NETWORK_DNS', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['network', 'dns'], 'reply': {'type': str}}
    GET_NETWORK_CLOUDIP = {'name': 'GET_NETWORK_CLOUDIP', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['network', 'cloudIp'], 'reply': {'type': str}}
    GET_NETWORK_CLOUDENABLED = {'name': 'GET_NETWORK_CLOUDENABLED', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['network', 'cloudEnabled'], 'reply': {'type': bool}}
    GET_DISPLAY_LANGUAGE = {'name': 'GET_DISPLAY_LANGUAGE', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['display', 'language'], 'reply': {'type': str}}
    GET_DISPLAY_BRIGHTNESS = {'name': 'GET_DISPLAY_BRIGHTNESS', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['display', 'brightness'], 'reply': {'type': int}}
    GET_DISPLAY_UNITS_TEMPERATURE = {'name': 'GET_DISPLAY_UNITS_TEMPERATURE', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['display', 'units', 'temperature'], 'reply': {'type': str}}
    GET_DISPLAY_UNITS_PRESSURE = {'name': 'GET_DISPLAY_UNITS_PRESSURE', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['display', 'units', 'pressure'], 'reply': {'type': str}}
    GET_SOUNDS_BUTTONTONE = {'name': 'GET_SOUNDS_BUTTONTONE', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['sounds', 'buttonTone'], 'reply': {'type': bool}}
    GET_SOUNDS_PLAYSOUNDONFINISH = {'name': 'GET_SOUNDS_PLAYSOUNDONFINISH', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['sounds', 'playSoundOnFinish'], 'reply': {'type': bool}}
    GET_VACUUM_PRESSUREHYSTERESIS = {'name': 'GET_VACUUM_PRESSUREHYSTERESIS', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['vacuum', 'pressureHysteresis'], 'reply': {'type': float}}
    GET_VACUUM_ALTITUDE = {'name': 'GET_VACUUM_ALTITUDE', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['vacuum', 'altitude'], 'reply': {'type': float}}
    GET_VACUUM_MAXPERMPRESSURE = {'name': 'GET_VACUUM_MAXPERMPRESSURE', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['vacuum', 'maxPermPressure'], 'reply': {'type': float}}
    GET_VACUUM_MAXPUMPOUTPUT = {'name': 'GET_VACUUM_MAXPUMPOUTPUT', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['vacuum', 'maxPumpOutput'], 'reply': {'type': int}}
    GET_VACUUM_VENTONFINISH = {'name': 'GET_VACUUM_VENTONFINISH', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['vacuum', 'ventOnFinish'], 'reply': {'type': bool}}
    GET_ROTATION_STARTROTATIONONSTART = {'name': 'GET_ROTATION_STARTROTATIONONSTART', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['rotation', 'startRotationOnStart'], 'reply': {'type': bool}}
    GET_ROTATION_STOPROTATIONONFINISH = {'name': 'GET_ROTATION_STOPROTATIONONFINISH', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['rotation', 'stopRotationOnFinish'], 'reply': {'type': bool}}
    GET_HEATING_MAXTEMPERATURE = {'name': 'GET_HEATING_MAXTEMPERATURE', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['heating', 'maxTemperature'], 'reply': {'type': float}}
    GET_HEATING_STOPHEATINGONFINISH = {'name': 'GET_HEATING_STOPHEATINGONFINISH', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['heating', 'stopHeatingOnFinish'], 'reply': {'type': bool}}
    GET_COOLING_STOPCOOLINGONFINISH = {'name': 'GET_COOLING_STOPCOOLINGONFINISH', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['cooling', 'stopCoolingOnFinish'], 'reply': {'type': bool}}
    GET_LIFT_DEPTHSTOP = {'name': 'GET_LIFT_DEPTHSTOP', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['lift', 'depthStop'], 'reply': {'type': float}}
    GET_LIFT_IMMERSEONSTART = {'name': 'GET_LIFT_IMMERSEONSTART', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['lift', 'immerseOnStart'], 'reply': {'type': bool}}
    GET_LIFT_LIFTOUTFLASKONFINISH = {'name': 'GET_LIFT_LIFTOUTFLASKONFINISH', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['lift', 'liftOutFlaskOnFinish'], 'reply': {'type': bool}}
    GET_PROGRAM_ECO_ISENABLED = {'name': 'GET_PROGRAM_ECO_ISENABLED', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['program', 'eco', 'isEnabled'], 'reply': {'type': bool}}
    GET_PROGRAM_ECO_ACTIVATIONAFTERMINS = {'name': 'GET_PROGRAM_ECO_ACTIVATIONAFTERMINS', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['program', 'eco', 'activationAfterMins'], 'reply': {'type': int}}
    GET_PROGRAM_ECO_HEATINGBATHTEMPERATURE = {'name': 'GET_PROGRAM_ECO_HEATINGBATHTEMPERATURE', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['program', 'eco', 'heatingBathTemperature'], 'reply': {'type': float}}
    GET_PROGRAM_ECO_COOLANTTEMPERATURE = {'name': 'GET_PROGRAM_ECO_COOLANTTEMPERATURE', 'method': 'GET', 'endpoint': '/api/v1/settings', 'path': ['program', 'eco', 'coolantTemperature'], 'reply': {'type': float}}
    SET_DISPLAY_LANGUAGE = {'name': 'SET_DISPLAY_LANGUAGE', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': str, 'check': {'values': ['en', 'de', 'fr', 'it', 'es', 'ru', 'pt', 'ja', 'zh', 'ko', 'id']}, 'path': ['display', 'language']}
    SET_DISPLAY_BRIGHTNESS = {'name': 'SET_DISPLAY_BRIGHTNESS', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': int, 'check': {'min': 0, 'max': 100}, 'path': ['display', 'brightness']}
    SET_DISPLAY_UNITS_TEMPERATURE = {'name': 'SET_DISPLAY_UNITS_TEMPERATURE', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': str, 'check': {'values': ['Celsius', 'Fahrenheit', 'Kelvin']}, 'path': ['display', 'units', 'temperature']}
    SET_DISPLAY_UNITS_PRESSURE = {'name': 'SET_DISPLAY_UNITS_PRESSURE', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': str, 'check': {'values': ['hPa', 'mBar', 'torr', 'mmhg']}, 'path': ['display', 'units', 'pressure']}
    SET_SOUNDS_BUTTONTONE = {'name': 'SET_SOUNDS_BUTTONTONE', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': bool, 'check': None, 'path': ['sounds', 'buttonTone']}
    SET_SOUNDS_PLAYSOUNDONFINISH = {'name': 'SET_SOUNDS_PLAYSOUNDONFINISH', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': bool, 'check': None, 'path': ['sounds', 'playSoundOnFinish']}
    SET_VACUUM_PRESSUREHYSTERESIS = {'name': 'SET_VACUUM_PRESSUREHYSTERESIS', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': float, 'check': {'min': 0, 'max': 200}, 'path': ['vacuum', 'pressureHysteresis']}
    SET_VACUUM_ALTITUDE = {'name': 'SET_VACUUM_ALTITUDE', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': float, 'check': {'min': 0, 'max': 4000}, 'path': ['vacuum', 'altitude']}
    SET_VACUUM_MAXPERMPRESSURE = {'name': 'SET_VACUUM_MAXPERMPRESSURE', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': float, 'check': {'min': 0, 'max': 1300}, 'path': ['vacuum', 'maxPermPressure']}
    SET_VACUUM_MAXPUMPOUTPUT = {'name': 'SET_VACUUM_MAXPUMPOUTPUT', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': int, 'check': {'min': 0, 'max': 100}, 'path': ['vacuum', 'maxPumpOutput']}
    SET_VACUUM_VENTONFINISH = {'name': 'SET_VACUUM_VENTONFINISH', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': bool, 'check': None, 'path': ['vacuum', 'ventOnFinish']}
    SET_ROTATION_STARTROTATIONONSTART = {'name': 'SET_ROTATION_STARTROTATIONONSTART', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': bool, 'check': None, 'path': ['rotation', 'startRotationOnStart']}
    SET_ROTATION_STOPROTATIONONFINISH = {'name': 'SET_ROTATION_STOPROTATIONONFINISH', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': bool, 'check': None, 'path': ['rotation', 'stopRotationOnFinish']}
    SET_HEATING_STOPHEATINGONFINISH = {'name': 'SET_HEATING_STOPHEATINGONFINISH', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': bool, 'check': None, 'path': ['heating', 'stopHeatingOnFinish']}
    SET_COOLING_STOPCOOLINGONFINISH = {'name': 'SET_COOLING_STOPCOOLINGONFINISH', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': bool, 'check': None, 'path': ['cooling', 'stopCoolingOnFinish']}
    SET_LIFT_IMMERSEONSTART = {'name': 'SET_LIFT_IMMERSEONSTART', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': bool, 'check': None, 'path': ['lift', 'immerseOnStart']}
    SET_LIFT_LIFTOUTFLASKONFINISH = {'name': 'SET_LIFT_LIFTOUTFLASKONFINISH', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': bool, 'check': None, 'path': ['lift', 'liftOutFlaskOnFinish']}
    SET_PROGRAM_ECO_ISENABLED = {'name': 'SET_PROGRAM_ECO_ISENABLED', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': bool, 'check': None, 'path': ['program', 'eco', 'isEnabled']}
    SET_PROGRAM_ECO_ACTIVATIONAFTERMINS = {'name': 'SET_PROGRAM_ECO_ACTIVATIONAFTERMINS', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': int, 'check': {'min': 5, 'max': 100}, 'path': ['program', 'eco', 'activationAfterMins']}
    SET_PROGRAM_ECO_HEATINGBATHTEMPERATURE = {'name': 'SET_PROGRAM_ECO_HEATINGBATHTEMPERATURE', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': float, 'check': {'min': 3, 'max': 200}, 'path': ['program', 'eco', 'heatingBathTemperature']}
    SET_PROGRAM_ECO_COOLANTTEMPERATURE = {'name': 'SET_PROGRAM_ECO_COOLANTTEMPERATURE', 'method': 'PUT', 'endpoint': '/api/v1/settings', 'type': float, 'check': {'min': 3, 'max': 50}, 'path': ['program', 'eco', 'coolantTemperature']}
    GET_LEAKTESTS = {'name': 'GET_LEAKTESTS', 'method': 'GET', 'endpoint': '/api/v1/health', 'path': ['leakTests'], 'reply': {'type': list}}


class R300Rotovap(AbstractRotavap, AbstractPressureController):
    """
    This provides a Python class for the R300 rotavap
    based on the Buchi OpenAPI specification v. 0.10.0
    """

    def __init__(self,
                 device_name: str,
                 connection_mode: str,
                 address: Optional[str],
                 port: Union[str, int],
                 user: Optional[str],
                 password: Optional[str]) -> None:

        # Load commands from helper class
        self.cmd = R300RotovapCommands

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        connection_parameters["user"] = user
        connection_parameters["schema"] = "https"
        connection_parameters["password"] = password
        connection_parameters["address"] = address
        connection_parameters["port"] = port
        connection_parameters["verify_ssl"] = False
        connection_parameters["headers"] = {"Content-Type": "application/json"}

        super().__init__(
            device_name, connection_mode, connection_parameters)

        # Protocol settings
        self.reply_prefix = None
        self.reply_terminator = None

        # Disable requests warnings about Buchi self-signed certificate
        urllib3.disable_warnings()

    def prepare_message(self, cmd: Dict, value: Any) -> Any:
        """ Checks parameter value if necessary and prepares JSON payload
        """

        message = {}
        message["endpoint"] = cmd["endpoint"]
        message["method"] = cmd["method"]

        # Prepare payload
        payload = None
        # Check that value is empty for GET requests
        if cmd["method"] == "GET":
            if value is not None:
                self.logger.warning("Trying to send GET request with non-empty payload <%s>", value)
        else:
            path_to_payload = cmd["path"].copy()
            parameter = path_to_payload.pop()
            payload = {parameter: value}
            # The easiest way to build the rest of the nested dict we need
            # is to start bottom up
            path_to_payload.reverse()
            # Wrap the rest of stuff around
            for item in path_to_payload:
                payload = {item: payload}
            payload = json.dumps(payload)
        message["data"] = payload
        self.logger.debug("prepare_message()::constructed payload <%s>", payload)
        return message

    def parse_reply(self, cmd: Dict, reply: LabDeviceReply) -> Any:
        """ Parses JSON payload and returns device reply.
        """

        # Extract and load reply body
        if reply.content_type != "json":
            raise PLDeviceReplyError(f"Invalid content-type {reply.content_type} in device reply!")
        try:
            reply = json.loads(reply.body)
        except (json.JSONDecodeError, TypeError) as e:
            raise PLDeviceReplyError("Can't transform device reply to JSON!") from e
        self.logger.debug("parse_reply():: JSON decoded reply: <%s>", reply)
        # Extract required element from JSON tree
        for item in cmd["path"]:
            reply = reply[item]
        # Run text parsing / type casting, if any
        return super().parse_reply(cmd, reply)

#   ### General methods ###

    def initialize_device(self) -> None:
        """ Initialization sequence
        """
        # TODO Add any initialization if necessary - e.g. setting default method

    def is_connected(self) -> bool:
        """ Checks whether the right device is connected.
        """

        return self.send(self.cmd.GET_SYSTEMLINE) == self.cmd.DEFAULT_SYSTEM_LINE

    def is_idle(self) -> bool:
        """ Checks whether the device is idle
        """

        return self.send(self.cmd.GET_GLOBALSTATUS_RUNNING) is False

    def check_errors(self) -> None:
        """ Returns last error code
        """
        # TODO check the manual for error codes & interpert them.
        return self.send(self.cmd.GET_GLOBALSTATUS_CURRENTERROR)

    def clear_errors(self) -> None:
        """ Not supported on this model
        """

    def get_status(self) -> str:
        """ Gets device status.
        """

    def get_systemclass(self) -> str:
        """Gets system type
        """

        return self.send(self.cmd.GET_SYSTEMCLASS)

    def get_systemname(self) -> str:
        """Gets system name (as set from the I-300)
        """

        return self.send(self.cmd.GET_SYSTEMNAME)

    def get_mode(self) -> str:
        """Gets the current operation mode of the R300.
        """

        return self.send(self.cmd.GET_MODE)

    def set_mode(self, mode: str) -> None:
        """Sets the operation mode of the R300. Valid modes are
        'Manual', 'AuotDest', 'Timer', 'Dry', 'CloudDest', 'Method',
        'Solvent', 'TightnessTest', 'Calibration'.
        """
        # Not all programs are fully supported by the current
        # OpenInterface API version. The known restricitons are:
        # - The 'Calibration' and 'TightnessTest' programms cannot
        #   be started through the API.
        # - The 'Dry' program does not expose all it's parameters
        #   (see github.com/buchi-labortechnik-ag/openinterface_rotavapor/issues/1)
        return self.send(self.cmd.SET_MODE, mode)

    def set_timer_time(self, time: int) -> None:
        """Sets the time variable for the Timer program.
        """
        current_mode = self.get_mode()
        # Defining the time for the Timer program only has an effect
        # when first the Timer program is selected.
        if current_mode != 'Timer':
            self.set_mode('Timer')
            self.logger.info(f"Switching program from '{current_mode}' to "
                             "'Timer'.")

        return self.send(self.cmd.SET_TIMER_TIME, time)

    def get_timer_set_time(self) -> Optional[int]:
        """Gets the time variable for the Timer program.
        """
        current_mode = self.get_mode()
        # Check that 'Timer' program is enabled.
        # Retreiving the set-point time without
        # this programm being selected first would trigger
        # a key error when unpacking the device reply.
        if current_mode != 'Timer':
            self.logger.warning("Can't retreive set time of the 'Timer' program "
                                "since this program is not currently selected "
                                f"(selected program is '{current_mode}'). Select "
                                "'Timer' program first.")
            return None
        else:
            return self.send(self.cmd.GET_TIMER_SET_TIME)

    def get_timer_remaining_time(self) -> Optional[int]:
        """Gets the remaining time of the timer method.
        """
        current_mode = self.get_mode()
        # Check that 'Timer' program is enabled.
        # Retreiving the remaining time without
        # this programm being selected first would trigger
        # a key error when unpacking the device reply.
        if current_mode != 'Timer':
            self.logger.warning("Can't retreive remaining time of the 'Timer' "
                                "program since this program is not currently "
                                f"selected (selected program is '{current_mode}'). "
                                "Select 'Timer' program first.")
            return None
        else:
            return self.send(self.cmd.GET_TIMER_REMAINING_TIME)

    def set_solvent_name(self, solvent: str) -> None:
        """Sets the solvent name for the 'Solvent' program.

        Args:
            solvent (str): Solvent name. If the solvent is in the solvent
                library of the R300 the appropriate evaporation parameters
                will be automatically choosen by the device.

        Exceptions:
            raises PLDeviceCommandError if an unknonw solvent is selected.
        """
        current_mode = self.get_mode()
        # Defining the time for the Solvent program only has an effect
        # when first the Timer program is selected.
        if current_mode != 'Solvent':
            self.set_mode('Solvent')
            self.logger.info(f"Switching program from '{current_mode}' to "
                             "'Solvent'.")

        self.send(self.cmd.SET_SOLVENT_NAME, solvent)

        # Check whether the rotavap found an entry in it's
        # internal libraries for the desired solvent.
        if self.get_solvent_name() != solvent:
            raise PLDeviceCommandError(f"The solvent name '{solvent}' was not recognised. "
                                       "Check the solvent library of the R300 and if the "
                                       "desired solvent is not included (e.g. with different "
                                       "spelling) add it manually to the custom solvent "
                                       "library (on the I-300Pro interface under 'Libraies' "
                                       "-> 'Own solvent library')")

    def get_solvent_name(self) -> Optional[str]:
        """Gets the name of the selected solvent for the 'Solvent' program.
        """
        current_mode = self.get_mode()
        # Check that 'Solvent' program is enabled.
        # Retreiving the remaining time without
        # this programm being selected first would trigger
        # a key error when unpacking the device reply.
        if current_mode != 'Solvent':
            self.logger.warning("Can't retreive selected solvent of the 'Solvent' "
                                "program since this program is not currently "
                                f"selected (selected program is '{current_mode}'). "
                                "Select 'Solvent' program first.")
            return None
        else:
            return self.send(self.cmd.GET_SOLVENT_NAME)

    def set_method_name(self, method: str) -> None:
        """Sets the method name for the 'Method' program.

        Args:
            method (str): Method name. The R300 will load the
                predefined method.

        Exceptions:
            raises PLDeviceCommandError if an unknonw method is selected.
        """
        current_mode = self.get_mode()
        # Defining the time for the Solvent program only has an effect
        # when first the Timer program is selected.
        if current_mode != 'Method':
            self.set_mode('Method')
            self.logger.info(f"Switching program from '{current_mode}' to "
                             "'Method'.")

        self.send(self.cmd.SET_METHOD_NAME, method)

        # Check whether the rotavap found an entry in it's
        # internal libraries for the desired solvent.
        if self.get_method_name() != method:
            raise PLDeviceCommandError(f"The method name '{method}' was not recognised. "
                                       "Check that the method exists (e.g. with different "
                                       "spelling) and if not define the required method on "
                                       "the device (on the I-300Pro interface under 'Operating "
                                       "modes' -> 'Methods')")

    def get_method_name(self) -> Optional[str]:
        """Gets the name of the selected method for the 'Method' program.
        """
        current_mode = self.get_mode()
        # Check that 'Solvent' program is enabled.
        # Retreiving the remaining time without
        # this programm being selected first would trigger
        # a key error when unpacking the device reply.
        if current_mode != 'Method':
            self.logger.warning("Can't retreive selected method of the 'Method' "
                                "program since this program is not currently "
                                f"selected (selected program is '{current_mode}'). "
                                "Select 'Method' program first.")
            return None
        else:
            return self.send(self.cmd.GET_METHOD_NAME)

    def set_clouddest_mode(self, mode: str) -> None:
        """Sets the mode name for the 'CloudDest' program.

        Args:
            method (str): Mode name. Valide mode names are
                'fullControl' and 'endDetection'.
        """
        current_mode = self.get_mode()
        # Defining the time for the Solvent program only has an effect
        # when first the Timer program is selected.
        if current_mode != 'CloudDest':
            self.set_mode('CloudDest')
            self.logger.info(f"Switching program from '{current_mode}' to "
                             "'CloudDest'.")

        self.send(self.cmd.SET_CLOUDDEST_MODE, mode)

    def get_clouddest_mode(self) -> Optional[str]:
        """Gets the current mode of the 'CloudDest' program.
        """
        current_mode = self.get_mode()
        # Check that 'CloudDest' program is enabled.
        # Retreiving the remaining time without
        # this programm being selected first would trigger
        # a key error when unpacking the device reply.
        if current_mode != 'CloudDest':
            self.logger.warning("Can't retreive selected method of the 'CloudDest' "
                                "program since this program is not currently "
                                f"selected (selected program is '{current_mode}'). "
                                "Select 'CloudDest' program first.")
            return None
        else:
            return self.send(self.cmd.GET_CLOUDDEST_MODE)

    def set_clouddest_flask_size(self, flask_size: int) -> None:
        """Sets the flask size parameter of the 'CloudDest' program.

        Args:
            flask_size (int): Flask size.
        """
        # TODO: Confirm allowed range of flask sizes against Buchi specs.
        current_mode = self.get_mode()
        # Defining the time for the Solvent program only has an effect
        # when first the Timer program is selected.
        if current_mode != 'CloudDest':
            self.set_mode('CloudDest')
            self.logger.info(f"Switching program from '{current_mode}' to "
                             "'CloudDest'.")

        self.send(self.cmd.SET_CLOUDDEST_FLASK_SIZE, flask_size)

    def get_clouddest_flask_size(self) -> Optional[int]:
        """Gets the current flask size parameter of the 'CloudDest' program.
        """
        current_mode = self.get_mode()
        # Check that 'CloudDest' program is enabled.
        # Retreiving the remaining time without
        # this programm being selected first would trigger
        # a key error when unpacking the device reply.
        if current_mode != 'CloudDest':
            self.logger.warning("Can't retreive selected method of the 'CloudDest' "
                                "program since this program is not currently "
                                f"selected (selected program is '{current_mode}'). "
                                "Select 'CloudDest' program first.")
            return None
        else:
            return self.send(self.cmd.GET_CLOUDDEST_FLASK_SIZE)

    def start(self) -> None:
        """Starts current method
        """

        self.send(self.cmd.SET_GLOBALSTATUS_RUNNING, True)

    def stop(self) -> None:
        """Stops current method
        """

        # Chemputer specifics - see #23 on Gitlab
        # Need to lift up before stopping
        self.lift_up()
        self.send(self.cmd.SET_GLOBALSTATUS_RUNNING, False)
        # FIXME Possible bug - chiller doesn't switch off either remotely or
        # by pressing STOP on I-300
        self.stop_chiller()

#   ### Bath control methods ###

    def start_bath(self) -> None:
        """Starts heating the bath.
        """

        self.send(self.cmd.SET_HEATING_RUNNING, True)

    def stop_bath(self):
        """Stops heating the bath.
        """

        self.send(self.cmd.SET_HEATING_RUNNING, False)

    def is_heating_running(self) -> bool:
        """ Checks whether bath heating is running.
        """

        return self.send(self.cmd.GET_HEATING_RUNNING)

    def set_temperature(self, temperature: float, sensor: int = 0):
        """Sets the desired bath temperature.

        Args:
            temperature (float): Temperature setpoint in °C.
            sensor (int): Specify which temperature probe the setpoint applies to.
                          This device has only an internal sensor.
                          Thus, the sensor variable has no effect here.
        """

        self.send(self.cmd.SET_HEATING_SET, temperature)

    def get_temperature(self, sensor: int = 0) -> float:
        """Gets current bath temperature.

        Args:
            sensor (int): Specify which temperature probe the setpoint applies to.
                          This device has only an internal sensor.
                          Thus, the sensor variable has no effect here.
        """

        return self.send(self.cmd.GET_HEATING_ACT)

    def get_temperature_setpoint(self, sensor: int = 0) -> float:
        """Reads the current temperature setpoint.

        Args:
            sensor (int): Specify which temperature probe the setpoint applies to.
                          This device has only an internal sensor.
                          Thus, the sensor variable has no effect here.
        """

        return self.send(self.cmd.GET_HEATING_SET)

#   ### Chiller control methods ###

    def start_chiller(self) -> None:
        """Starts recirculation chiller.
        """

        self.send(self.cmd.SET_COOLING_RUNNING, True)

    def stop_chiller(self):
        """Stops recirculation chiller.
        """

        self.send(self.cmd.SET_COOLING_RUNNING, False)

    def is_chiller_running(self) -> bool:
        """Checks if recirculation chiller is running.
        """

        return self.send(self.cmd.GET_COOLING_RUNNING)

    def set_chiller_temperature(self, temperature: float) -> None:
        """Sets desired chiller temperature
        """

        self.send(self.cmd.SET_COOLING_SET, temperature)

    def get_chiller_temperature(self) -> float:
        """Gets current chiller temperature.
        """

        return self.send(self.cmd.GET_COOLING_ACT)

    def get_chiller_temperature_setpoint(self) -> float:
        """Gets chiller temperature setpoint.
        """

        return self.send(self.cmd.GET_COOLING_SET)

#   ### Rotation control methods ###

    def start_rotation(self) -> None:
        """Starts rotation.
        """

        self.send(self.cmd.SET_ROTATION_RUNNING, True)

    def stop_rotation(self) -> None:
        """Stops rotation.
        """

        self.send(self.cmd.SET_ROTATION_RUNNING, False)

    def is_rotation_running(self) -> bool:
        """Checks whether flask rotation is running.
        """

        return self.send(self.cmd.GET_ROTATION_RUNNING)

    def set_speed(self, speed: float) -> None:
        """Sets rotation speed.
        """

        self.send(self.cmd.SET_ROTATION_SET, speed)

    def get_speed(self):
        """Gets actual rotation speed.
        """
        return self.send(self.cmd.GET_ROTATION_ACT)

    def get_speed_setpoint(self):
        """Gets rotation speed setpoint.
        """

        return self.send(self.cmd.GET_ROTATION_SET)

#   ### Lift control methods ###

    def set_lift_pos(self, position):
        """Sets lift position.
        """

        # BUG
        self.logger.warning("Setting arbitrary lift position doesn't work in the current version of API")
        # self.send(self.cmd.SET_LIFT_SET, position)

    def get_lift_position(self) -> float:
        """Returns current lift position
        """

        return self.send(self.cmd.GET_LIFT_ACT)

    def lift_up(self):
        """Moves evaporation flask up.
        """

        # Can't reuse set_lift_pos due to bug above
        self.send(self.cmd.SET_LIFT_SET, self.cmd.SET_LIFT_SET["check"]["min"])

    def lift_down(self):
        """Moves evaporation flask down.
        """

        # Can't reuse set_lift_pos due to bug above
        bottom_limit = self.get_lift_limit()
        self.send(self.cmd.SET_LIFT_SET, bottom_limit)

    def get_lift_limit(self) -> float:
        """Gets lift bottom position limit.
        """

        return self.send(self.cmd.GET_LIFT_LIMIT)

    def get_lift_set(self) -> float:
        """Returns lift position setpoint
        """

        return self.send(self.cmd.GET_LIFT_SET)

#   ### Pump control methods ###

    def start_pressure_regulation(self):
        self.logger.warning(
            'Pressure regulation can only be started along with everything else. Use `device.start()`.')

    def stop_pressure_regulation(self):
        self.logger.warning(
            'Pressure regulation can only be stopped along with everything else. Use `device.stop()`.')

    def set_pressure(self, pressure: float):
        """Sets desired pressure.
        """

        self.send(self.cmd.SET_VACUUM_SET, pressure)

    @in_simulation_device_returns(1013.25)
    def get_pressure(self) -> float:
        """ Gets current pressure.
        """

        return self.send(self.cmd.GET_VACUUM_ACT)

    def get_pressure_setpoint(self) -> float:
        """Gets desired pressure setpoint.
        """

        return self.send(self.cmd.GET_VACUUM_SET)

    def vent_on(self) -> None:
        """Vents the system.
        """

        self.send(self.cmd.SET_VACUUM_AERATEVALVEOPEN, True)

    def vent_off(self) -> None:
        """Stops venting the system.
        """

        self.send(self.cmd.SET_VACUUM_AERATEVALVEOPEN, False)

    def vent_pulse(self) -> None:
        """Pulses vent valve open for a short time.
        """

        self.send(self.cmd.SET_VACUUM_AERATEVALVEPULSE, True)

#   ### Distillation sensors methods ###

    def get_vapor_temperature(self) -> float:
        """Gets vapour temperature.
        """

        return self.send(self.cmd.GET_VACUUM_VAPORTEMP)

    def get_water_in_temperature(self) -> float:
        """Gets temperature of the water entering condenser.
        """

        return self.send(self.cmd.GET_VACUUM_AUTODESTIN)

    def get_water_out_temperature(self) -> float:
        """Gets temperature of the water leaving condenser.
        """

        return self.send(self.cmd.GET_VACUUM_AUTODESTOUT)

    def get_vacuum_aeratevalveopen(self) -> bool:
        """Gets status of aeration valve (optional).
        """

        return self.send(self.cmd.GET_VACUUM_AERATEVALVEOPEN)

    def get_vacuum_vacuumvalveopen(self) -> bool:
        """Gets status of vacuum valve (optional, for non-Buchi pumps).
        """

        return self.send(self.cmd.GET_VACUUM_VACUUMVALVEOPEN)

    def get_vacuum_powerpercentact(self) -> int:
        """Gets current vacuum pump power percentage.
        """

        return self.send(self.cmd.GET_VACUUM_POWERPERCENTACT)

#   ### Configuration methods ###

    def get_globalstatus_onhold(self) -> bool:
        """Gets hold mode status.
        """

        return self.send(self.cmd.GET_GLOBALSTATUS_ONHOLD)

    def get_globalstatus_foamactive(self) -> bool:
        """Gets foam sensor status.
        """

        return self.send(self.cmd.GET_GLOBALSTATUS_FOAMACTIVE)

    def set_globalstatus_onhold(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_GLOBALSTATUS_ONHOLD, value)

    def get_network_dhcp(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_NETWORK_DHCP)

    def get_network_ip(self) -> str:
        """
        """

        return self.send(self.cmd.GET_NETWORK_IP)

    def get_network_subnet(self) -> str:
        """
        """

        return self.send(self.cmd.GET_NETWORK_SUBNET)

    def get_network_gateway(self) -> str:
        """
        """

        return self.send(self.cmd.GET_NETWORK_GATEWAY)

    def get_network_dns(self) -> str:
        """
        """

        return self.send(self.cmd.GET_NETWORK_DNS)

    def get_network_cloudip(self) -> str:
        """
        """

        return self.send(self.cmd.GET_NETWORK_CLOUDIP)

    def get_network_cloudenabled(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_NETWORK_CLOUDENABLED)

    def get_display_language(self) -> str:
        """
        """

        return self.send(self.cmd.GET_DISPLAY_LANGUAGE)

    def get_display_brightness(self) -> int:
        """
        """

        return self.send(self.cmd.GET_DISPLAY_BRIGHTNESS)

    def get_display_units_temperature(self) -> str:
        """
        """

        return self.send(self.cmd.GET_DISPLAY_UNITS_TEMPERATURE)

    def get_display_units_pressure(self) -> str:
        """
        """

        return self.send(self.cmd.GET_DISPLAY_UNITS_PRESSURE)

    def get_sounds_buttontone(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_SOUNDS_BUTTONTONE)

    def get_sounds_playsoundonfinish(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_SOUNDS_PLAYSOUNDONFINISH)

    def get_vacuum_pressurehysteresis(self) -> float:
        """
        """

        return self.send(self.cmd.GET_VACUUM_PRESSUREHYSTERESIS)

    def get_vacuum_altitude(self) -> float:
        """
        """

        return self.send(self.cmd.GET_VACUUM_ALTITUDE)

    def get_vacuum_maxpermpressure(self) -> float:
        """
        """

        return self.send(self.cmd.GET_VACUUM_MAXPERMPRESSURE)

    def get_vacuum_maxpumpoutput(self) -> int:
        """
        """

        return self.send(self.cmd.GET_VACUUM_MAXPUMPOUTPUT)

    def get_vacuum_ventonfinish(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_VACUUM_VENTONFINISH)

    def get_rotation_startrotationonstart(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_ROTATION_STARTROTATIONONSTART)

    def get_rotation_stoprotationonfinish(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_ROTATION_STOPROTATIONONFINISH)

    def get_heating_maxtemperature(self) -> float:
        """
        """

        return self.send(self.cmd.GET_HEATING_MAXTEMPERATURE)

    def get_heating_stopheatingonfinish(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_HEATING_STOPHEATINGONFINISH)

    def get_cooling_stopcoolingonfinish(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_COOLING_STOPCOOLINGONFINISH)

    def get_lift_depthstop(self) -> float:
        """
        """

        return self.send(self.cmd.GET_LIFT_DEPTHSTOP)

    def get_lift_immerseonstart(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_LIFT_IMMERSEONSTART)

    def get_lift_liftoutflaskonfinish(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_LIFT_LIFTOUTFLASKONFINISH)

    def get_program_eco_isenabled(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_PROGRAM_ECO_ISENABLED)

    def get_program_eco_activationaftermins(self) -> int:
        """
        """

        return self.send(self.cmd.GET_PROGRAM_ECO_ACTIVATIONAFTERMINS)

    def get_program_eco_heatingbathtemperature(self) -> float:
        """
        """

        return self.send(self.cmd.GET_PROGRAM_ECO_HEATINGBATHTEMPERATURE)

    def get_program_eco_coolanttemperature(self) -> float:
        """
        """

        return self.send(self.cmd.GET_PROGRAM_ECO_COOLANTTEMPERATURE)

    def set_display_language(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_DISPLAY_LANGUAGE, value)

    def set_display_brightness(self, value: int) -> None:
        """
        """

        self.send(self.cmd.SET_DISPLAY_BRIGHTNESS, value)

    def set_display_units_temperature(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_DISPLAY_UNITS_TEMPERATURE, value)

    def set_display_units_pressure(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_DISPLAY_UNITS_PRESSURE, value)

    def set_sounds_buttontone(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_SOUNDS_BUTTONTONE, value)

    def set_sounds_playsoundonfinish(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_SOUNDS_PLAYSOUNDONFINISH, value)

    def set_vacuum_pressurehysteresis(self, value: float) -> None:
        """
        """

        self.send(self.cmd.SET_VACUUM_PRESSUREHYSTERESIS, value)

    def set_vacuum_altitude(self, value: float) -> None:
        """
        """

        self.send(self.cmd.SET_VACUUM_ALTITUDE, value)

    def set_vacuum_maxpermpressure(self, value: float) -> None:
        """
        """

        self.send(self.cmd.SET_VACUUM_MAXPERMPRESSURE, value)

    def set_vacuum_maxpumpoutput(self, value: int) -> None:
        """
        """

        self.send(self.cmd.SET_VACUUM_MAXPUMPOUTPUT, value)

    def set_vacuum_ventonfinish(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_VACUUM_VENTONFINISH, value)

    def set_rotation_startrotationonstart(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_ROTATION_STARTROTATIONONSTART, value)

    def set_rotation_stoprotationonfinish(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_ROTATION_STOPROTATIONONFINISH, value)

    def set_heating_stopheatingonfinish(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_HEATING_STOPHEATINGONFINISH, value)

    def set_cooling_stopcoolingonfinish(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_COOLING_STOPCOOLINGONFINISH, value)

    def set_lift_immerseonstart(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_LIFT_IMMERSEONSTART, value)

    def set_lift_liftoutflaskonfinish(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_LIFT_LIFTOUTFLASKONFINISH, value)

    def set_program_eco_isenabled(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_PROGRAM_ECO_ISENABLED, value)

    def set_program_eco_activationaftermins(self, value: int) -> None:
        """
        """

        self.send(self.cmd.SET_PROGRAM_ECO_ACTIVATIONAFTERMINS, value)

    def set_program_eco_heatingbathtemperature(self, value: float) -> None:
        """
        """

        self.send(self.cmd.SET_PROGRAM_ECO_HEATINGBATHTEMPERATURE, value)

    def set_program_eco_coolanttemperature(self, value: float) -> None:
        """
        """

        self.send(self.cmd.SET_PROGRAM_ECO_COOLANTTEMPERATURE, value)

    def get_leaktests(self) -> list:
        """
        """

        return self.send(self.cmd.GET_LEAKTESTS)
