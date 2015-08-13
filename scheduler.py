#!/usr/bin/python3

# Power demand scheduler for a loadbank

# Copyright (C) 2015  Simon Howroyd
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

# Import libraries
import time, os.path


# Define class
class Scheduler():
    # Code to run when class is created
    def __init__(self, filename):
        self.__filename = filename
        if os.path.isfile(filename):
            self.__filename = filename
        else:
            print("\nInvalid profile filename\n")
            raise SystemExit
        self.__last_line = ''
        self.__this_line = ''
        self.__start_time = time.time()
        self.__running = 0
        self.__setpoint = 0
        self.__setpoint_last = -1
        self.__paused_time = 0.0
        self.__paused_at = 0.0
	
    # Method to read a line
    def _get_line(self, pointer=1):
        # If we want to re-read the last line...
        if pointer is -1:
            # Move the cursor backwards to the start of the last line
            self.__fid.seek( self.__fid.tell() - len(self.__this_line) )
            
        # Save our last line
        self.__last_line = self.__this_line
        
        # Update our current line
        self.__this_line = self.__fid.readline()

        # Return the line as single row of columns
        return list( map(float,self.__this_line.split()) )

    # Method to find the setpoint relative to system time
    def _find_now(self):
        # Calculate time since start of schedule
        psuedo_time = self._get_psuedo_time()
        
        # Check if the current setpoint has expired
        try:
            if list( map(float,self.__this_line.split()) )[0] > psuedo_time:
                # If it hasn't expired, return this setpoint
                return list( map(float,self.__this_line.split()) )[1]
                
        # If there is an IndexError it is the first record so ignore
        except (IndexError):
            pass
        
        # The current setpoint has expired so get the next one
        try:
           x = self._get_line()
           
           # Find the next non-expired setpoint
           while float(x[0]) < psuedo_time:
               x = self._get_line()
               pass  # Check next line
           
        # An exception of these types means end of test
        except (IndexError, ValueError):
            return -1
            
        # Return this new unexpired setpoint
        return x[1]

    # Property - Is the schedule currently running?
    @property
    def running(self):
        return self.__running

    # Property - Set the scheduler as running
    @running.setter
    def running(self, state):
        state = int(state)        
        # If we want to turn on and not already running...
        if state is 1 and not self.__running:
            self._start()
        # If we want to pause/unpause or user unpauses using state 1...
        elif (state is 2 and self.__running) or (state is 1 and self.__running is 2):
            self._pause()
        # If we want to turn off and not already off...
        elif not state and self.__running:
            self._stop()

    # Method to start the scheduler
    def _start(self):
        # Tell the user we are trying to start
        print("Firing up the engines...")
        
        # Open the profile file
        try:
            self.__fid = open(self.__filename)
        except IOError:
            print("Can't open profile file!")
            raise SystemExit
        
        # Set the schedule start time
        self.__start_time = time.time()
        
        # Put the setpoint to zero for safety
        self.__setpoint = 0
        
        # Set the class flag as running
        self.__running = 1
        
        # Tell the user we are now running
        print("Chocks away!")

    # Method to pause the profile
    def _pause(self):
        if self.__running is 2:
            self.__running = 1
            paused_for = time.time() - self.__paused_at - 0.00015 # [Crudely] Calibrated for average CPU time
            self.__paused_time = self.__paused_time + paused_for
            print("...unpaused after " + str(paused_for) + "s, continuing from " + str(self._get_psuedo_time()) + "s")
        elif self.__running is 1:
            self.__paused_at = time.time()
            self.__running = 2
            print("Paused at " + str(self._get_psuedo_time()) + "s,")
            print("Use 'profile pause' again to continue...")

    # Calculate psuedo time. Time since start not including pauses
    def _get_psuedo_time(self):
        return time.time() - self.__start_time - self.__paused_time

    # Method to stop the scheduler
    def _stop(self):
        # Tell the user we are trying to stop
        print("Landing...")
        
        # Set the class flag to stopped
        self.__running = 0
        
        # Close the profile file
        self.__fid.close()
        
        # Tell the user we have stopped running
        print("Back in hangar!\n")

    # Internal method to run the scheduler
    def _run(self):
        # Check if we are actually running
        if self.__running is 1:
            
            # Check the setpoint isn't in a safety error state (-1)
            if self.__setpoint >= 0:
                
                # Get the setpoint for this time
                setpoint = self._find_now()
                
                # If the setpoint isn't in a safety error state (-1)...
                if setpoint >= 0:
                    
                    # If the setpoint has changed since last time...
                    if setpoint != self.__setpoint:
                        
                        # Update the memory
                        self.__setpoint = setpoint
                        
                        # Return the new setpoint
                        return self.__setpoint
                    
                    # Otherwise return the old setpoint
                    else:
                        return self.__setpoint
                
                # Otherwise we are in error so return the error code -1
                else:
                    return -1
                    
            # Otherwise we are in error so return the error code -1
            else:
                return -1

        # Check if paused
        elif self.__running is 2:
#            self.__paused_time = self.__paused_time + (time.time() - self.__paused_at)
#            self.__paused_at = time.time() - 0.00003 # execution time
#            print("Paused " + str(self.__paused_time) + "s")
            return -1

        # Otherwise we are not running so return the error code -1
        else:
            return -1

    # Method to run the scheduler
    def run(self):
        # Run the internal method
        running = self._run()
        
        # If we are currenty running but we have hit the end of file or an error...
        if self.__running is 1 and running is -1:
            self._stop()

#        if self.__running is 2:
#            print("State is " + str(self.__running) + ".  Cumulative pause is " + str(self._get_psuedo_time()))
            
        # Return the run state
        return running
