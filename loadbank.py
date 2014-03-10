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


# Includes
import telnetlib


class TdiLoadbank():
    def __init__(self, HOST, PORT=23, password=''):
        self.HOST = HOST
        self.PORT = PORT # Default 23 if not specified
        self.password = password # Default blank if not specified
        self.tn = self.__connect(HOST, PORT, password)

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
        tn.read_until(b"\r", 0.1) # Flush read buffer (needed)
        if value:
            # Send new setting
            tn.write((command + ' ' + value + '\r').encode('ascii'))
        # Request data
        tn.write((command + '?\r').encode('ascii'))
        # Receive data
        data = tn.read_until(b"\r", 0.1) # Timeout = 0.1sec
        data = data.decode('ascii')
        if data.isspace() or not data:
            # Redo if nothing received (needed)
            data = TdiLoadbank.__send(tn, command) # RECURSIVE #
        data = data.strip('\r\n')
        return data

    # Random command
    def random(self, command, state=''):
        return self.__send(self.tn, command, state)

    # Load
    def load(self, state=''):
        return self.__send(self.tn, 'load', state).split(' ')[1]

    # Mode
    def mode(self):
        return self.__send(self.tn, 'mode')

    # Voltage
    def voltage(self):
        return float(self.__send(self.tn, 'v').split(' ')[0])
    def constantVoltage(self, value=''):
        return float(self.__send(self.tn, 'cv', value).split(' ')[0])
    def voltageLimit(self, value=''):
        return float(self.__send(self.tn, 'vl', value).split(' ')[0])
    def voltageMinimum(self, value=''):
        return float(self.__send(self.tn, 'uv', value).split(' ')[0])

    # Current
    def current(self):
        return float(self.__send(self.tn, 'i').split(' ')[0])
    def constantCurrent(self, value=''):
        return float(self.__send(self.tn, 'ci', value).split(' ')[0])
    def currentLimit(self, value=''):
        return float(self.__send(self.tn, 'il', value).split(' ')[0])

    # Power
    def power(self):
        return float(self.__send(self.tn, 'p').split(' ')[0])
    def constantPower(self, value=''):
        return float(self.__send(self.tn, 'cp', value).split(' ')[0])
    def powerLimit(self, value=''):
        return float(self.__send(self.tn, 'pl', value).split(' ')[0])
