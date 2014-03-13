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

class PowerScheduler():
    def __init__(self, filename):
        self.filename = filename
        self.lineRegister = self.getLinePositions(filename)
        self.linePointer = -1
    
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
        return data

    def main(self):
        # open file
        # read time & compare with now
        # export power to loadbank
        for i in (self.getLine(self.filename, self.lineRegister)):
            print(i)
