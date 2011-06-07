#!/bin/bash

. /etc/socorro/socorrorc

NAME=`basename $0 .sh`
lock $NAME
${SOCORRO_DIR}/analysis/modulelist.sh Firefox "Windows NT" `date +%Y%m%d`
EXIT_CODE=$?
unlock $NAME

exit $EXIT_CODE
