#!/bin/bash

export VTC_API_URL='set vtc-api-server url here.'
export VTC_API_KEY='set api-key here for client.'

python /home/pi/vtc-detector.py '{"start":{"check":"request to open","next":"opened"},"end":{"check":"request to close","next":"closed"}}'


