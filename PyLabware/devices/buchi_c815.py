"""PyLabware driver for Buchi C815 flash system."""


import json
import warnings
from typing import Dict, Optional, Union, Any

# Core imports
from ..controllers import AbstractFlashChromatographySystem, in_simulation_device_returns
from ..exceptions import PLConnectionError, PLDeviceReplyError
from ..models import ConnectionParameters, LabDeviceCommands, LabDeviceReply


class C815Commands(LabDeviceCommands):
    """Collection of command definitions for C815 flash chromatography system.
    """

    # ################### Configuration constants #############################

    C815_IDLE_STATE = "Idle"
    C815_SYSTEMMODEL = "C815_FlashAdvanced"

    # !!! THESE VALUES ARE AUTO-GENERATED FROM API SPECIFICATIONS !!!
    # ################### Process parameters #############################

    GET_SYSTEMCLASS = {'name': 'GET_SYSTEMCLASS', 'method': 'GET', 'endpoint': '/api/v1/Info', 'path': ['systemClass'], 'reply': {'type': str}}
    GET_SYSTEMLINE = {'name': 'GET_SYSTEMLINE', 'method': 'GET', 'endpoint': '/api/v1/Info', 'path': ['systemLine'], 'reply': {'type': str}}
    GET_SYSTEMNAME = {'name': 'GET_SYSTEMNAME', 'method': 'GET', 'endpoint': '/api/v1/Info', 'path': ['systemName'], 'reply': {'type': str}}
    GET_SYSTEMMODEL = {'name': 'GET_SYSTEMMODEL', 'method': 'GET', 'endpoint': '/api/v1/Info', 'path': ['systemModel'], 'reply': {'type': str}}
    GET_DETECTORS = {'name': 'GET_DETECTORS', 'method': 'GET', 'endpoint': '/api/v1/Info', 'path': ['detectors'], 'reply': {'type': list}}
    GET_PUMP_PUMPTYPE = {'name': 'GET_PUMP_PUMPTYPE', 'method': 'GET', 'endpoint': '/api/v1/Info', 'path': ['pump', 'pumpType'], 'reply': {'type': str}}
    GET_PUMP_FIRMWARE = {'name': 'GET_PUMP_FIRMWARE', 'method': 'GET', 'endpoint': '/api/v1/Info', 'path': ['pump', 'firmware'], 'reply': {'type': str}}
    GET_PUMP_HARDWARE = {'name': 'GET_PUMP_HARDWARE', 'method': 'GET', 'endpoint': '/api/v1/Info', 'path': ['pump', 'hardware'], 'reply': {'type': str}}
    GET_FRACTIONCOLLECTOR_FIRMWARE = {'name': 'GET_FRACTIONCOLLECTOR_FIRMWARE', 'method': 'GET', 'endpoint': '/api/v1/Info', 'path': ['fractionCollector', 'firmware'], 'reply': {'type': str}}
    GET_FRACTIONCOLLECTOR_TRAYS = {'name': 'GET_FRACTIONCOLLECTOR_TRAYS', 'method': 'GET', 'endpoint': '/api/v1/Info', 'path': ['fractionCollector', 'trays'], 'reply': {'type': list}}
    GET_COLUMN_VERSION = {'name': 'GET_COLUMN_VERSION', 'method': 'GET', 'endpoint': '/api/v1/Info', 'path': ['column', 'version'], 'reply': {'type': str}}
    GET_COLUMN_COLUMNNAME = {'name': 'GET_COLUMN_COLUMNNAME', 'method': 'GET', 'endpoint': '/api/v1/Info', 'path': ['column', 'columnName'], 'reply': {'type': str}}
    GET_COLUMN_DATA = {'name': 'GET_COLUMN_DATA', 'method': 'GET', 'endpoint': '/api/v1/Info', 'path': ['column', 'data'], 'reply': {'type': str}}
    GET_RUNNINGSTATE = {'name': 'GET_RUNNINGSTATE', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['runningState'], 'reply': {'type': str}}
    GET_RUNMODE = {'name': 'GET_RUNMODE', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['runMode'], 'reply': {'type': str}}
    GET_SENSORS_SOLVENTPRESSUREAFTERPUMP = {'name': 'GET_SENSORS_SOLVENTPRESSUREAFTERPUMP', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['sensors', 'solventPressureAfterPump'], 'reply': {'type': float}}
    GET_SENSORS_SOLVENTPRESSUREAFTERCOLUMN = {'name': 'GET_SENSORS_SOLVENTPRESSUREAFTERCOLUMN', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['sensors', 'solventPressureAfterColumn'], 'reply': {'type': float}}
    GET_SENSORS_AIRPRESSURENEBULIZER = {'name': 'GET_SENSORS_AIRPRESSURENEBULIZER', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['sensors', 'airPressureNebulizer'], 'reply': {'type': float}}
    GET_SENSORS_AIRPRESSUREINLET = {'name': 'GET_SENSORS_AIRPRESSUREINLET', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['sensors', 'airPressureInlet'], 'reply': {'type': float}}
    GET_SENSORS_VAPORLEVEL = {'name': 'GET_SENSORS_VAPORLEVEL', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['sensors', 'vaporLevel'], 'reply': {'type': int}}
    GET_SENSORS_SOLVENTLEVELS = {'name': 'GET_SENSORS_SOLVENTLEVELS', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['sensors', 'solventLevels'], 'reply': {'type': list}}
    GET_SENSORS_WASTELEVEL = {'name': 'GET_SENSORS_WASTELEVEL', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['sensors', 'wasteLevel'], 'reply': {'type': float}}
    GET_AIRSYSTEM_ISENABLED = {'name': 'GET_AIRSYSTEM_ISENABLED', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['airSystem', 'isEnabled'], 'reply': {'type': bool}}
    GET_AIRSYSTEM_VALVEPOS = {'name': 'GET_AIRSYSTEM_VALVEPOS', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['airSystem', 'valvePos'], 'reply': {'type': str}}
    GET_ELSDDETECTOR_LASERISENABLED = {'name': 'GET_ELSDDETECTOR_LASERISENABLED', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['elsdDetector', 'laserIsEnabled'], 'reply': {'type': bool}}
    GET_ELSDDETECTOR_LASERVOLTAGE = {'name': 'GET_ELSDDETECTOR_LASERVOLTAGE', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['elsdDetector', 'laserVoltage'], 'reply': {'type': float}}
    GET_ELSDDETECTOR_SHUTTLEVALVEISENABLED = {'name': 'GET_ELSDDETECTOR_SHUTTLEVALVEISENABLED', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['elsdDetector', 'shuttleValveIsEnabled'], 'reply': {'type': bool}}
    GET_ELSDDETECTOR_CARRIERFLOWISENABLED = {'name': 'GET_ELSDDETECTOR_CARRIERFLOWISENABLED', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['elsdDetector', 'carrierFlowIsEnabled'], 'reply': {'type': bool}}
    GET_ELSDDETECTOR_SENSITIVITY = {'name': 'GET_ELSDDETECTOR_SENSITIVITY', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['elsdDetector', 'sensitivity'], 'reply': {'type': str}}
    GET_ELSDDETECTOR_SIGNAL_TIMESINCESTART = {'name': 'GET_ELSDDETECTOR_SIGNAL_TIMESINCESTART', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['elsdDetector', 'signal', 'timeSinceStart'], 'reply': {'type': str}}
    GET_ELSDDETECTOR_SIGNAL_SIGNAL = {'name': 'GET_ELSDDETECTOR_SIGNAL_SIGNAL', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['elsdDetector', 'signal', 'signal'], 'reply': {'type': float}}
    GET_FRACTIONCOLLECTOR_POSITION_TRAY = {'name': 'GET_FRACTIONCOLLECTOR_POSITION_TRAY', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['fractionCollector', 'position', 'tray'], 'reply': {'type': str}}
    GET_FRACTIONCOLLECTOR_POSITION_VIAL = {'name': 'GET_FRACTIONCOLLECTOR_POSITION_VIAL', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['fractionCollector', 'position', 'vial'], 'reply': {'type': str}}
    GET_FRACTIONCOLLECTOR_COLLECTIONTASK_ACTION = {'name': 'GET_FRACTIONCOLLECTOR_COLLECTIONTASK_ACTION', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['fractionCollector', 'collectionTask', 'action'], 'reply': {'type': str}}
    GET_SOLVENTSYSTEM_FLOWISENABLED = {'name': 'GET_SOLVENTSYSTEM_FLOWISENABLED', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['solventSystem', 'flowIsEnabled'], 'reply': {'type': bool}}
    GET_SOLVENTSYSTEM_FLOWRATE = {'name': 'GET_SOLVENTSYSTEM_FLOWRATE', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['solventSystem', 'flowRate'], 'reply': {'type': int}}
    GET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE1PERCENTAGE = {'name': 'GET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE1PERCENTAGE', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['solventSystem', 'solventMixture', 'line1Percentage'], 'reply': {'type': float}}
    GET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE2PERCENTAGE = {'name': 'GET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE2PERCENTAGE', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['solventSystem', 'solventMixture', 'line2Percentage'], 'reply': {'type': float}}
    GET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE3PERCENTAGE = {'name': 'GET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE3PERCENTAGE', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['solventSystem', 'solventMixture', 'line3Percentage'], 'reply': {'type': float}}
    GET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE4PERCENTAGE = {'name': 'GET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE4PERCENTAGE', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['solventSystem', 'solventMixture', 'line4Percentage'], 'reply': {'type': float}}
    GET_SOLVENTSYSTEM_SAMPLEINJECTIONVALVEPOS = {'name': 'GET_SOLVENTSYSTEM_SAMPLEINJECTIONVALVEPOS', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['solventSystem', 'sampleInjectionValvePos'], 'reply': {'type': str}}
    GET_SOLVENTSYSTEM_MODE = {'name': 'GET_SOLVENTSYSTEM_MODE', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['solventSystem', 'mode'], 'reply': {'type': str}}
    GET_UVDETECTOR_ABSORBANCE_TIMESINCESTART = {'name': 'GET_UVDETECTOR_ABSORBANCE_TIMESINCESTART', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'absorbance', 'timeSinceStart'], 'reply': {'type': str}}
    GET_UVDETECTOR_ABSORBANCE_CH1 = {'name': 'GET_UVDETECTOR_ABSORBANCE_CH1', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'absorbance', 'ch1'], 'reply': {'type': float}}
    GET_UVDETECTOR_ABSORBANCE_CH2 = {'name': 'GET_UVDETECTOR_ABSORBANCE_CH2', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'absorbance', 'ch2'], 'reply': {'type': float}}
    GET_UVDETECTOR_ABSORBANCE_CH3 = {'name': 'GET_UVDETECTOR_ABSORBANCE_CH3', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'absorbance', 'ch3'], 'reply': {'type': float}}
    GET_UVDETECTOR_ABSORBANCE_CH4 = {'name': 'GET_UVDETECTOR_ABSORBANCE_CH4', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'absorbance', 'ch4'], 'reply': {'type': float}}
    GET_UVDETECTOR_ABSORBANCE_SCAN = {'name': 'GET_UVDETECTOR_ABSORBANCE_SCAN', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'absorbance', 'scan'], 'reply': {'type': float}}
    GET_UVDETECTOR_WAVELENGTHS_CH1 = {'name': 'GET_UVDETECTOR_WAVELENGTHS_CH1', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'wavelengths', 'ch1'], 'reply': {'type': int}}
    GET_UVDETECTOR_WAVELENGTHS_CH2 = {'name': 'GET_UVDETECTOR_WAVELENGTHS_CH2', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'wavelengths', 'ch2'], 'reply': {'type': int}}
    GET_UVDETECTOR_WAVELENGTHS_CH3 = {'name': 'GET_UVDETECTOR_WAVELENGTHS_CH3', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'wavelengths', 'ch3'], 'reply': {'type': int}}
    GET_UVDETECTOR_WAVELENGTHS_CH4 = {'name': 'GET_UVDETECTOR_WAVELENGTHS_CH4', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'wavelengths', 'ch4'], 'reply': {'type': int}}
    GET_UVDETECTOR_WAVELENGTHS_SCANSTART = {'name': 'GET_UVDETECTOR_WAVELENGTHS_SCANSTART', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'wavelengths', 'scanStart'], 'reply': {'type': int}}
    GET_UVDETECTOR_WAVELENGTHS_SCANEND = {'name': 'GET_UVDETECTOR_WAVELENGTHS_SCANEND', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'wavelengths', 'scanEnd'], 'reply': {'type': int}}
    GET_UVDETECTOR_ENABLEDCHANNELS_CH1 = {'name': 'GET_UVDETECTOR_ENABLEDCHANNELS_CH1', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'enabledChannels', 'ch1'], 'reply': {'type': str}}
    GET_UVDETECTOR_ENABLEDCHANNELS_CH2 = {'name': 'GET_UVDETECTOR_ENABLEDCHANNELS_CH2', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'enabledChannels', 'ch2'], 'reply': {'type': str}}
    GET_UVDETECTOR_ENABLEDCHANNELS_CH3 = {'name': 'GET_UVDETECTOR_ENABLEDCHANNELS_CH3', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'enabledChannels', 'ch3'], 'reply': {'type': str}}
    GET_UVDETECTOR_ENABLEDCHANNELS_CH4 = {'name': 'GET_UVDETECTOR_ENABLEDCHANNELS_CH4', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'enabledChannels', 'ch4'], 'reply': {'type': str}}
    GET_UVDETECTOR_ENABLEDCHANNELS_SCAN = {'name': 'GET_UVDETECTOR_ENABLEDCHANNELS_SCAN', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'enabledChannels', 'scan'], 'reply': {'type': str}}
    GET_UVDETECTOR_SENSITIVITY = {'name': 'GET_UVDETECTOR_SENSITIVITY', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'sensitivity'], 'reply': {'type': str}}
    GET_UVDETECTOR_SPECTRUM_TIMESINCESTART = {'name': 'GET_UVDETECTOR_SPECTRUM_TIMESINCESTART', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'spectrum', 'timeSinceStart'], 'reply': {'type': str}}
    GET_UVDETECTOR_SPECTRUM_VALUES = {'name': 'GET_UVDETECTOR_SPECTRUM_VALUES', 'method': 'GET', 'endpoint': '/api/v1/Process', 'path': ['uvDetector', 'spectrum', 'values'], 'reply': {'type': list}}
    SET_RUNMODE = {'name': 'SET_RUNMODE', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Flash', 'Prep']}, 'path': ['runMode']}
    SET_AIRSYSTEM_ISENABLED = {'name': 'SET_AIRSYSTEM_ISENABLED', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': bool, 'check': None, 'path': ['airSystem', 'isEnabled']}
    SET_AIRSYSTEM_VALVEPOS = {'name': 'SET_AIRSYSTEM_VALVEPOS', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Off', 'Elsd', 'Column']}, 'path': ['airSystem', 'valvePos']}
    SET_ELSDDETECTOR_LASERISENABLED = {'name': 'SET_ELSDDETECTOR_LASERISENABLED', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': bool, 'check': None, 'path': ['elsdDetector', 'laserIsEnabled']}
    SET_ELSDDETECTOR_SHUTTLEVALVEISENABLED = {'name': 'SET_ELSDDETECTOR_SHUTTLEVALVEISENABLED', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': bool, 'check': None, 'path': ['elsdDetector', 'shuttleValveIsEnabled']}
    SET_ELSDDETECTOR_CARRIERFLOWISENABLED = {'name': 'SET_ELSDDETECTOR_CARRIERFLOWISENABLED', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': bool, 'check': None, 'path': ['elsdDetector', 'carrierFlowIsEnabled']}
    SET_ELSDDETECTOR_SENSITIVITY = {'name': 'SET_ELSDDETECTOR_SENSITIVITY', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Low', 'High']}, 'path': ['elsdDetector', 'sensitivity']}
    SET_FRACTIONCOLLECTOR_POSITION_TRAY = {'name': 'SET_FRACTIONCOLLECTOR_POSITION_TRAY', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Left', 'Right', 'Unknown']}, 'path': ['fractionCollector', 'position', 'tray']}
    SET_FRACTIONCOLLECTOR_POSITION_VIAL = {'name': 'SET_FRACTIONCOLLECTOR_POSITION_VIAL', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Unknown', 'Home']}, 'path': ['fractionCollector', 'position', 'vial']}
    SET_FRACTIONCOLLECTOR_COLLECTIONTASK_ACTION = {'name': 'SET_FRACTIONCOLLECTOR_COLLECTIONTASK_ACTION', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Waste', 'Vial']}, 'path': ['fractionCollector', 'collectionTask', 'action']}
    SET_SOLVENTSYSTEM_FLOWISENABLED = {'name': 'SET_SOLVENTSYSTEM_FLOWISENABLED', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': bool, 'check': None, 'path': ['solventSystem', 'flowIsEnabled']}
    SET_SOLVENTSYSTEM_FLOWRATE = {'name': 'SET_SOLVENTSYSTEM_FLOWRATE', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': int, 'check': None, 'path': ['solventSystem', 'flowRate']}
    SET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE1PERCENTAGE = {'name': 'SET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE1PERCENTAGE', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': float, 'check': None, 'path': ['solventSystem', 'solventMixture', 'line1Percentage']}
    SET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE2PERCENTAGE = {'name': 'SET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE2PERCENTAGE', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': float, 'check': None, 'path': ['solventSystem', 'solventMixture', 'line2Percentage']}
    SET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE3PERCENTAGE = {'name': 'SET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE3PERCENTAGE', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': float, 'check': None, 'path': ['solventSystem', 'solventMixture', 'line3Percentage']}
    SET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE4PERCENTAGE = {'name': 'SET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE4PERCENTAGE', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': float, 'check': None, 'path': ['solventSystem', 'solventMixture', 'line4Percentage']}
    SET_SOLVENTSYSTEM_SAMPLEINJECTIONVALVEPOS = {'name': 'SET_SOLVENTSYSTEM_SAMPLEINJECTIONVALVEPOS', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Load', 'Separation']}, 'path': ['solventSystem', 'sampleInjectionValvePos']}
    SET_SOLVENTSYSTEM_MODE = {'name': 'SET_SOLVENTSYSTEM_MODE', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Flash', 'Prep']}, 'path': ['solventSystem', 'mode']}
    SET_UVDETECTOR_WAVELENGTHS_CH1 = {'name': 'SET_UVDETECTOR_WAVELENGTHS_CH1', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': int, 'check': None, 'path': ['uvDetector', 'wavelengths', 'ch1']}
    SET_UVDETECTOR_WAVELENGTHS_CH2 = {'name': 'SET_UVDETECTOR_WAVELENGTHS_CH2', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': int, 'check': None, 'path': ['uvDetector', 'wavelengths', 'ch2']}
    SET_UVDETECTOR_WAVELENGTHS_CH3 = {'name': 'SET_UVDETECTOR_WAVELENGTHS_CH3', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': int, 'check': None, 'path': ['uvDetector', 'wavelengths', 'ch3']}
    SET_UVDETECTOR_WAVELENGTHS_CH4 = {'name': 'SET_UVDETECTOR_WAVELENGTHS_CH4', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': int, 'check': None, 'path': ['uvDetector', 'wavelengths', 'ch4']}
    SET_UVDETECTOR_WAVELENGTHS_SCANSTART = {'name': 'SET_UVDETECTOR_WAVELENGTHS_SCANSTART', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': int, 'check': None, 'path': ['uvDetector', 'wavelengths', 'scanStart']}
    SET_UVDETECTOR_WAVELENGTHS_SCANEND = {'name': 'SET_UVDETECTOR_WAVELENGTHS_SCANEND', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': int, 'check': None, 'path': ['uvDetector', 'wavelengths', 'scanEnd']}
    SET_UVDETECTOR_ENABLEDCHANNELS_CH1 = {'name': 'SET_UVDETECTOR_ENABLEDCHANNELS_CH1', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Off', 'On', 'Monitor']}, 'path': ['uvDetector', 'enabledChannels', 'ch1']}
    SET_UVDETECTOR_ENABLEDCHANNELS_CH2 = {'name': 'SET_UVDETECTOR_ENABLEDCHANNELS_CH2', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Off', 'On', 'Monitor']}, 'path': ['uvDetector', 'enabledChannels', 'ch2']}
    SET_UVDETECTOR_ENABLEDCHANNELS_CH3 = {'name': 'SET_UVDETECTOR_ENABLEDCHANNELS_CH3', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Off', 'On', 'Monitor']}, 'path': ['uvDetector', 'enabledChannels', 'ch3']}
    SET_UVDETECTOR_ENABLEDCHANNELS_CH4 = {'name': 'SET_UVDETECTOR_ENABLEDCHANNELS_CH4', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Off', 'On', 'Monitor']}, 'path': ['uvDetector', 'enabledChannels', 'ch4']}
    SET_UVDETECTOR_ENABLEDCHANNELS_SCAN = {'name': 'SET_UVDETECTOR_ENABLEDCHANNELS_SCAN', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Off', 'On', 'Monitor']}, 'path': ['uvDetector', 'enabledChannels', 'scan']}
    SET_UVDETECTOR_SENSITIVITY = {'name': 'SET_UVDETECTOR_SENSITIVITY', 'method': 'PUT', 'endpoint': '/api/v1/Process', 'type': str, 'check': {'values': ['Low', 'High']}, 'path': ['uvDetector', 'sensitivity']}


class C815FlashChromatographySystem(AbstractFlashChromatographySystem):
    """
    This provides a Python class for the Buchi C815 flash chromatography system
    based on the Buchi OpenAPI specification v.1
    """

    def __init__(self,
                 device_name: str,
                 connection_mode: str,
                 address: Optional[str],
                 port: Union[str, int],
                 user: Optional[str],
                 password: Optional[str]) -> None:

        # Load commands from helper class
        self.cmd = C815Commands

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        connection_parameters["user"] = user
        connection_parameters["schema"] = "http"
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
        warnings.filterwarnings("ignore", message="InsecureRequestWarning")

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

        # Extract required element from JSON tree
        for item in cmd["path"]:
            reply = reply[item]
        # Run text parsing / type casting, if any
        return super().parse_reply(cmd, reply)

    def initialize_device(self) -> None:
        """ Initialization sequence
        """
        # TODO Add any initialization if necessary

    @in_simulation_device_returns(C815Commands.C815_SYSTEMMODEL)
    def is_connected(self) -> bool:
        """ Stateless device - always connected
        """

        try:
            return self.send(self.cmd.GET_SYSTEMMODEL) == self.cmd.C815_SYSTEMMODEL
        except PLConnectionError:
            return False

    @in_simulation_device_returns(C815Commands.C815_IDLE_STATE)
    def is_idle(self) -> bool:
        """ Checks whether the device is idle
        """

        return self.get_runningstate == self.cmd.C815_IDLE_STATE

    def check_errors(self) -> None:
        """ Not supported on this model
        """

    def clear_errors(self) -> None:
        """ Not supported on this model
        """

    def get_status(self) -> str:
        """ Gets device status.
        """

        return self.get_runningstate()

    def get_systemclass(self) -> str:
        """
        """

        return self.send(self.cmd.GET_SYSTEMCLASS)

    def get_systemline(self) -> str:
        """
        """

        return self.send(self.cmd.GET_SYSTEMLINE)

    def get_systemname(self) -> str:
        """
        """

        return self.send(self.cmd.GET_SYSTEMNAME)

    def get_systemmodel(self) -> str:
        """
        """

        return self.send(self.cmd.GET_SYSTEMMODEL)

    def get_detectors(self) -> list:
        """
        """

        return self.send(self.cmd.GET_DETECTORS)

    def get_pump_pumptype(self) -> str:
        """
        """

        return self.send(self.cmd.GET_PUMP_PUMPTYPE)

    def get_pump_firmware(self) -> str:
        """
        """

        return self.send(self.cmd.GET_PUMP_FIRMWARE)

    def get_pump_hardware(self) -> str:
        """
        """

        return self.send(self.cmd.GET_PUMP_HARDWARE)

    def get_fractioncollector_firmware(self) -> str:
        """
        """

        return self.send(self.cmd.GET_FRACTIONCOLLECTOR_FIRMWARE)

    def get_fractioncollector_trays(self) -> list:
        """
        """

        return self.send(self.cmd.GET_FRACTIONCOLLECTOR_TRAYS)

    def get_column_version(self) -> str:
        """
        """

        return self.send(self.cmd.GET_COLUMN_VERSION)

    def get_column_columnname(self) -> str:
        """
        """

        return self.send(self.cmd.GET_COLUMN_COLUMNNAME)

    def get_column_data(self) -> str:
        """
        """

        return self.send(self.cmd.GET_COLUMN_DATA)

    def get_runningstate(self) -> str:
        """
        """

        return self.send(self.cmd.GET_RUNNINGSTATE)

    def get_runmode(self) -> str:
        """
        """

        return self.send(self.cmd.GET_RUNMODE)

    def get_sensors_solventpressureafterpump(self) -> float:
        """
        """

        return self.send(self.cmd.GET_SENSORS_SOLVENTPRESSUREAFTERPUMP)

    def get_sensors_solventpressureaftercolumn(self) -> float:
        """
        """

        return self.send(self.cmd.GET_SENSORS_SOLVENTPRESSUREAFTERCOLUMN)

    def get_sensors_airpressurenebulizer(self) -> float:
        """
        """

        return self.send(self.cmd.GET_SENSORS_AIRPRESSURENEBULIZER)

    def get_sensors_airpressureinlet(self) -> float:
        """
        """

        return self.send(self.cmd.GET_SENSORS_AIRPRESSUREINLET)

    def get_sensors_vaporlevel(self) -> int:
        """
        """

        return self.send(self.cmd.GET_SENSORS_VAPORLEVEL)

    def get_sensors_solventlevels(self) -> list:
        """
        """

        return self.send(self.cmd.GET_SENSORS_SOLVENTLEVELS)

    def get_sensors_wastelevel(self) -> float:
        """
        """

        return self.send(self.cmd.GET_SENSORS_WASTELEVEL)

    def get_airsystem_isenabled(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_AIRSYSTEM_ISENABLED)

    def get_airsystem_valvepos(self) -> str:
        """
        """

        return self.send(self.cmd.GET_AIRSYSTEM_VALVEPOS)

    def get_elsddetector_laserisenabled(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_ELSDDETECTOR_LASERISENABLED)

    def get_elsddetector_laservoltage(self) -> float:
        """
        """

        return self.send(self.cmd.GET_ELSDDETECTOR_LASERVOLTAGE)

    def get_elsddetector_shuttlevalveisenabled(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_ELSDDETECTOR_SHUTTLEVALVEISENABLED)

    def get_elsddetector_carrierflowisenabled(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_ELSDDETECTOR_CARRIERFLOWISENABLED)

    def get_elsddetector_sensitivity(self) -> str:
        """
        """

        return self.send(self.cmd.GET_ELSDDETECTOR_SENSITIVITY)

    def get_elsddetector_signal_timesincestart(self) -> str:
        """
        """

        return self.send(self.cmd.GET_ELSDDETECTOR_SIGNAL_TIMESINCESTART)

    def get_elsddetector_signal_signal(self) -> float:
        """
        """

        return self.send(self.cmd.GET_ELSDDETECTOR_SIGNAL_SIGNAL)

    def get_fractioncollector_position_tray(self) -> str:
        """
        """

        return self.send(self.cmd.GET_FRACTIONCOLLECTOR_POSITION_TRAY)

    def get_fractioncollector_position_vial(self) -> str:
        """
        """

        return self.send(self.cmd.GET_FRACTIONCOLLECTOR_POSITION_VIAL)

    def get_fractioncollector_collectiontask_action(self) -> str:
        """
        """

        return self.send(self.cmd.GET_FRACTIONCOLLECTOR_COLLECTIONTASK_ACTION)

    def get_solventsystem_flowisenabled(self) -> bool:
        """
        """

        return self.send(self.cmd.GET_SOLVENTSYSTEM_FLOWISENABLED)

    def get_solventsystem_flowrate(self) -> int:
        """
        """

        return self.send(self.cmd.GET_SOLVENTSYSTEM_FLOWRATE)

    def get_solventsystem_solventmixture_line1percentage(self) -> float:
        """
        """

        return self.send(self.cmd.GET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE1PERCENTAGE)

    def get_solventsystem_solventmixture_line2percentage(self) -> float:
        """
        """

        return self.send(self.cmd.GET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE2PERCENTAGE)

    def get_solventsystem_solventmixture_line3percentage(self) -> float:
        """
        """

        return self.send(self.cmd.GET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE3PERCENTAGE)

    def get_solventsystem_solventmixture_line4percentage(self) -> float:
        """
        """

        return self.send(self.cmd.GET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE4PERCENTAGE)

    def get_solventsystem_sampleinjectionvalvepos(self) -> str:
        """
        """

        return self.send(self.cmd.GET_SOLVENTSYSTEM_SAMPLEINJECTIONVALVEPOS)

    def get_solventsystem_mode(self) -> str:
        """
        """

        return self.send(self.cmd.GET_SOLVENTSYSTEM_MODE)

    def get_uvdetector_absorbance_timesincestart(self) -> str:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_ABSORBANCE_TIMESINCESTART)

    def get_uvdetector_absorbance_ch1(self) -> float:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_ABSORBANCE_CH1)

    def get_uvdetector_absorbance_ch2(self) -> float:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_ABSORBANCE_CH2)

    def get_uvdetector_absorbance_ch3(self) -> float:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_ABSORBANCE_CH3)

    def get_uvdetector_absorbance_ch4(self) -> float:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_ABSORBANCE_CH4)

    def get_uvdetector_absorbance_scan(self) -> float:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_ABSORBANCE_SCAN)

    def get_uvdetector_wavelengths_ch1(self) -> int:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_WAVELENGTHS_CH1)

    def get_uvdetector_wavelengths_ch2(self) -> int:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_WAVELENGTHS_CH2)

    def get_uvdetector_wavelengths_ch3(self) -> int:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_WAVELENGTHS_CH3)

    def get_uvdetector_wavelengths_ch4(self) -> int:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_WAVELENGTHS_CH4)

    def get_uvdetector_wavelengths_scanstart(self) -> int:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_WAVELENGTHS_SCANSTART)

    def get_uvdetector_wavelengths_scanend(self) -> int:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_WAVELENGTHS_SCANEND)

    def get_uvdetector_enabledchannels_ch1(self) -> str:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_ENABLEDCHANNELS_CH1)

    def get_uvdetector_enabledchannels_ch2(self) -> str:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_ENABLEDCHANNELS_CH2)

    def get_uvdetector_enabledchannels_ch3(self) -> str:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_ENABLEDCHANNELS_CH3)

    def get_uvdetector_enabledchannels_ch4(self) -> str:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_ENABLEDCHANNELS_CH4)

    def get_uvdetector_enabledchannels_scan(self) -> str:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_ENABLEDCHANNELS_SCAN)

    def get_uvdetector_sensitivity(self) -> str:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_SENSITIVITY)

    def get_uvdetector_spectrum_timesincestart(self) -> str:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_SPECTRUM_TIMESINCESTART)

    def get_uvdetector_spectrum_values(self) -> list:
        """
        """

        return self.send(self.cmd.GET_UVDETECTOR_SPECTRUM_VALUES)

    def set_runmode(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_RUNMODE, value)

    def set_airsystem_isenabled(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_AIRSYSTEM_ISENABLED, value)

    def set_airsystem_valvepos(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_AIRSYSTEM_VALVEPOS, value)

    def set_elsddetector_laserisenabled(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_ELSDDETECTOR_LASERISENABLED, value)

    def set_elsddetector_shuttlevalveisenabled(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_ELSDDETECTOR_SHUTTLEVALVEISENABLED, value)

    def set_elsddetector_carrierflowisenabled(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_ELSDDETECTOR_CARRIERFLOWISENABLED, value)

    def set_elsddetector_sensitivity(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_ELSDDETECTOR_SENSITIVITY, value)

    def set_fractioncollector_position_tray(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_FRACTIONCOLLECTOR_POSITION_TRAY, value)

    def set_fractioncollector_position_vial(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_FRACTIONCOLLECTOR_POSITION_VIAL, value)

    def set_fractioncollector_collectiontask_action(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_FRACTIONCOLLECTOR_COLLECTIONTASK_ACTION, value)

    def set_solventsystem_flowisenabled(self, value: bool) -> None:
        """
        """

        self.send(self.cmd.SET_SOLVENTSYSTEM_FLOWISENABLED, value)

    def set_solventsystem_flowrate(self, value: int) -> None:
        """
        """

        self.send(self.cmd.SET_SOLVENTSYSTEM_FLOWRATE, value)

    def set_solventsystem_solventmixture_line1percentage(self, value: float) -> None:
        """
        """

        self.send(self.cmd.SET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE1PERCENTAGE, value)

    def set_solventsystem_solventmixture_line2percentage(self, value: float) -> None:
        """
        """

        self.send(self.cmd.SET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE2PERCENTAGE, value)

    def set_solventsystem_solventmixture_line3percentage(self, value: float) -> None:
        """
        """

        self.send(self.cmd.SET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE3PERCENTAGE, value)

    def set_solventsystem_solventmixture_line4percentage(self, value: float) -> None:
        """
        """

        self.send(self.cmd.SET_SOLVENTSYSTEM_SOLVENTMIXTURE_LINE4PERCENTAGE, value)

    def set_solventsystem_sampleinjectionvalvepos(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_SOLVENTSYSTEM_SAMPLEINJECTIONVALVEPOS, value)

    def set_solventsystem_mode(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_SOLVENTSYSTEM_MODE, value)

    def set_uvdetector_wavelengths_ch1(self, value: int) -> None:
        """
        """

        self.send(self.cmd.SET_UVDETECTOR_WAVELENGTHS_CH1, value)

    def set_uvdetector_wavelengths_ch2(self, value: int) -> None:
        """
        """

        self.send(self.cmd.SET_UVDETECTOR_WAVELENGTHS_CH2, value)

    def set_uvdetector_wavelengths_ch3(self, value: int) -> None:
        """
        """

        self.send(self.cmd.SET_UVDETECTOR_WAVELENGTHS_CH3, value)

    def set_uvdetector_wavelengths_ch4(self, value: int) -> None:
        """
        """

        self.send(self.cmd.SET_UVDETECTOR_WAVELENGTHS_CH4, value)

    def set_uvdetector_wavelengths_scanstart(self, value: int) -> None:
        """
        """

        self.send(self.cmd.SET_UVDETECTOR_WAVELENGTHS_SCANSTART, value)

    def set_uvdetector_wavelengths_scanend(self, value: int) -> None:
        """
        """

        self.send(self.cmd.SET_UVDETECTOR_WAVELENGTHS_SCANEND, value)

    def set_uvdetector_enabledchannels_ch1(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_UVDETECTOR_ENABLEDCHANNELS_CH1, value)

    def set_uvdetector_enabledchannels_ch2(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_UVDETECTOR_ENABLEDCHANNELS_CH2, value)

    def set_uvdetector_enabledchannels_ch3(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_UVDETECTOR_ENABLEDCHANNELS_CH3, value)

    def set_uvdetector_enabledchannels_ch4(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_UVDETECTOR_ENABLEDCHANNELS_CH4, value)

    def set_uvdetector_enabledchannels_scan(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_UVDETECTOR_ENABLEDCHANNELS_SCAN, value)

    def set_uvdetector_sensitivity(self, value: str) -> None:
        """
        """

        self.send(self.cmd.SET_UVDETECTOR_SENSITIVITY, value)
