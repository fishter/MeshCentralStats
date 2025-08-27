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
from datetime import datetime, timezone
from pathlib import Path

def main(argv) :
    default_file = Path.home() / "meshcentral-data" / "meshcentral-events.db"
    
    default_byte_type='none'
    default_since=datetime(2000,1,1,tzinfo=timezone.utc) # All times/dates are using UTC timezone. If a time/date does not have a timezone it is assumed to be UTC.
    output="console"
    debug = 0
    usage =f"usage: {sys.argv[0]} [sbuamod|h] <filenames>...\n"
    usage+=f"  options:\n"
    usage+=f"-s, --since=<yyyy-mm-dd>, -b, --before=<yyyy-mm-dd> to restrict time span\n"
    usage+=f"-u, --user the user to include in the report (defaults to all)\n"
    usage+=f"-a, --asset the asset to include in the report (defaults to all)\n"
    usage+=f"-m, --measurement units to use 'dec', 'IEC', 'none', defaults to {default_byte_type}\n"
    usage+=f"-o, --output=<filename> to specify an output file, otherwise output to the terminal\n"
    usage+=f"-d, --debug. Specify multiple times to increase level\n"
    usage+=f"-h, --help. Display this help. Use --help+ to get a list of known assets and users\n"
    usage+=f"<filenames> to analyse, defaults to\n    '{default_file}'\n"
    usage+=f"For example:\n"
    usage+=f" {sys.argv[0]} -mdec --since=2025-08-01 meshcentral-events.db\n"
    usage+=f" to output log activity on and after the 1st of August 2025."
    try :
        from MeshCentral_data import nodeids # import a list of known assets and user ids and their aliases
        from MeshCentral_data import userids
    except :
                #    <nodeid> : <alias>
        nodeids = { "node//aabbccddeeffgghhiijjkkllmmnnooppqqrrssttuuvvwwxxyyzz001122334455" : "My Pi"}
                #    <username> : <alias>
        userids = { "admin" : "Administrator" }

    try :
        opts, args = getopt.getopt(argv,"f:s:b:u:o:m:dh",["filename=","since=","before=","user=","asset=","measurement=","output=","debug","help","help+"])
    except getopt.GetoptError:
        print(usage)
        sys.exit(2)

    files = []
    byte_type=None
    since = None
    before = None
    user = None
    asset = None
    for opt, arg in opts :
        if opt in ("-f", "--filename") : # hidden option...
            files.append(arg)
        
        if opt in ("-m", "--measurement"):
            if arg in ['dec','IEC','none'] : byte_type = arg
            else :
                print(f"Unknown unit, default to {default_byte_type}")
                byte_type=default_byte_type

        if opt in ("-d", "--debug") :
            debug += 1

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
            sys.exit(0)

        if opt in ("-s","--since") :
            try : since=datetime.strptime(arg,"%Y-%m-%d").astimezone(timezone.utc)
            except : 
                print(f"{arg} is not a valid date. Use yyyy-mm-dd format.")
                sys.exit(2)

        if opt in ("-b","--before") :
            try : before=datetime.strptime(arg,"%Y-%m-%d").astimezone(timezone.utc)
            except : 
                print(f"{arg} is not a valid date. Use yyyy-mm-dd format.")
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

    if debug > 0 : print(f"Arguments: {argv}")
    if debug > 0 : print(f"Options  : {opts}")
    if debug > 0 : print(f"Args     : {args}")
    if debug > 0 : print(f"units    : {byte_type}")

    if files == [] : files = [default_file]
    if byte_type == None : byte_type=default_byte_type
    if since == None  : since  = default_since
    if before == None : before = datetime.now(timezone.utc)
    
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

    user_data={}
    asset_data={}
    grand_total=0
    
    if debug > 2 : f=0 # file counter
    for file in files :
        if debug >2 :
            f+=1 # increment file counter (1-index)
            printf(f"File #{f} = {file}")
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
                        if debug > 2 :print(f"timestamp {timestamp.strftime('%Y-%m-%d')} is outside time range {since.strftime('%Y-%m-%d')} to {before.strftime('%Y-%m-%d')}")
                        pass
                    else:
                        
                        if (debug > 2) and (before != datetime.now(timezone.utc) or (since != default_since)) :
                            print(f"timestamp {timestamp.strftime('%Y-%m-%d')} is inside time range {since.strftime('%Y-%m-%d')} to {before.strftime('%Y-%m-%d')}")
                        username = line['username']
                        assetname = line['ids'][2]
                        if username in userids: username = userids[username] # pretty name
                        if assetname in nodeids: assetname = nodeids[line['ids'][2]] # pretty name

                        if ((username == user) or (user == None)) and ((assetname == asset) or (asset == None)) :
                            data_total = line['bytesin'] + line['bytesout']
                            grand_total += data_total
                            date = timestamp.strftime('%Y-%m-%d')
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
    
if __name__ == "__main__" :
    main(sys.argv[1:])



