#!/bin/bash

for i in $(ls /dev | grep -oP "sd.*[^\d+]" | sort -u); do
    echo /dev/$i
    echo -------------------
    echo $(sudo smartctl -A /dev/$i | grep Temperature_Celsius | awk '{print $10}') "Celsius"
    printf "\n"
done
