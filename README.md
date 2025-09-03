# MeshCentralStats

## Introduction

MeshCentral is a tool for providing remote access to computing assets (and other connected devices).

The script here is a first attempt at measuring network usage by a simple parse of the existing events logfile and collation of that data by user and asset. (There is a built in Report for that, but it lacks some features).

There are a couple of options available to tweak the time period, the user and the asset of interest. Sample files for scheduling the running of the analysis are included (logrotate, service and timer files).

The principal motivation here was to provide a means of assigning cost to users/assets given that the author's MeshCentral installation is running on cloud hardware and there is a charge for network transfers.

## Installation

Drop the AnalyseMeshCentralStats_v4.py file into your home folder. With no options it will assume that the `meshcentral-events.db` file is in `./meshcentral-data/meshcentral-events.db`. It will then trawl through this file and produce some output day-by-day, for each user and asset it finds in the log.

If you also rename the `meshcentral_data.py.template` file to remove `template` you can add some more friendly aliases for your devices or users. Follow the pattern in the file. You can find the nodeid on the web interface to mesh central. Open the Console and type info. Then, copy the node id to the file adding `node//` at the start.

If you want to be more automated you can put the logrotate config file into `/etc/logrotate.d/` to have logrotate take care of the events.db rotation. You can also set an option in your meshcentral `config.json` to limit the history in the events.db. Consider the two features together if you want to keep a permanent record.

The shell script, `run_usage_stats.sh`, is useful to produce output files with specific contents. This can be controlled by the `.service` and `.timer` files.  Put these systemd configuration files in `/usr/lib/systemd/system` and run `systemctl daemon-reload`, then `systemctl enable meshcentral_usage_stats.service`, `systemctl enable meshcentral_usage_stats.timer`, and `systemctl start meshcentral_usage_stats.timer`.

You will likely have to edit the paths in the shell script and the service file to point to the right files. You may also have to run dos2unix on the py and sh files, and set them to be executable (chmod +x <file>).

If you need help, or have suggestions, post an issue here: https://github.com/fishter/MeshCentralStats/issue

## Usage

Run the script with the -h or --help options and it will give you some assistance. --help+ will output a list of the known nodeids and users, and a short list of time formats to be used with the --since and --before options.

    usage: ./AnalyseMeshCentralEventsdb_v4.py [sbguamod|h] <filenames>...
      options:
    -s, --since=, -b, --before= to restrict time span. Use ISO8601 formats for UTC yyyy-mm-ddZhh:mm:ss, hh:mm:ss, hh:mm or hh'h'.
    -g, --granularity=<period> to specify a time period to aggregate.
     Valid values are 1, 2, 3, 4, 5, 6, 10, 15, 20, 30, 60, 120, 180, 240, 360, 720, 1440  1 minute to 1 day.
    -u, --user the user to include in the report (defaults to all)
    -a, --asset the asset to include in the report (defaults to all)
    -m, --measurement units to use 'dec', 'IEC', 'none', defaults to none
    -o, --output=<filename> to specify an output file, otherwise output to the terminal
    -d, --debug. Specify multiple times to increase level
    -h, --help. Display this help. Use --help+ to get a list of known assets and users
    <filenames> to analyse, defaults to
        '~/meshcentral-data/meshcentral-events.db'
    For example:
      ./AnalyseMeshCentralEventsdb_v4.py -mdec --since=2025-08-01 meshcentral-events.db
     to output log activity on and after the 1st of August 2025.
      ./AnalyseMeshCentralEventsdb_v4.py -mdec --since=12h meshcentral-events.db
     to output log activity since the previous midday.
