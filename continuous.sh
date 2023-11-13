#!/usr/bin/env bash
while true; do
	./gpx2mq.py $1 &
	sleep 300
done
