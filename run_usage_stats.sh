#!/usr/bin/env bash
# Run usage analysis and save to text file.
HOMEPATH=$HOME
OUTPUT_PATH=${HOMEPATH}/meshcentral-files/domain/user-fosina_admin/NetUsage
INPUT_PATH=${HOMEPATH}/meshcentral-data
SCRIPT_NAME=${HOMEPATH}/AnalyseMeshCentralEventsdb_v4.py

# create daily file, picking only recently updated db files to do so.
SINCE=$(date +"%Y-%m-%d" --date='yesterday')
BEFORE=$(date +"%Y-%m-%d" --date='today') # does not include today
OUTPUT_FILE=${OUTPUT_PATH}/NetUsage_Daily_${SINCE}.txt
SCRIPT_OPTIONS="--before=${BEFORE} --since=${SINCE} --measurement=dec --granularity=60 -o ${OUTPUT_FILE}"
find ${INPUT_PATH} -name meshcentral-events.db\* -newermt "$(date --date='yesterday')" -exec ${SCRIPT_NAME} ${SCRIPT_OPTIONS} {} +

# create monthly file (on 1st, for previous month),
# picking only db files modified in the last month - this may miss a few seconds of data at the start of a month, if the log rotation happens at exactly the wrong time.
# and delete all the daily files from previous month as they are now in the monthly file.
if [ $(date +"%d") == 01 ]
then
    SINCE=$(date +"%Y-%m-01" --date="yesterday") # the first of the preceding month, if today is the first of the current month.
#    BEFORE=$(${DATE_BIN} +"%Y-%m-%d" --date="today") # does not include today
    OUTPUT_FILE = ${OUTPUT_PATH}/NetUsage_Monthly_${SINCE}--$(date +"%Y-%m-%d" --date="yesterday").txt
    SCRIPT_OPTIONS="--before=${BEFORE} --since=${SINCE} --measurement=dec --granularity=1440 -o ${OUTPUT_FILE}"
    find ${INPUT_PATH} -name meshcentral-events.db\* -newermt "$(date} --date='last month')" -exec ${SCRIPT_NAME} ${SCRIPT_OPTIONS} {} +
    if [ $? == 0 ]
    then
        rm ${OUTPUT_PATH}/*Daily-$(date +'%Y-%m' --date=yesterday)-*.txt
    fi
fi


