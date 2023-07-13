#!/bin/bash

while true; do eval "$(cat /opt/meteo/meteo-pipe)" &> /opt/meteo/fifo_out.log; done