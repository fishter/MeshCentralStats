#!/usr/bin/env bash
# Run usage analysis and save to text file.
HOMEPATH=/home/ec2-user
OUTPUT_PATH=${HOMEPATH}/meshcentral-files/domain/user-fosina_admin/NetUsage
INPUT_PATH=${HOMEPATH}/meshcentral-data
DATE_BIN=/usr/bin/date
FIND_BIN=/usr/bin/find
RM_BIN=/usr/bin/rm
SCRIPT_NAME=${HOMEPATH}/AnalyseMeshCentralEventsdb_v4.py


# create daily file, picking only recently updated db files to do so.
SINCE=$(${DATE_BIN} +"%Y-%m-%d" --date='yesterday')
BEFORE=$(${DATE_BIN} +"%Y-%m-%d" --date='today') # does not include today
OUTPUT_FILE=${OUTPUT_PATH}/NetUsage_Daily_${SINCE}.txt
${FIND_BIN} ${INPUT_PATH} -name meshcentral-events.db\* -newermt "$(${DATE_BIN} --date='yesterday')" -exec ${SCRIPT_NAME} --before=${BEFORE} --since=${SINCE} --measurement=dec -o ${OUTPUT_FILE} {} +

# create monthly file (on 1st, for previous month),
# picking only db files modified in the last month - this may miss a few seconds of data at the start of a month, if the log rotation happens at exactly the wrong time.
# and delete all the daily files from previous month as they are now in the monthly file.
if [ $(${DATE_BIN} +"%d") == 01 ]
then
    SINCE=$(${DATE_BIN} +"%Y-%m-01" --date="yesterday") # the first of the preceding month, if today is the first of the current month.
#    BEFORE=$(${DATE_BIN} +"%Y-%m-%d" --date="today") # does not include today
    OUTPUT_FILE = ${OUTPUT_PATH}/NetUsage_Monthly_${SINCE}--$(${DATE_BIN} +"%Y-%m-%d" --date="yesterday").txt
    ${FIND_BIN} ${INPUT_PATH} -name meshcentral-events.db\* -newermt "$(${DATE_BIN} --date='last month')" -exec ${SCRIPT_NAME} --before=${BEFORE} --since=${SINCE} --measurement=dec -o ${OUTPUT_FILE} {} +
    if [ $? == 0 ]
    then
        ${RM_BIN} ${OUTPUT_PATH}/*Daily-$($DATE_BIN} +'%Y-%m' --date=yesterday)*
    fi
fi

