#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 25 09:32:23 2025

@author: Graeme Hilton ghilton@fosina.fr
Script to analyse an events.db file from Mesh Central.
The purpose is to explore the data volume per user in order to assign "costs".

The events.db file MeshCentral is a file containing json formatted data.
Each line is a log entry. Some log entries contain a data in/out parameter.
Use -o, --output= to specify an output file
Use -m, --measurement= to specify the units (none (bytes), dec (1000 bytes per kilobyte, etc) or IEC (1024 bytes per kilobyte, etc))
Use -s, --since= and/or -b,--before=<yyyy-mm-dd> to specify a time span including since, excluding before. 24hr periods only.
Use -u and/or -a to limit the user and asset to report on.
Last on the command line, optionally use the -f parameter to specify one or more filenames, otherwise defaults to the normal location of the file (meshcentral-data/meshcentral-events.db).

   Copyright 2025 Graeme Hilton

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

"""

import json, sys, getopt, math
from datetime import datetime, timezone, timedelta
from pathlib import Path

def main(argv) :
    default_file = Path.home() / "meshcentral-data" / "meshcentral-events.db"
    
    default_byte_type='none'
    default_since=datetime(2000,1,1,tzinfo=timezone.utc) # All times/dates are using UTC timezone. If a time/date does not have a timezone it is assumed to be UTC.
    default_before=datetime.now(timezone.utc)
    default_period=1440
    output="console"
    time_formats=[ "%Y-%m-%dZ%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%H:%M:%S", "%H:%M","%Hh"]
    debug = 0
    usage =f"usage: {sys.argv[0]} [sbguamod|h] <filenames>...\n"
    usage+=f"  options:\n"
    usage+=f"-s, --since=, -b, --before= to restrict time span. Use ISO8601 formats for UTC yyyy-mm-ddZhh:mm:ss, hh:mm:ss, hh:mm or hh'h'.\n"
    usage+=f"-g, --granularity=<period> to specify a time period to aggregate.\n Valid values are 1, 2, 3, 4, 5, 6, 10, 15, 20, 30, 60, 120, 180, 240, 360, 720, 1440  1 minute to 1 day.\n"
    usage+=f"-u, --user the user to include in the report (defaults to all)\n"
    usage+=f"-a, --asset the asset to include in the report (defaults to all)\n"
    usage+=f"-m, --measurement units to use 'dec', 'IEC', 'none', defaults to {default_byte_type}\n"
    usage+=f"-o, --output=<filename> to specify an output file, otherwise output to the terminal\n"
    usage+=f"-d, --debug. Specify multiple times to increase level\n"
    usage+=f"-h, --help. Display this help. Use --help+ to get a list of known assets and users\n"
    usage+=f"<filenames> to analyse, defaults to\n    '{default_file}'\n"
    usage+=f"For example:\n"
    usage+=f"  {sys.argv[0]} -mdec --since=2025-08-01 meshcentral-events.db\n"
    usage+=f" to output log activity on and after the 1st of August 2025.\n"
    usage+=f"  {sys.argv[0]} -mdec --since=12h meshcentral-events.db\n"
    usage+=f" to output log activity since the previous midday.\n"
    try :
        from MeshCentral_data import nodeids # import a list of known assets and user ids and their aliases
        from MeshCentral_data import userids
    except :
                #    <nodeid> : <alias>
        nodeids = { "node//aabbccddeeffgghhiijjkkllmmnnooppqqrrssttuuvvwwxxyyzz001122334455" : "My Pi"}
                #    <username> : <alias>
        userids = { "admin" : "Administrator" }

    try :
        opts, args = getopt.getopt(argv,"f:s:b:g:u:a:o:m:dh",["filename=","since=","before=","granularity=","user=","asset=","output=","measurement=","debug","help","help+"])
    except getopt.GetoptError:
        print(usage)
        sys.exit(2)

    files = []
    byte_type=None
    since = None
    before = None
    temptime=None
    user = None
    asset = None
    period=None
    
    # put the debug parameters at the top of the list so they are processed first.
    for element in [('-d',''), ('--debug','')] :
        try: 
            i=0
            while (opts[(i+1):].index(element) > 0): # no debug flags beyond position i
                opts.pop(opts[(i+1):].index(element)+i+1)
                opts.insert(0,element)
                i+=1
        except : pass # no debug found.
        
    for opt, arg in opts :
        if opt in ("-d", "--debug") : # put this first to allow some debug output ahead of parameter checking.
            debug += 1
            if debug == 1 : # only on the first d option, no need to print it 3 times on ddd!
                print(f"Arguments: {argv}")
                print(f"Options  : {opts}")
                print(f"Args     : {args}")


        if opt in ("-f", "--filename") : # hidden option...
            files.append(arg)
        
        if opt in ("-m", "--measurement"):
            if arg in ['dec','IEC','none'] : byte_type = arg
            else :
                print(f"Unknown unit, default to {default_byte_type}")
                byte_type=default_byte_type

        if opt in ("-h", "--help") :
            print(usage)
            sys.exit(0)

        if opt in ("--help+") :
            print(usage)
            print("Create a file called MeshCentral_data.py and add")
            print(" nodeids = { \"<nodeid1>\" : \"friendly name 1\",\n             \"<nodeid2>\" : \"friendly name 2\"\n           }\nand")
            print(" userids = { \"<username1>\" : \"friendly name 1\",\n             \"<username2>\" : \"friendly name 2\"\n           }")
            print("to associate nodeids and usernames with friendly aliases")
            for id in nodeids : print (f"Asset: \"{nodeids[id]}\"")
            for id in userids : print (f"User: \"{userids[id]}\"")
            print(f"Valid date/time input formats are\n {time_formats}")
            sys.exit(0)

        if opt in ("-s","--since","-b","--before") :
            for template in time_formats : 
                try :
                    temptime=datetime.strptime(arg,template)
                    temptime=temptime.replace(tzinfo=timezone.utc)
                    if (temptime.year == 1900) and (temptime.month == 1) and (temptime.day == 1) : # we only have a time
                        temptime=temptime.replace(year=datetime.now(timezone.utc).year,month=datetime.now(timezone.utc).month,day=datetime.now(timezone.utc).day)
                        if temptime > datetime.now(timezone.utc):
                            if (opt in ("-s","--since")) :
                                temptime=temptime-timedelta(days=1) # if this is in the future, subtract a day
                                if debug > 0 :
                                    print(f"Assuming you meant a time yesterday.")
                            else : # default to default if before is in the future
                                temptime = default_before
                                if debug >0 : print(f"Before {arg} is in the future; setting to now.")
                    if debug >0 : print(f"setting {opt}={temptime} as {arg} matches template {template}")
                    break
                except ValueError : 
                    if debug > 0 : print(f"{template} did not match {arg}, next")
                except :
                    print(f"Other error while setting since or before. {opt}={arg}")
                    sys.exit(2)
            if temptime == None : # we've exhausted our templates
                print(f"{arg} is not a valid date/time. Use a valid format: {template} format.")
                sys.exit(2)
            if opt in ("-s","--since") : since=temptime
            if opt in ("-b","--before") : before=temptime


        # if opt in ("-b","--before") :
        #     try : before=datetime.strptime(arg,"%Y-%m-%dZ%H:%M:%S")
        #     except : 
        #         print(f"{arg} is not a valid date. Use yyyy-mm-ddZHH:MM:SS format.")
        #         sys.exit(2)
                
        if opt in ("-g", "--granularity") :
            valid_granularity=[1,   2,  3,  4,  5,  6, 10,     15, 20, 30,  
                               60,120,180,240,    360,    720, 1440]
            if int(arg) in valid_granularity : 
                period=int(arg)
            else :
                print(f"{arg} is not a valid period. Valid values are 1, 2, 3, 4, 5, 6, 10, 15, 20, 30, 60, 120, 180, 240, 360, 720, 1440. I.e. 1 minute to 1 day in useful increments. Default is {default_period} minutes.")
                sys.exit(2)
            
        if opt in ("-u","--user") :
            if arg in list(userids.values()) : user=arg
            else :
                print(f"\"{arg}\" is not a known user alias. Use --help+ to get a list of known users.")
                print(f"Continuing with user={arg} anyway.")
                user=arg
            
        if opt in ("-a","--asset") :
            if arg in list(nodeids.values()) : asset=arg
            else :
                print(f"\"{arg}\" is not a known asset name. Use --help+ to get a list\n")
                print(f"Asset names are matched to nodeids. These must be added to the data file for\n")
                print(f"proper recognition. If you don't specify an asset all assets are listed.")
                sys.exit(2)

        if opt in ("-o","--output") :
            output_filename=arg
            output="file"

    if len(args) > 0 : # there are filenames to add.
        for arg in args :
            if arg[0] == "-" : pass
            else : files.append(arg)
    if debug > 0 :
        print(f"units    : {byte_type}")


    if files == [] : files = [default_file]
    if byte_type == None : byte_type=default_byte_type
    if since == None  : since  = default_since
    if before == None : before = default_before
    if period == None : period = default_period
    
    ## Set some display variables
    if   byte_type=="dec" :
        byte_mult=1000
        SI_name= [ "byte", "kilobyte", "megabyte", "gigabyte", "terabyte","petabyte"]
        SI_unit= [ "B",    "kB",       "MB",       "GB",       "TB",      "PB",]
    elif byte_type=="IEC" :
        byte_mult = 1024
        SI_name= [ "byte", "kibibyte", "mebibyte", "gibibyte", "tebibyte","pebibyte"]
        SI_unit= [ "B",    "kiB",      "MiB",      "GiB",      "TiB",     "PiB"]
    elif byte_type=='none' :
        byte_mult = 0
        SI_name= [ "byte" ]
        SI_unit= [ "B" ]
    
    if period == 1440 :
        date_format="%Y-%m-%d"
    else :
        date_format="%Y-%m-%d %H:%M"



    user_data={}
    asset_data={}
    grand_total=0
    
    if debug > 2 : f=0 # file counter
    for file in files :
        if debug >2 :
            f+=1 # increment file counter (1-index)
            print(f"File #{f} = {file}")
        with open(file,"r") as fp :
            if debug > 2 : i=0 # line counter
            for fline in fp :
                line=json.loads(fline)
                if debug > 2 : i+=1 # increment line counter (1-index)
                if ('etype' in line) and (line['etype'] == 'relay' and (line['msgid'] in [9,10,12])) : # end of relay session
                    if debug > 2 : print(f"{f}-{i} : {line}") # File and line reference
                    timestamp=datetime.fromtimestamp((line['time']['$$date'])/1000,timezone.utc) # millisecond Unix timestamp, assume UTC
                    #date = timestamp.strftime('%Y-%m-%d')
                    if (timestamp <= since) or (timestamp > before) :
                        if debug > 2 :print(f"timestamp {timestamp.strftime('%Y-%m-%d %H:%M:%S')} is outside time range {since.strftime('%Y-%m-%d  %H:%M:%S')} to {before.strftime('%Y-%m-%d  %H:%M:%S')}")
                        pass
                    else:
                        
                        if (debug > 2) and (before != datetime.now(timezone.utc) or (since != default_since)) :
                            print(f"timestamp {timestamp.strftime('%Y-%m-%d  %H:%M:%S')} is inside time range {since.strftime('%Y-%m-%d  %H:%M:%S')} to {before.strftime('%Y-%m-%d  %H:%M:%S')}")
                        username = line['username']
                        assetname = line['ids'][2]
                        if username in userids: username = userids[username] # pretty name
                        if assetname in nodeids: assetname = nodeids[line['ids'][2]] # pretty name

                        if ((username == user) or (user == None)) and ((assetname == asset) or (asset == None)) :
                            data_total = line['bytesin'] + line['bytesout']
                            grand_total += data_total
                            # round down the date and convert to a string to use as a key.
                            date = round_date(timestamp,period).strftime(date_format)
                            if debug > 1 : print(f"granularity = {period}")
                            if debug > 1 :
                                print(f"{username}  : {timestamp.strftime('%Y-%m-%d %H:%M:%S')} : {data_total}")
                                print(f"{username}  : {date} : {user_data[username][date]} : overall {user_data[username]['overall']}")
                                print(f"{assetname} : {timestamp.strftime('%Y-%m-%d %H:%M:%S')} : {data_total}")
                                print(f"{assetname} : {date} : {asset_data[assetname][date]} : overall {asset_data[assetname]['overall']}")

                            if (username in user_data) and (date in user_data[username]) : # user and date exist
                                user_data[username].update({date : user_data[username][date]+data_total, 'overall' : data_total + user_data[username]['overall'] })
                            elif username in user_data : # user exists, but not date
                                user_data[username].update({date : data_total, 'overall': data_total + user_data[username]['overall']})
                            else : # neither user nor date exist
                                user_data.update({username : {date : data_total, 'overall': data_total}})
                                
                            if (assetname in asset_data) and (date in asset_data[assetname]) : # asset and date exist
                                asset_data[assetname].update({date : asset_data[assetname][date]+data_total, 'overall' : data_total + asset_data[assetname]['overall'] })
                            elif assetname in asset_data : # asset exists, but not date
                                asset_data[assetname].update({date : data_total, 'overall' : data_total + asset_data[assetname]['overall']})
                            else : # neither asset nor date exist
                                asset_data.update({assetname : {date : data_total, 'overall' : data_total}})
                            
                elif (('bytesin' in line) or ('bytesout' in line)) and (debug > 2) : print(f"####NOT COUNTED#### {f}-{i} : {line}") # catch any other data
                
    if output=="console" :
        f=None # no output, None forces print statement to stdout
    else :
        try : f=open(output_filename,"w")
        except :
            f=None
            print(f"Can't open file {output_filename}; using console output.")
    power = 0 # default power value, in case of byte_type='none'
    print("User Summary:",file=f)
    for user in sorted(user_data, key=lambda s: s.lower()) :
        user_total=user_data[user]['overall']
        if user_total == 0 :
            print(f"No data for {user}")
        else : 
            print(f" User = {user}",file=f)
            percentage = 100*user_total/grand_total
            for date in sorted(user_data[user]) :
                if date!='overall' :
                    data=user_data[user][date]
                    if byte_type != "none" : power=(int(math.log(data,byte_mult))) # get the magnitude
                    print(f"   {date} {100*data/user_total:.2f}% ({data/pow(byte_mult,power):.2f} {SI_unit[power]})",file=f)
            if byte_type != "none": power=(int(math.log(user_total,byte_mult))) # get the magnitude
            print(f" User Total = {percentage:.2f}% {user_total/pow(byte_mult,power):.2f} {SI_unit[power]}\n",file=f)

    print("Asset Summary:",file=f)
    for asset in sorted(asset_data, key=lambda s: s.lower()) :
        asset_total=asset_data[asset]['overall']
        if asset_total == 0 :
            print(f"No data for {asset}")
        else :
            print(f" Asset = {asset}",file=f)
            percentage = 100*asset_total/grand_total
            for date in sorted(asset_data[asset]) :
                if date!='overall' :
                    data=asset_data[asset][date]
                    if byte_type != "none" : power=(int(math.log(data,byte_mult))) # get the magnitude
                    print(f"   {date} {100*data/asset_total:.2f}% ({data/pow(byte_mult,power):.2f} {SI_unit[power]})",file=f)
            if byte_type != "none": power=(int(math.log(asset_total,byte_mult))) # get the magnitude
            print(f" Asset Total = {percentage:.2f}% {asset_total/pow(byte_mult,power):.2f} {SI_unit[power]}\n",file=f)

    if grand_total == 0 :
        if user != None : print(f"No data for {user}")
        if asset != None : print(f"No data for {asset}")
    else :
        if byte_type != "none" : power=(int(math.log(grand_total,byte_mult))) # get the magnitude
        print(f"Grand Total = {grand_total/pow(byte_mult,power):.2f} {SI_unit[power]}",file=f)
        if byte_type != "none" : print(f"(1 {SI_name[power]} = {byte_mult}^{power} = {pow(byte_mult,power)} bytes)",file=f)
    if f != None: f.close()
    
def round_date(date,period) :
    # work out periods for granularity
    # rounding down in all cases. period should be an integer multiple of minutes that fit into an hour, or hours that fit into a day
    # in all cases, remove seconds and microseconds
    date=date.replace(second=0,microsecond=0)
    # for 1 minute remove the seconds
    if period == 1 : 
        return date
    # for less than one hour
    # round the minutes element to nearest multiple
    if period < 60 :
        minute=int(date.minute/period)*period
        return date.replace(minute=minute)
    # for more than one hour remove the minutes
    if period >= 60:
        date=date.replace(minute=0)
    if period == 60 :
        return date
    # round the hours element to the nearest hour.
    if period > 60 :
        period //= 60 # integer division
        hour=int(date.hour/period)*period
        return date.replace(hour=hour)
    
    
    
    
    
if __name__ == "__main__" :
    main(sys.argv[1:])




