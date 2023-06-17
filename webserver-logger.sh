#!/usr/bin/env bash
(cat ~/mqlog.txt; mosquitto_sub -p 1883 -h localhost -t 'msh/+/json/#' -u $MUSER -P $MPASS -F %J | tee -a ~/mqlog.txt) | ./webserver.py
