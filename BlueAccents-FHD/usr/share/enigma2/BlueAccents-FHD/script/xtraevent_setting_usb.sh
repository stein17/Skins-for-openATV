#!/bin/sh

# ============================================================================================================
SETTINGS="/etc/enigma2/settings"
echo "Adding new setting ..."
echo ""
echo ">>>>>>>>>     RESTARTING     <<<<<<<<<"
echo ""
init 4
sleep 3
sed -i "/xtraEvent/d" $SETTINGS
{
	echo "config.plugins.xtraEvent.backdrop=True"
	echo "config.plugins.xtraEvent.banner=True"
    echo "config.plugins.xtraEvent.cnfg=True"
	echo "config.plugins.xtraEvent.extra3=False"
	echo "config.plugins.xtraEvent.info=True"
	echo "config.plugins.xtraEvent.loc=/media/usb/"
	echo "config.plugins.xtraEvent.onoff=True"
	echo "config.plugins.xtraEvent.poster=True"
	echo "config.plugins.xtraEvent.searchLang=True"
	echo "config.plugins.xtraEvent.searchMOD=Bouquets"
	echo "config.plugins.xtraEvent.searchNUMBER=24"
	echo "config.plugins.xtraEvent.searchType=multi"
	echo "config.plugins.xtraEvent.timerHour=2"
	echo "config.plugins.xtraEvent.timerMod=Period"
	echo "config.plugins.xtraEvent.tmdb=True"
	echo "config.plugins.xtraEvent.tvdb=True"
	
} >> $SETTINGS

# ============================================================================================================
sleep 2
sync
init 3
echo "==================================================================="
echo "===                          FINISHED                           ==="
echo "==================================================================="
exit 0
