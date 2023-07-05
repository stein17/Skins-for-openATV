#!/bin/sh
echo "                                                                            "
echo "                                                                            "
echo "                                                                            "
echo "                                                                            "
echo "Check if a previous version of the PLi-HD-FullNight_stein17_Mod is installed"
if [ -f /usr/share/enigma2/PLi-HD-FullNight_stein17_Mod/skin.xml ]; then
    cp -R /usr/share/enigma2/PLi-HD-FullNight_stein17_Mod/ /tmp
    rm -rf /usr/share/enigma2/PLi-HD-FullNight_stein17_Mod
	rm -rf /usr/lib/enigma2/python/Plugins/Extensions/PLiHDFullNightMod*
    echo "                                                   "
    echo "Previous PLi-HD-FullNight_stein17_Mod skin installation        "
    echo "    was found and removed successfully!            "
    echo "                                                   "
fi
echo "                                                       "
echo "PLi-HD-FullNight_stein17_Mod is now being installed...        "
echo "                                                       "
exit 0
