#!/usr/bin/python3

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

#############################################################################

# Import Libraries
import telnetlib, time, os


# Define Class
class TdiLoadbank():
    # Code to run when class is created
    def __init__(self, HOST, PORT=23, password=''):
        
        # Define network connection information
        self.__HOST = HOST
        self.__PORT = PORT  # Default 23 if not specified
        self.__password = password  # Default blank if not specified
        
        # Define Loadbank commands
        self.__LOAD_COMMAND = "load"
        self.__RANGE_COMMAND = "rng"
        self.__MODE_COMMAND = "mode"
        self.__VOLTAGE_COMMAND = "v"
        self.__CURRENT_COMMAND = "i"
        self.__POWER_COMMAND = "p"
        self.__VOLTAGE_LIMIT_COMMAND = "vl"
        self.__CURRENT_LIMIT_COMMAND = "il"
        self.__POWER_LIMIT_COMMAND = "pl"
        self.__VOLTAGE_MINIMUM_COMMAND = "uv"
        self.__CONSTANT_VOLTAGE_COMMAND = "cv"
        self.__CONSTANT_CURRENT_COMMAND = "ci"
        self.__CONSTANT_POWER_COMMAND = "cp"

        # Define internal variables
        self.__mode    = ""
        self.__voltage = 0
        self.__current = 0
        self.__power   = 0    
        self.__set_v   = "0"
        self.__set_i   = "0"
        self.__set_p   = "0"

    # Method to connect over the network
    def connect(self):
        
        # Ping the loadbank first to see if it is there
        if os.system("ping -c 1 -w 2 " + self.__HOST + " > /dev/null 2>&1"):
            print("Failed to detect a loadbank on network")
            return 0
        print("Loadbank found! Connecting...")

        # Connect using telnet
        self._tn = self._connect(self.__HOST, self.__PORT, self.__password)

        if not self._tn:
            print("Failed to connect to the loadbank, check password?")
            return 0

        # Get safety limits
        self.__set_v = self._get(self._tn, self.__CONSTANT_VOLTAGE_COMMAND).split()[0]
        self.__set_i = self._get(self._tn, self.__CONSTANT_CURRENT_COMMAND).split()[0]
        self.__set_p = self._get(self._tn, self.__CONSTANT_POWER_COMMAND).split()[0]

        # Get current mode
        self.mode = self._get(self._tn, self.__MODE_COMMAND)

        # Everything working, return 1
        return 1


    # Method to connect over Telnet
    @classmethod
    def _connect(cls, HOST, PORT, password):
        
        # Initiate connection
        tn = telnetlib.Telnet(HOST, PORT)
        
        # If we have a password...
        if password:
            
            # Wait for the loadbank to ask us for a password
            tn.read_until(b"Password ? ")
            
            # Write the password to the Loadbank
            tn.write(password.encode('ascii') + b"\r\n")
            
        # Clear the buffer
        cls._flush(tn)  # Flush read buffer (needed)
        
        # Return the Telnet handle
        print('\nLoadbank connected!\n')
        return tn

    # Method to close down the connection
    def shutdown(self):
        time.sleep(0.4)
        self.load = False
        self.zero()
        self._tn.close()
        return 1

    # Method to zero the Loadbank
    def zero(self):
        time.sleep(0.4)
        if "VOLTAGE" in self.mode:
            self.voltage_constant = '0.0'
        elif "CURRENT" in self.mode:
            self.current_constant = '0.0'
        elif "POWER" in self.mode:
            self.power_constant = '0.0'

    # Method to clear the buffer
    @staticmethod
    def _flush(tn):
        tn.read_very_eager()  # Flush read buffer

    # Method to set a value
    @classmethod
    def _set(cls, tn, command, value):
        
        # Build the command in the correct format
        buf = (command + ' ' + value + '\r')
        
        # Send the command over the network
        cls._send(tn, buf)

    # Method to get a string of text
    @classmethod
    def _get(cls, tn, command):
        
        # Queries end with a '?', append if necessary
        if not command.endswith('?'):
            command += '?'
            
        # Build the query in the correct format
        buf = (command + '\r')
        
        # Send the query over the network
        return str(cls._send(tn, buf))

    # Method to get a number **recursive**
    @classmethod
    def _get_float(cls, tn, command):
        
        # Get the raw data string
        data = cls._get(tn, command)
        
        # Look for a valid reply
        try:
            return float(data.split()[0])
            
        # No valid reply so run the method again
        except ValueError:
            return cls._get_float(tn, command) # **recursivity**

    # Method to handle data 2way telnet datastream
    @classmethod
    def _send(cls, tn, inbuf):
        
        # Flush the buffer
        cls._flush(tn)
        
        # Create some memory
        outbuf = ""

        # Send the query or command to the Loadbank
        tn.write(inbuf.encode('ascii'))

        # Was it a query? If so what is the expected reply?
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

            # Check if the Loadbank acknowledged the query
            while not outbuf or outbuf.isspace():
                
                # Look for the expected reply or timeout
                outbuf = tn.read_until(expected, 0.1)  # Timeout = 0.1sec TODO
                
                # Decode the reply
                outbuf = outbuf.decode('ascii').strip('\r\n')
                
                # If the reply is not what we expected...
                if not outbuf or outbuf.isspace():
                    # Flush the buffer
                    cls._flush(tn)
                    
                    # Send the query again
                    tn.write(inbuf.encode('ascii'))

            # Return the query reply
            return outbuf
            
        # Was a command not a query, no reply expected.
        else:
            return inbuf

    # Property - Is the load on or off?
    @property
    def load(self):
        
        # Query the Loadbank
        state = self._get(self._tn, self.__LOAD_COMMAND)
        
        # Return the answer in boolean
        if "on" in state:
            return True
        elif "off" in state:
            return False
        else:
            return "UNKNOWN STATE"

    # Property - Set the Loadbank on or off
    @load.setter
    def load(self, state):
        if state:
            self._set(self._tn, self.__LOAD_COMMAND, "on")
        else:
            self._set(self._tn, self.__LOAD_COMMAND, "off")

    # Property - What is the Loadbank sensitivity range (see Loadbank manual)
    @property
    def range(self):
        return self._get(self._tn, self.__RANGE_COMMAND)

    # Property - Set a new range
    @range.setter
    def range(self, setting):
        
        # Sanity check that the request is a number 0-9
        if int(setting) in range(1,10):
            self._set(self._tn, self.__RANGE_COMMAND, setting)
            print('Set new rng ' + self.range)
        else:
            raise ValueError

    # Property - What is the current Loadbank mode
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

    # Property - Set new Loadbank mode
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

    # Update electrical data
    def update(self):
        self.__voltage = self._get_float(self._tn, self.__VOLTAGE_COMMAND)
        self.__current = self._get_float(self._tn, self.__CURRENT_COMMAND)
        self.__power   = self._get_float(self._tn, self.__POWER_COMMAND)


    # Property - What is the voltage?
    @property
    def voltage(self):
        return self.__voltage

    # Property - What is the voltage setpoint
    @property
    def voltage_constant(self):
        return self.__set_v

    # Propert - Set a new voltage setpoint
    @voltage_constant.setter
    def voltage_constant(self, volts):
        self._set(self._tn, self.__CONSTANT_VOLTAGE_COMMAND, volts)
        self.__set_v = volts

    # Property - What is the maximum voltage limit?
    @property
    def voltage_limit(self):
        return self._get_float(self._tn, self.__VOLTAGE_LIMIT_COMMAND)

    # Property - Set a new maximum voltage limit
    @voltage_limit.setter
    def voltage_limit(self, volts):
        self._set(self._tn, self.__VOLTAGE_LIMIT_COMMAND, volts)

    # Property - What is the mimimum voltage limit?
    @property
    def voltage_minimum(self):
        return self._get_float(self._tn, self.__VOLTAGE_MINIMUM_COMMAND)

    # Property - Set a new minimum voltage limit
    @voltage_minimum.setter
    def voltage_minimum(self, volts):
        self._set(self._tn, self.__VOLTAGE_MINIMUM_COMMAND, volts)


    # Property - What is the current?
    @property
    def current(self):
        return self.__current

    # Property - What is the current setpoint?
    @property
    def current_constant(self):
        return self.__set_i

    # Property - Set a new current setpoint
    @current_constant.setter
    def current_constant(self, amps):
        self._set(self._tn, self.__CONSTANT_CURRENT_COMMAND, amps)
        self.__set_i = amps
 
    # Property - What is the maximum current limit?
    @property
    def current_limit(self):
        return self._get_float(self._tn, self.__CURRENT_LIMIT_COMMAND)

    # Property - Set a new maximum current limit?
    @current_limit.setter
    def current_limit(self, amps):
        self._set(self._tn, self.__CURRENT_LIMIT_COMMAND, amps)


    # Property - What is the power?
    @property
    def power(self):
        return self.__power

    # Property - What is the power setpoint?
    @property
    def power_constant(self):
        return self.__set_p

    # Property - Set a new power setpoint?
    @power_constant.setter
    def power_constant(self, watts):
        self._set(self._tn, self.__CONSTANT_POWER_COMMAND, watts)
        self.__set_p = watts

    # Property - What is the maximum power limit?
    @property
    def power_limit(self):
        return self._get_float(self._tn, self.__POWER_LIMIT_COMMAND)

    # Property - Set a new maximum power limit?
    @power_limit.setter
    def power_limit(self, watts):
        self._set(self._tn, self.__POWER_LIMIT_COMMAND, watts)
