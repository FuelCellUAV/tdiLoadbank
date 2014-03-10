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
import time
import getpass
import telnetlib


class TdiLoadbank():
    def __init__(self, HOST, PORT=23, password=''):
        self.HOST = HOST
        self.PORT = PORT
        self.password = password
        self.tn = self.connect(HOST, PORT, password)

    @staticmethod
    def connect(HOST, PORT, password):
        tn = telnetlib.Telnet(HOST, PORT)
        if password:
            tn.read_until(b"Password ? ")
            tn.write(password.encode('ascii') + b"\r\n")
        return tn

    @staticmethod
    def get(tn, command):
        tn.read_until(b"\r",0.1) # Flush read buffer
        tn.write(command)
        data = tn.read_until(b"\r",0.1) # Timeout = 0.1sec
        data = data.decode('ascii')
        if data.isspace() or not data:
            # print('Got only whitespace, reading again')
            data = TdiLoadbank.get(tn, command) # RECURSIVE #
        data = data.strip('\r\n')
        return data

    def getVolts(self):
        voltsString = self.get(self.tn, b"v?\r")
        return float(voltsString.split(' ')[0])

    def getAmps(self):
        ampsString = self.get(self.tn, b"i?\r")
        return float(ampsString.split(' ')[0])

    def getMode(self):
        modeString = self.get(self.tn, b"mode?\r")
        return modeString

    def getThis(self, query):
        self.tn.write(query + b"\n")
        time.sleep(1)
        data = self.tn.read_some()
        print('data = ' + data.decode('ascii'))
        return data.decode('ascii') # Timeout = 1sec

#if __name__ == "__main__":
#    load = TdiLoadbank('158.125.152.225',port=10001,password='fuelcell'
    
