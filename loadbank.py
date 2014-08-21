4  #!/usr/bin/python3

# TDi Loadbank Controller

# Copyright (C) 2014  Simon Howroyd
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.


# Includes
import telnetlib, time


class TdiLoadbank():
    __LOAD_COMMAND = "load"
    __RANGE_COMMAND = "rng"
    __MODE_COMMAND = "mode"
    __VOLTAGE_COMMAND = "v"
    __CURRENT_COMMAND = "i"
    __POWER_COMMAND = "p"
    __VOLTAGE_LIMIT_COMMAND = "vl"
    __CURRENT_LIMIT_COMMAND = "il"
    __POWER_LIMIT_COMMAND = "pl"
    __VOLTAGE_MINIMUM_COMMAND = "uv"

    __CONSTANT_VOLTAGE_COMMAND = "cv"
    __CONSTANT_CURRENT_COMMAND = "ci"
    __CONSTANT_POWER_COMMAND = "cp"

    __mode    = ""
    __voltage = 0
    __current = 0
    __power   = 0    
    __set_v   = "0"
    __set_i   = "0"
    __set_p   = "0"

    def __init__(self, HOST, PORT=23, password=''):
        self.__HOST = HOST
        self.__PORT = PORT  # Default 23 if not specified
        self.__password = password  # Default blank if not specified
        self._tn = self._connect(HOST, PORT, password)

        self.__set_v = self._get(self._tn, self.__CONSTANT_VOLTAGE_COMMAND).split()[0]
        self.__set_i = self._get(self._tn, self.__CONSTANT_CURRENT_COMMAND).split()[0]
        self.__set_p = self._get(self._tn, self.__CONSTANT_POWER_COMMAND).split()[0]

        self.mode = self._get(self._tn, self.__MODE_COMMAND)


    # Telnet connect method
    @classmethod
    def _connect(cls, HOST, PORT, password):
        tn = telnetlib.Telnet(HOST, PORT)
        if password:
            tn.read_until(b"Password ? ")
            tn.write(password.encode('ascii') + b"\r\n")
        cls._flush(tn)  # Flush read buffer (needed)
        print('\nLoadbank connected!\n')
        return tn

    def shutdown(self):
        self._tn.close()
        return 1

    @staticmethod
    def _flush(tn):
        tn.read_very_eager()  # Flush read buffer

    @classmethod
    def _set(cls, tn, command, value):
        buf = (command + ' ' + value + '\r')
        cls._send(tn, buf)

    @classmethod
    def _get(cls, tn, command):
        if not command.endswith('?'):
            command += '?'
        buf = (command + '\r')
        return str(cls._send(tn, buf))

    @classmethod
    def _get_float(cls, tn, command):
        data = cls._get(tn, command)
        try: # Recursive until we get a valid answer
            return float(data.split()[0])
        except ValueError:
            return cls._get_float(tn, command)

    # Method to handle data 2way telnet datastream
    @classmethod
    def _send(cls, tn, inbuf):
        cls._flush(tn)  # Flush read buffer (needed)
        outbuf = ""

        tn.write(inbuf.encode('ascii'))

        if '?' in inbuf:
            if 'v' in inbuf:
                expected = b'volts'
            elif 'i' in inbuf:
                expected = b'amps'
            elif 'p' in inbuf:
                expected = b'watts'
            elif 'rng' in inbuf:
                expected = b'AMP'
            else:
                expected = b'\r'

            while not outbuf or outbuf.isspace():
                outbuf = tn.read_until(expected, 0.1)  # Timeout = 0.1sec TODO
                outbuf = outbuf.decode('ascii').strip('\r\n')
                if not outbuf or outbuf.isspace():
                    cls._flush(tn)  # Flush read buffer (needed)
                    tn.write(inbuf.encode('ascii'))

            return outbuf
        else:
            return inbuf
        return

    # LOAD ON/OFF
    @property
    def load(self):
        state = self._get(self._tn, self.__LOAD_COMMAND)
        if "on" in state:
            return True
        elif "off" in state:
            return False
        else:
            return "UNKNOWN STATE"

    @load.setter
    def load(self, state):
        if state:
            self._set(self._tn, self.__LOAD_COMMAND, "on")
        else:
            self._set(self._tn, self.__LOAD_COMMAND, "off")

    # RANGE 1-9
    @property
    def range(self):
        return self._get(self._tn, self.__RANGE_COMMAND)

    @range.setter
    def range(self, setting):
        if int(setting) in range(1,10):
            self._set(self._tn, self.__RANGE_COMMAND, setting)
            print('Set new rng ' + self.range)
        else:
            print('Invalid range setting for loadbank')

    # MODE
    @property
    def mode(self):
        if "VOLTAGE" in self.__mode:
            return self.__mode + " " + str(self.voltage_constant)
        elif "CURRENT" in self.__mode:
            return self.__mode + " " + str(self.current_constant)
        elif "POWER" in self.__mode:
            return self.__mode + " " + str(self.power_constant)
        else:
            self.__setpoint = "error getting mode"

    @mode.setter
    def mode(self, op_mode):
        op_mode = op_mode.lower()  # Change any capitals to lower case
        if "vo" in op_mode or "cv" in op_mode:
            self._set(self._tn, self.__MODE_COMMAND, self.__CONSTANT_VOLTAGE_COMMAND)
            self.__mode =  "VOLTAGE"            
        elif "cu" in op_mode or "ci" in op_mode:
            self._set(self._tn, self.__MODE_COMMAND, self.__CONSTANT_CURRENT_COMMAND)
            self.__mode =  "CURRENT"
        elif "po" in op_mode or "cp" in op_mode:
            self._set(self._tn, self.__MODE_COMMAND, self.__CONSTANT_POWER_COMMAND)
            self.__mode =  "POWER"


    def update(self):
        self.__voltage = self._get_float(self._tn, self.__VOLTAGE_COMMAND)
        self.__current = self._get_float(self._tn, self.__CURRENT_COMMAND)
        self.__power   = self._get_float(self._tn, self.__POWER_COMMAND)


    # VOLTAGE CONTROL
    @property
    def voltage(self):
        return self.__voltage

    @voltage.setter
    def voltage(self, volts):
        self._set(self._tn, self.__VOLTAGE_COMMAND, volts)

    @property
    def voltage_constant(self):
        return self.__set_v

    @voltage_constant.setter
    def voltage_constant(self, volts):
        self._set(self._tn, self.__CONSTANT_VOLTAGE_COMMAND, volts)
        self.__set_v = volts

    @property
    def voltage_limit(self):
        return self._get_float(self._tn, self.__VOLTAGE_LIMIT_COMMAND)

    @voltage_limit.setter
    def voltage_limit(self, volts):
        self._set(self._tn, self.__VOLTAGE_LIMIT_COMMAND, volts)

    @property
    def voltage_minimum(self):
        return self._get_float(self._tn, self.__VOLTAGE_MINIMUM_COMMAND)

    @voltage_minimum.setter
    def voltage_minimum(self, volts):
        self._set(self._tn, self.__VOLTAGE_MINIMUM_COMMAND, volts)


    # CURRENT CONTROL
    @property
    def current(self):
        return self.__current

    @current.setter
    def current(self, amps):
        self._set(self._tn, self.__CURRENT_COMMAND, amps)

    @property
    def current_constant(self):
        return self.__set_i

    @current_constant.setter
    def current_constant(self, amps):
        self._set(self._tn, self.__CONSTANT_CURRENT_COMMAND, amps)
        self.__set_i = amps
 
    @property
    def current_limit(self):
        return self._get_float(self._tn, self.__CURRENT_LIMIT_COMMAND)

    @current_limit.setter
    def current_limit(self, amps):
        self._set(self._tn, self.__CURRENT_LIMIT_COMMAND, amps)


    # POWER CONTROL
    @property
    def power(self):
        return self.__power

    @power.setter
    def power(self, watts):
        self._set(self._tn, self.__POWER_COMMAND, watts)

    @property
    def power_constant(self):
        return self.__set_p

    @power_constant.setter
    def power_constant(self, watts):
        self._set(self._tn, self.__CONSTANT_POWER_COMMAND, watts)
        self.__set_p = watts

    @property
    def power_limit(self):
        return self._get_float(self._tn, self.__POWER_LIMIT_COMMAND)

    @power_limit.setter
    def power_limit(self, watts):
        self._set(self._tn, self.__POWER_LIMIT_COMMAND, watts)
