#############################################################################
# PDDF
# Module contains an implementation of SONiC PDDF Chassis Base API and
# provides the chassis information
#
#############################################################################

try:
    import sys
    from sonic_platform_base.chassis_base import ChassisBase
    from sonic_platform.sfp import Sfp
    from sonic_platform.psu import Psu
    from sonic_platform.fan_drawer import FanDrawer
    from sonic_platform.thermal import Thermal
    from sonic_platform.eeprom import Eeprom
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class PddfChassis(ChassisBase):
    """
    PDDF Generic Chassis class
    """
    pddf_obj = {}
    plugin_data = {}

    def __init__(self, pddf_data=None, pddf_plugin_data=None):

        ChassisBase.__init__(self)

        self.pddf_obj = pddf_data if pddf_data else None
        self.plugin_data = pddf_plugin_data if pddf_plugin_data else None
        if not self.pddf_obj or not self.plugin_data:
            try:
                from . import pddfapi
                import json
                self.pddf_obj = pddfapi.PddfApi()
                with open('/usr/share/sonic/platform/pddf/pd-plugin.json') as pd:
                    self.plugin_data = json.load(pd)
            except Exception as e:
                raise Exception("Error: Unable to load PDDF JSON data - %s" % str(e))

        self.platform_inventory = self.pddf_obj.get_platform()

        # Initialize EEPROM
        try:
            self._eeprom = Eeprom(self.pddf_obj, self.plugin_data)
        except Exception as err:
            sys.stderr.write("Unable to initialize syseeprom - {}".format(repr(err)))
            # Dont exit as we dont want failure in loading other components


        # FANs
        for i in range(self.platform_inventory['num_fantrays']):
            fandrawer = FanDrawer(i, self.pddf_obj, self.plugin_data)
            self._fan_drawer_list.append(fandrawer)
            self._fan_list.extend(fandrawer._fan_list)

        # PSUs
        for i in range(self.platform_inventory['num_psus']):
            psu = Psu(i, self.pddf_obj, self.plugin_data)
            self._psu_list.append(psu)

        # OPTICs
        for index in range(self.platform_inventory['num_ports']):
            sfp = Sfp(index, self.pddf_obj, self.plugin_data)
            self._sfp_list.append(sfp)

        # THERMALs
        for i in range(self.platform_inventory['num_temps']):
            thermal = Thermal(i, self.pddf_obj, self.plugin_data)
            self._thermal_list.append(thermal)


    def get_name(self):
        """
        Retrieves the name of the chassis
        Returns:
            string: The name of the chassis
        """
        return self._eeprom.modelstr()

    def get_presence(self):
        """
        Retrieves the presence of the chassis
        Returns:
            bool: True if chassis is present, False if not
        """
        return True

    def get_model(self):
        """
        Retrieves the model number (or part number) of the chassis
        Returns:
            string: Model/part number of chassis
        """
        return self._eeprom.part_number_str()

    def get_serial(self):
        """
        Retrieves the serial number of the chassis (Service tag)
        Returns:
            string: Serial number of chassis
        """
        return self._eeprom.serial_str()

    def get_status(self):
        """
        Retrieves the operational status of the chassis
        Returns:
            bool: A boolean value, True if chassis is operating properly
            False if not
        """
        return True

    def get_base_mac(self):
        """
        Retrieves the base MAC address for the chassis

        Returns:
            A string containing the MAC address in the format
            'XX:XX:XX:XX:XX:XX'
        """
        return self._eeprom.base_mac_addr()

    def get_serial_number(self):
        """
        Retrieves the hardware serial number for the chassis

        Returns:
            A string containing the hardware serial number for this
            chassis.
        """
        return self._eeprom.serial_number_str()

    def get_system_eeprom_info(self):
        """
        Retrieves the full content of system EEPROM information for the chassis
        Returns:
            A dictionary where keys are the type code defined in
            OCP ONIE TlvInfo EEPROM format and values are their corresponding
            values.
        """
        return self._eeprom.system_eeprom_info()

    def get_reboot_cause(self):
        """
        Retrieves the cause of the previous reboot

        Returns:
            A tuple (string, string) where the first element is a string
            containing the cause of the previous reboot. This string must be
            one of the predefined strings in this class. If the first string
            is "REBOOT_CAUSE_HARDWARE_OTHER", the second string can be used
            to pass a description of the reboot cause.
        """
        raise NotImplementedError

    ##############################################
    # Component methods
    ##############################################

    ##############################################
    # Module methods
    ##############################################
    # All module methods are part of chassis_base.py
    # if they need to be overwritten, define them here

    ##############################################
    # Fan methods
    ##############################################
    # All fan methods are part of chassis_base.py
    # if they need to be overwritten, define them here

    ##############################################
    # PSU methods
    ##############################################
    # All psu methods are part of chassis_base.py
    # if they need to be overwritten, define them here

    ##############################################
    # THERMAL methods
    ##############################################
    # All thermal methods are part of chassis_base.py
    # if they need to be overwritten, define them here

    ##############################################
    # SFP methods
    ##############################################
    # All sfp methods are part of chassis_base.py
    # if they need to be overwritten, define them here

    ##############################################
    # System LED  methods
    ##############################################
    def set_system_led(self, led_device_name, color):
        result, msg = self.pddf_obj.is_supported_sysled_state(led_device_name, color)
        if result == False:
            print(msg)
            return (False)

        index = self.pddf_obj.data[led_device_name]['dev_attr']['index']
        device_name = self.pddf_obj.data[led_device_name]['dev_info']['device_name']
        self.pddf_obj.create_attr('device_name', device_name,  self.pddf_obj.get_led_path())
        self.pddf_obj.create_attr('index', index, self.pddf_obj.get_led_path())
        self.pddf_obj.create_attr('color', color, self.pddf_obj.get_led_cur_state_path())
        self.pddf_obj.create_attr('dev_ops', 'set_status',  self.pddf_obj.get_led_path())
        return (True)

    def get_system_led(self, led_device_name):
        if led_device_name not in self.pddf_obj.data.keys():
            status = "[FAILED] " + led_device_name + " is not configured"
            return (status)

        index = self.pddf_obj.data[led_device_name]['dev_attr']['index']
        device_name = self.pddf_obj.data[led_device_name]['dev_info']['device_name']
        self.pddf_obj.create_attr('device_name', device_name,  self.pddf_obj.get_led_path())
        self.pddf_obj.create_attr('index', index, self.pddf_obj.get_led_path())
        self.pddf_obj.create_attr('dev_ops', 'get_status',  self.pddf_obj.get_led_path())
        color = self.pddf_obj.get_led_color()
        return (color)

    ##############################################
    # Other methods
    ##############################################
