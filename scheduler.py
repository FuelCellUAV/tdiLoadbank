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
import time, csv
from loadbank import TdiLoadbank

class PowerScheduler(TdiLoadbank):
    def __init__(self, filename, HOST, PORT=23, password=''):
        super().__init__(HOST, PORT, password)
        self.filename = filename
        self.lineRegister = self.getLinePositions(filename)
        self.linePointer = -1
        self.startTime = time.time()
    
    @staticmethod
    def getLinePositions(filename):
        # Get the start points of each line/row in the file
        print('\nReading flight profile data...', end='...')
        file = open(filename)
        lineRegister = [0]
        thisLine = 1
        data = ' '
        while data:
            data = file.readline()
            thisLine = file.tell()
            if thisLine>0: lineRegister.append(thisLine)
        print('done!')
        return lineRegister

    def getLine(self, lineRequired=1):
        # Get last/current/next line (default = next line)
        file=open(self.filename)
        self.linePointer += lineRequired
        if self.linePointer < 0: self.linePointer = 0
        file.seek(self.lineRegister[self.linePointer])
        data = file.readline()
        file.close()
        return self.decodeLine(data)

    # Decode line from list of strings to list of floats
    @staticmethod
    def decodeLine(line): return list(map(float, line.split(',')))

    # Find this time entry
    def findNow(self):
        psuedoTime = time.time() - self.startTime

        try:
            while self.getLine(1)[0] < psuedoTime: pass # Check next line
        except (IndexError, ValueError):
#            print('End of Test')
            return -1 # End of test
        return self.getLine(-1)[1] # Set pointer to the line before

    def main(self):
        setpoint = 0
        setpointLast = 0
        input('Press any key to start')
        self.startTime=time.time()
        self.load('on')
        file = open((self.filename.split('.')[0] + 'Results' + time.strftime('%y%m%d%H%M%S') + '.txt'),'w')
        while setpoint >= 0:
            setpoint = self.findNow()
            if setpoint != setpointLast and setpoint >=0:
                setpointLast = setpoint
                self.constantCurrent(str(setpoint))
                ci = self.constantCurrent()
                voltage = self.voltage()
                current = self.current()
                power = self.power()
                print(ci, end='\t')
                print(voltage, end='\t')
                print(current, end='\t')
                print(power, end='\n')
                file.write(str(time.time()) + '\t')
                file.write(str(ci) + '\t')
                file.write(str(voltage) + '\t')
                file.write(str(current) + '\t')
                file.write(str(power) + '\n')
        print('End of test.')
        self.load('off')
        file.close()
