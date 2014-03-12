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
    
    @staticmethod
    def getData(file):
        data = [[0,0]]
        with open(file) as tsv:
            for line in csv.reader(tsv, delimiter='\t'):
                data = data + [[int(line[0]), int(line[1])]]
            tsv.close()
        return data        
         

    def main(self):
        # open file
        # read time & compare with now
        # export power to loadbank
        print(self.getData(self.filename))
