4#!/usr/bin/python3

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
    def __init__(self, HOST, PORT=23, password=''):
        self.HOST = HOST
        self.PORT = PORT # Default 23 if not specified
        self.password = password # Default blank if not specified
        self.tn = self.__connect(HOST, PORT, password)
        self.tn.read_very_eager() # Flush read buffer (needed)

    # Telnet connect method
    @staticmethod
    def __connect(HOST, PORT, password):
        tn = telnetlib.Telnet(HOST, PORT)
        if password:
            tn.read_until(b"Password ? ")
            tn.write(password.encode('ascii') + b"\r\n")
        return tn

    # Method to handle data 2way telnet datastream
    @staticmethod
    def __send(tn, command, value=''):
        data = ""
        tn.read_very_eager() # Flush read buffer (needed)
        while not data or data.isspace():
            # If we are setting a variable
            if value:
                tn.write((command + ' ' + value + '\r').encode('ascii'))
#                print((command + ' ' + value + '\r').encode('ascii'))
                time.sleep(0.1)
                tn.read_very_eager() # Flush read buffer (needed)
            # Request data
            tn.write((command + '?\r').encode('ascii'))
#            print((command + '?\r').encode('ascii'))
            time.sleep(0.12)
            # Receive data
            data = tn.read_until(b"\r", 0.1) # Timeout = 0.1sec
            data = data.decode('ascii')
            data = data.strip('\r\n')
            tn.read_very_eager() # Flush read buffer (needed)

        return data

    @staticmethod
    def __get(request):
        success = False
        while success is False:
            try:
                result = request()
                success = True
            except (KeyboardInterrupt, SystemExit): raise
            except: pass
        return result
        

    # Random command
    def random(self, command, state=''):
        return self.__get(lambda: self.__send(self.tn, command, state))

    # Load
    def load(self, state=''):
        return self.__get(lambda: self.__send(self.tn, 'load', state).split(' ')[1])

    # Mode
    def mode(self):
        return self.__get(lambda: self.__send(self.tn, 'mode'))

    # Voltage
    def voltage(self):
        return self.__get(lambda: float(self.__send(self.tn, 'v').split(' ')[0]))
    def constantVoltage(self, value=''):
        return self.__get(lambda: float(self.__send(self.tn, 'cv', value).split(' ')[0]))
    def voltageLimit(self, value=''):
        return self.__get(lambda: float(self.__send(self.tn, 'vl', value).split(' ')[0]))
    def voltageMinimum(self, value=''):
        return self.__get(lambda: float(self.__send(self.tn, 'uv', value).split(' ')[0]))

    # Current
    def current(self):
        return self.__get(lambda: float(self.__send(self.tn, 'i').split(' ')[0]))
    def constantCurrent(self, value=''):
        return self.__get(lambda: float(self.__send(self.tn, 'ci', value).split(' ')[0]))
    def currentLimit(self, value=''):
        return self.__get(lambda: float(self.__send(self.tn, 'il', value).split(' ')[0]))

    # Power
    def power(self):
        return self.__get(lambda: float(self.__send(self.tn, 'p').split(' ')[0]))
    def constantPower(self, value=''):
        return self.__get(lambda: float(self.__send(self.tn, 'cp', value).split(' ')[0]))
    def powerLimit(self, value=''):
        return self.__get(lambda: float(self.__send(self.tn, 'pl', value).split(' ')[0]))
