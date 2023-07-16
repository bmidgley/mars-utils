#!/usr/bin/env bash
set -e
while sleep 6
do
  date=$(date +%F)
  folder=$(eval echo "~$MSERVERUSER/mqlog")
  echo logging to $folder
  logfile=$folder/$date
  mkdir -p $folder
  touch $logfile
  ./webserver.py $folder $MSERVERUSER < <(cat $logfile; mosquitto_sub -p 1883 -h localhost -t 'msh/+/json/#' -u $MUSER -P $MPASS -F %J | tee -a $logfile)
done
