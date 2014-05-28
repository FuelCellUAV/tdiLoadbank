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
        self.__filename = filename
        self.__line_register = self._get_line_positions(filename)
#        print(self.__line_register)
        self.__line_pointer = -1
        self.__start_time = time.time()
        self.__out = out
        self.__running = 0
        self.__setpoint = 0
        self.__setpoint_last = -1

    @staticmethod
    def _get_line_positions(filename):
        # Get the start points of each line/row in the file
        print('\nReading flight profile data...', end='...')
        with open(filename) as file:
            line_register = [0]
            data = ' '
            while data:
                data = file.readline()
                this_line = file.tell()
                if this_line >= 0 and this_line != line_register[-1]:
                    line_register.append(this_line)
            print('...done!\n')
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
#        print(line)
        line = line.lstrip()
#        print(line)
        line = "\t".join(line.split())
        #line = line.replace(' ','\t')
#        print(line)
        line = line.split('\t')
#        print(line)
        line = map(float,line)
#        print(line)
        line = list(line)
#        print(line)
        return line
#        return list(map(float, line.replace(',', '\t').split('\t')))

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

    @property
    def running(self):
        return self.__running

    @running.setter
    def running(self, state):
        if state and not self.__running:
            self._start()
        elif not state and self.__running:
            self._stop()

    def _start(self):
        # Turn on
        print("Firing up the engines...")
        self.__start_time = time.time()
        self.current_constant = '0'
        self.load = True
        self.__log = open(('/media/usb0/'
                           + time.strftime('%y%m%d-%H%M%S')
                           + '-profile-' + self.__out + '.tsv'), 'w')
        self.__running = 1
        print("Chocks away!")

    def _stop(self):
        # Turn off
        print("Landing...")
        self.current_constant = '0'
        self.load = False
        self.__log.close()
        self.__running = 0
        print("Back in hangar!\n")

    def _run(self):
        if self.__running:
            if self.__setpoint >= 0:
                setpoint = self._find_now()
                if setpoint >= 0:
                    if setpoint != self.__setpoint:
                        self.power_constant = str(setpoint)
#                        self.current_constant = str(setpoint)
                        self.__setpoint = setpoint
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def run(self):
        # Do more running
        self.running = self._run()

        if self.__running:
            self.__log.write(str(time.time()) + '\t')
            self.__log.write(str(self.current_constant) + '\t')
            self.__log.write(str(self.voltage) + '\t')
            self.__log.write(str(self.current) + '\t')
            self.__log.write(str(self.power) + '\n')
