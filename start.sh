#!/user/bin/env bash

echo "start sub_module"

PROCESS_NAME="sub_module.py"
SERVICE_HOST=$HOSTNAME
CHECK=`ps -ef | grep $PROCESS_NAME | wc | awk '{print$1}'`

RED='\033[1;31m'
GRE='\033[1;32m'
NC='\033[0m'  # No Color

if [ $CHECK -gt 1 ]
then
    STATUS="sub_module is already running"
    PID=`ps -eo user,pid,command | grep $PROCESS_NAME | grep -v grep | awk '{print $2}'`
    printf "${RED}$STATUS, PID : $PID${NC}\n"
    printf "${PID}"
else
    STATUS="sub_module is not running, sub_module start"
    PID=`ps -eo user,pid,command | grep $PROCESS_NAME | grep -v grep | awk '{print $2}'`
    printf "${GRE}$STATUS${NC}\n"
    source activate sub_module && python sub_module.py > /dev/null &
fi
