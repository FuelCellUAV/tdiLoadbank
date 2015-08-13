#!/usr/bin/python3

# TDI Loadbank Controller

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
#############################################################################

## Required imports
import sys, os, time, argparse, select
import loadbank, scheduler


## Function to print the header
def _display_header(destination):
    header = ("\n\n\n"
              + "TDI Loadbank Controller \n"
              + "(c) Simon Howroyd 2015 \n"
              + "Loughborough University \n"
              + "\n"
              + "This program is distributed in the hope that it will be useful, \n"
              + "but WITHOUT ANY WARRANTY; without even the implied warranty of \n"
              + "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the \n"
              + "GNU General Public License for more details. \n\n"
              + str(time.asctime())
              + "\n\n")

    # Write the data to destination
    _writer(destination, header),

    # Return the data
    return header


## Inspect user input arguments
def _parse_commandline():
    # Define the parser
    parser = argparse.ArgumentParser(description='TDi Loadbank Controller by Simon Howroyd 2015')
    
    # Define aguments
    parser.add_argument('--out', type=str, default='', help='Save my data to USB stick')
    parser.add_argument('--verbose', default=False, action='store_true', help='Print log to screen')
    parser.add_argument('--profile', type=str, default='', help='Name of flight profile file')
    parser.add_argument('--auto', default=False, action='store_true', help='Auto voltage hold')

    # Return what was argued
    return parser.parse_args()


## Function to read user input while running (stdin)
def _reader():
    # Get data from screen
    __inputlist = [sys.stdin]

    # Parse the typed in characters
    while __inputlist:
        __ready = select.select(__inputlist, [], [], 0.001)[0]

        # If no data has been typed then return blank
        if not __ready:
            return ''
            
        # Otherwise parse line
        else:
            # Read the line
            for __file in __ready:
                __line = __file.readline()

            # If there is nothing it is the end of the line
            if not __line:
               __inputlist.remove(__file)
               
            # Otherwise return line with no whitespace and all letters in lowercase
            elif __line.rstrip():  # optional: skipping empty lines
                return __line.lower().strip()
                
    # If we get here something went wrong so return blank
    return ''


## Function to write list data
def _writer(function, data):
    if type(data) is float:
        try:
            function("{0:.1f}".format(data) + '\t', end='')
        except (ValueError, TypeError):  # Not a print function
            function(str(data) + '\t')
    else: # Assume type(data) is str:
        try:
            function(data + '\t', end='')
        except (ValueError, TypeError):  # Not a print function
            function(str(data) + '\t')

    return data

#############################################################################
## Voltage controller
def _voltage_controller(v_now, v_set, i_now):
    controller_current = 0

    ## Voltage hold controller
    # Tweak towards setpoint
    if v_now < (v_set - 0.01):
        controller_current = i_now - 0.001
    elif v_now > (v_set + 0.01):
        controller_current = i_now + 0.001

    # Stop negative values
    if controller_current < 0.0: controller_current = 0.0
   
    return controller_current


## Function to print command list to screen
def _print_help(destination):
    help_text = ["\nHere is a list of available commands. There may be more!\n",
                 "\n",
                 "Time:\n",
                 "\t'time?'         [epoch since_start]s\n",
                 "\n",
                 "Electric data output:\n",
                 "\t'python3 main.py --verbose'\n",
                 "\t'python3 main.py --out your_filename_tag'\n",
                 "\t'v?'            [voltage]V\n",
                 "\t'i?'            [current]A\n",
                 "\t'p?'            [power]W\n",
                 "\t'elec?'         [mode setpoint voltage current power]\n",
                 "\n",
                 "Loadbank control:\n",
                 "\t'v 1.5'         [set 1.5V]\n",
                 "\t'i 2.0'         [set 2.0A]\n",
                 "\t'load on'\n",
                 "\t'load off'\n",
                 "\t'auto?'         [voltage controller state]\n",
                 "\t'auto on'       [turn voltage controller on]\n",
                 "\t'auto off'      [turn voltage controller off]\n",
                 "\n",
                 "Profile scheduler:\n",
                 "\t'python3 main.py --profile filename_on_usb_stick.txt'\n",
                 "\t'profile?'      [profile state]]\n",
                 "\t'profile on'    [start profile]\n",
                 "\t'profile pause' [pause profile]\n",
                 "\t'profile off'   [stop  profile]\n",
                 "\n",
                 "*run commands can be stacked, eg:\n",
                 "\tpython3 main.py --verbose --out test1 --profile my_profile.txt\n\n"]

    # Write the data to destination
    for cell in help_text:
        _writer(destination, cell)

    # Return the text
    return help_text


