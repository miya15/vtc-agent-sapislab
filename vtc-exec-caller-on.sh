#!/bin/bash

export VTC_API_URL='https://api.sapislab.com'
export VTC_API_APIKEY='set api-key here'
export VTC_API_SECRETKEY='set secret-key here'
export VTC_API_KEY='set KeyValues service key here'

python /home/pi/vtc-detector.py '{"start":{"check":"closed","next":"request to open"}}'


