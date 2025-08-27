# MeshCentralStats
MeshCentral is a tool for providing remote access to computing assets (and other connected devices).
It has many features, but one that is lacking is reporting. There is no built-in tool to report on usage by user or asset.

The script here is a first attempt at measuring network usage by a simple parse of the existing events logfile and collation of that data by user and asset.

There are a couple of options available to tweak the time period, the user and the asset of interest. Sample files for scheduling the running of the analysis are included.

The principal motivation here was to provide a means of assigning cost to users/assets given that the author's MeshCentral installation is running on cloud hardware and there is a charge for network transfers.
