#!/bin/bash

export VTC_API_URL='set vtc-api-server url here.'
export VTC_API_KEY='set api-key here for server.'

python /home/pi/vtc-detector.py '{"end":{"check":"opened","next":"request to close"}}'


