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
    def __init__(self, filename, HOST, PORT=23, password=''):
        super().__init__(HOST, PORT, password)
        self.__filename = filename
        self.__line_register = self._get_line_positions(filename)
        self.__line_pointer = -1
        self.__start_time = time.time()

    @staticmethod
    def _get_line_positions(filename):
        # Get the start points of each line/row in the file
        print('\nReading flight profile data...', end='...')
        with open(filename) as file:
            line_register = [0]
            data = ''
            while data:
                data = file.readline()
                this_line = file.tell()
                if this_line >= 0 and this_line != line_register[-1]:
                    line_register.append(this_line)
            print('...done!')
            return line_register

    def _get_line(self, line_required=1):
        # Get last/current/next line (default = next line)
        with open(self.__filename) as file:
            self.__line_pointer += line_required
            if self.__line_pointer < 0:
                self.__line_pointer = 0
            file.seek(self.__line_register[self.__line_pointer])
            line = file.readline()
        return self._decode_line(line)

    # Decode line from list of strings to list of floats
    @staticmethod
    def _decode_line(line):
        return list(map(float, line.replace(',', '\t').split('\t')))

    # Find this time entry
    def _find_now(self):
        psuedo_time = time.time() - self.__start_time
        try:
            while self._get_line(1)[0] < psuedo_time:
                pass  # Check next line
        except (IndexError, ValueError):
            #            print('End of Test')
            self.__line_pointer = -1
            return -1  # End of test
        return self._get_line(-1)[1]  # Set pointer to the line before

    def main(self):
        setpoint = 0
        setpoint_last = -1
        input('Press any key to start')
        self.__start_time = time.time()
        self.load('on')
        with open((self.__filename.split('.')[0] + 'Results-' + time.strftime('%y%m%d-%H%M%S') + '.txt'), 'w') as file:
            while setpoint >= 0:
                setpoint = self._find_now()
                if setpoint != setpoint_last and setpoint >= 0:
                    setpoint_last = setpoint
                    self.current_constant = str(setpoint)
                ci = self.current_constant
                voltage = self.voltage
                current = self.current
                power = self.power
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