## Function to print the time
def _print_time(timeStart, destination, verbose=False):
    # Get the time data
    if verbose:
        delta = [
            "Epoch:",    time.time(),
            "Duration:", time.time() - timeStart,
        ]
    else:
        delta = [
            time.time(),
            time.time() - timeStart,
        ]

    # Write the data to destination
    for cell in delta:
        _writer(destination, cell)

    # Return the data
    return delta


## Function to print the electrical data
def _print_electric(load, destination, verbose=False):
    # If there is a digital loadbank connected get that data
    if load:
        if verbose:
            mode_code = load.mode.split()[0] + '\t' + load.mode.split()[1]

            # Add the load data to the controller data
            electric = ["Mode:",  mode_code,
                        "V_load:", load.voltage,
                        "I_load:", load.current,
                        "P_load:", load.power]
        else:
            # Convert mode to a code for Matlab compatibility
            if "CURRENT" in load.mode:
                mode_code = "1\t" + load.mode.split()[1]
            elif "VOLTAGE" in load.mode:
                mode_code = "2\t" + load.mode.split()[1]
            elif "POWER" in load.mode:
                mode_code = "3\t" + load.mode.split()[1]
            else:
                mode_code = "999\t999"

            # Add the load data to the controller data
            electric = [mode_code,
                        load.voltage,
                        load.current,
                        load.power]
    
    # Write the data to destination
    for cell in electric:
        _writer(destination, cell)

    # Return the data
    return electric


## Function to print the voltage data
def _print_voltage(load, destination, verbose=False):
    # If there is a digital loadbank connected get that data
    if load:
        if verbose:
            # Add the load data to the controller data
            voltage = ["V_load:", load.voltage]
        else:
            voltage = load.voltage 
    
    # Write the data to destination
    for cell in voltage:
        _writer(destination, cell)

    # Return the data
    return voltage


## Function to print the current data
def _print_current(load, destination, verbose=False):
    # If there is a digital loadbank connected get that data
    if load:
        if verbose:
            # Add the load data to the controller data
            current = ["I_load:", load.current]
        else:
            current = load.current
    
    # Write the data to destination
    for cell in current:
        _writer(destination, cell)

    # Return the data
    return current


## Function to print the power data
def _print_power(load, destination, verbose=False):
    # If there is a digital loadbank connected get that data
    if load:
        if verbose:
            # Add the load data to the controller data
            power = ["P_load:", load.power]
        else:
            power = load.power
    
    # Write the data to destination
    for cell in power:
        _writer(destination, cell)

    # Return the data
    return power


## Shutdown routine        
def _shutdown(load, log):
    try:
        print("\nShutting down...")

        # Shutdown loadbank
        if load:
            print('...Loadbank disconnected')
            if load.shutdown(): print('Done\n')
        
        # Shutdown datalog
        if log:
            print('...Datalogger closed')
            if log.close(): print('Done\n')
        
    except KeyboardInterrupt:        
        if input("Force close? [y/n]: ") is "y":
            print("FORCED CLOSE. TURN OFF DEVICES MANUALLY!")
            return
        else:
            _shutdown(load, log) # RECURSION

    # End
    print('Programme successfully exited and closed down\n\n')

#############################################################################

