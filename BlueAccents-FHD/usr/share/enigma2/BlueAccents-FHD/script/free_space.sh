#!/bin/bash
# mounted storage:
_storage=/media/usb
#left space in MB:
_wish_free_size=10240
#days to delete:
_maxdays=30

_free_size=$(df -m | grep $_storage | awk '{print $4}')

if (( $(echo "$_free_size < $_wish_free_size" |bc -l) )); then
        find $_storage/xtraEvent/ -type f -mtime +$_maxdays -delete
	echo "free space smaler than $_wish_free_size . cleaning up now!!!"
else
        echo "free space left: $_free_size"
	echo "nothing to do; exit"
fi
