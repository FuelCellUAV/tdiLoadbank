#!/usr/bin/python3

# Power demand scheduler for a loadbank

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

# Import libraries
import time
from .loadbank import TdiLoadbank

class PowerScheduler(TdiLoadbank):
    def __init__(self, filename, out, HOST, PORT=23, password=''):
        super().__init__(HOST, PORT, password)
        self.filename = filename
        self.out = out
        self.lineRegister = self.getLinePositions(filename)
        self.linePointer = -1
        self.startTime = time.time()
        self._setpoint = 0
        self._setpointLast = -1
        self._running = 0
    
    @staticmethod
    def getLinePositions(filename):
        # Get the start points of each line/row in the file
        print('\nReading flight profile data...', end='...')
        with open(filename) as file:
            lineRegister = [0]
            thisLine = 1
            data = ' '
            while data:
                data = file.readline()
                thisLine = file.tell()
                if thisLine>=0 and thisLine!=lineRegister[-1]: lineRegister.append(thisLine)
            print('done!')
            return lineRegister

    def getLine(self, lineRequired=1):
        # Get last/current/next line (default = next line)
        with open(self.filename) as file:
            self.linePointer += lineRequired
            if self.linePointer < 0: self.linePointer = 0
            file.seek(self.lineRegister[self.linePointer])
            data = file.readline()
        return self.decodeLine(data)

    # Decode line from list of strings to list of floats
    @staticmethod
    def decodeLine(line): return list(map(float, line.replace(',','\t').split('\t')))

    # Find this time entry
    def findNow(self):
        psuedoTime = time.time() - self.startTime
        try:
            while self.getLine(1)[0] < psuedoTime: pass # Check next line
        except (IndexError, ValueError):
#            print('End of Test')
            self.linePointer = -1
            return -1 # End of test
        return self.getLine(-1)[1] # Set pointer to the line before

    def _start(self):
        self.startTime = time.time()
        self._running = 1
        self.load('on')
        self._log = open(('/media/usb0/' + time.strftime('%y%m%d-%H%M%S') + '-profile-' + self.out + '.tsv'),'w')
    def _stop(self):
        print("Flight finished!\n")
        self._running = 0
        self.load('off')
        self._log.close()

    def _run(self):
        if self._setpoint >= 0:
            setpoint = self.findNow()
            if setpoint >= 0:
                if setpoint != self._setpoint:
                    self.constantCurrent(str(setpoint))
                    self._setpoint = setpoint
                return 1
            else: return 0
        else:
            return 0

    def main(self, running):
#        input('Press any key to start')
        if running:
            if not self._running:
                print("Starting")
                self._start()
                print("Flying!")
            # Do running
            running = self._run()

            ci = self.constantCurrent()
            voltage = self.voltage()
            current = self.current()
            power = self.power()

            self._log.write(str(time.time()) + '\t')
            self._log.write(str(ci) + '\t')
            self._log.write(str(voltage) + '\t')
            self._log.write(str(current) + '\t')
            self._log.write(str(power) + '\n')

        if not running and self._running:
            print("Stopping")
            self._stop()
        return self._running  