## Main run function
if __name__ == "__main__":
    try:
        os.system('cls' if os.name == 'nt' else 'clear')

        _display_header(print)

        args = _parse_commandline()

        # Initialise Digital loadbank
        load = loadbank.TdiLoadbank('158.125.152.246', 10001, 'fuelcell')

        # If we cannot connect to the loadbank, quit
        if load.connect() == 0:
            raise SystemExit
        # Otherwise zero it and set safety limits
        else:
            print("Setting up loadbank...")
            mysleep = 0.4
            load.zero()
            time.sleep(mysleep)
            load.mode = "CURRENT"
            time.sleep(mysleep)
            load.range = "9" # 4
            time.sleep(mysleep)
            load.current_limit = "30.0" # 30.0
            time.sleep(mysleep)
            load.voltage_limit = "35.0" # 35.0
            time.sleep(mysleep)
            load.voltage_minimum = "0.01"#"1.2" # 5.0

        # Initialise profile scheduler if argued
        if args.profile:
            profile = scheduler.Scheduler("/media/usb/" + args.profile)
            
            # If a loadbank is connected then define this as the output
            if load:
                output = "loadbank"
            # Otherwise error
            else:
                raise SystemExit               
        # Otherwise make the variable blank
        else:
            profile = ''

        # If user asked for a logfile then open this
        if args.out:
            log = open(("/media/usb/" + time.strftime("%y%m%d-%H%M%S") + "-controller-" + args.out + ".tsv"), 'w')
        # Otherwise open nothing to prevent errors
        else:
            log = open("/dev/null", 'w')

        timeStart = time.time()

        # Display a list of available user commands
        print("\n\nType command:\n"
            + "add ? to query or space then setpoint \n"
            + "**Type 'help' for a full list**\n\n")

        flag = False
        auto_voltage = 0.0


        ### Main loop ###
        while True:
            # Handle the loadbank
            if load:
                load.update()


            ## Handle the voltage controller
            if args.auto:
                if not flag:
                    time.sleep(1)
                    auto_voltage = load.voltage
                    print("Set voltage hold to " + str(auto_voltage) +"V")
                    load.load = True
                    flag = True
                else:
                    if load.load:  
                        load.current_constant = str(_voltage_controller(load.voltage, auto_voltage, float(load.current_constant)))
            else:
                if flag:
                    load.load = False
                    load.zero()
                    flag = False


            ## Handle the profile
            if profile:
                try:
                    # Running
                    if profile.state is 1:
                        # Check if just [re]started
                        if profile.state_last is not 1:
                            print("Turning loadbank on")
                            load.load = True

                        # Get the programmed setpoint
                        setpoint = profile.run()

                        # and the setpoint is not in an error mode...
                        if setpoint >= 0:
                            
                            # Set the type of electrical profile we are running
                            mode = load.mode
                            
                            # Set the setpoint for the electrical profile for now
                            if args.auto:
                                auto_voltage = float(setpoint)
                            elif "VOLTAGE" in mode:
                                load.voltage_constant = str(setpoint)
                            elif "CURRENT" in mode:
                                load.current_constant = str(setpoint)
                            elif "POWER" in mode:
                                load.power_constant = str(setpoint)

                    # Paused
                    elif profile.state is 2:
                        if profile.state_last is 1:
                            load.load = False
                            load.zero()
                            args.auto = False
                        pass
                    # Stopped
                    else:
                        if profile.state_last in (1, 2):
                            load.load = False
                            load.zero()
                            args.auto = False
                    
                except AttributeError:
                    print("No profile loaded. Restart the programme with --profile filename.txt")
                    break


            ## Handle the logfile
            # Log time
            _print_time(timeStart, log.write)
        
            # Log electrical data
            electric = _print_electric(load, log.write)
                
            # Log a new line, end of this timestep
            if log:
                log.write("\n")
        
            # If verbose is argued then print all data to screen
            if args.verbose and not args.timer:
                _print_time(timeStart, print)
                _print_electric(load, print)
                print()


            ## Handle the user interface
            # Read typed in user data on the screen
            request = _reader()

            # If something was typed in...
            if request:
                    
                # Split the argument from the value
                request = request.split(' ')
                    
                # Determine the number of pieces of information
                req_len = len(request)
                    
                # Strip away any whitespace
                for x in range(req_len):
                    request[x] = request[x].strip()
        
                # If only one piece of information, it is a request for data
                if req_len is 1:
                    if request[0].startswith("help"):
                        _print_help(print)
                    elif request[0].startswith("time?"):
                        _print_time(timeStart, print, True)
                    elif request[0].startswith("elec?"):
                        _print_electric(load, print, True)
                    elif request[0].startswith("v?"):
                        _print_voltage(load, print, True)
                    elif request[0].startswith("i?"):
                        _print_current(load, print, True)
                    elif request[0].startswith("p?"):
                        _print_power(load, print, True)
                    elif request[0].startswith("auto?"):
                        print("Voltage controller set to " + str(auto_voltage) + "V")
                    elif request[0].startswith("profile?"):
                        if profile and profile.state is 1:
                            print("Profile running")
                        elif profile and profile.state is 2:
                            print("Profile paused")
                        else:
                            print("Profile stopped")
        
                # If there are two pieces of information it is a command to change something
                elif req_len is 2:
                    if request[0].startswith("profile"):
                        if not profile: print("No profile loaded. Restart the programme with --profile filename.txt")
                        elif request[1].startswith("on"):
                            profile.state = 1
                        elif request[1].startswith("pause"):
                            profile.state = 2
                        elif request[1].startswith("off"):
                            profile.state = 0
                        else:
                            print("Unknown command '" + request[1] + "', try [on, pause, off]")
                    elif request[0].startswith("auto"):
                        if request[1].startswith("on"):
                            args.auto = True
                            auto_voltage = load.voltage
                        else:
                            args.auto = False
                    elif request[0].startswith("i"):
                        load.current_constant = str(request[1])
                    elif request[0].startswith("v"):
                        if "VOLTAGE" in load.mode:
                            load.voltage_constant = str(request[1])
                        else:
                            auto_voltage = float(request[1])
                    elif request[0].startswith("load"):
                        if request[1].startswith("on"):
                            load.load = True
                        else:
                            load.load = False
        
                # Print a new line to the screen
                print()

    except (SystemExit, KeyboardInterrupt):
        print("Shutting down programme")
        try: _shutdown(load, log)
        except NameError: pass
        sys.exit()

    #######
    # End #
    #######
