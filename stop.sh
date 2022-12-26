#!/user/bin/env bash

echo "stop sub_module"

PROCESS_NAME="sub_module.py"
CHECK=`ps -ef | grep $PROCESS_NAME | wc | awk '{print$1}'`

if [ $CHECK -gt 1 ]
then
    PID=`ps -eo user,pid,command | grep $PROCESS_NAME | grep -v grep | awk '{print $2}'`
    kill ${PID} && sleep 2;
    echo "sub_module stop success"
else
    echo "sub_module already stop"
fi
