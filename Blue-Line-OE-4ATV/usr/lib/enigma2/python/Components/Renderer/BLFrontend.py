#######################################################################
#
#    Renderer for Enigma2
#    Coded by shamann (c)2011
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

from Components.Renderer.Renderer import Renderer
from enigma import eLabel
from Components.VariableText import VariableText
from enigma import eServiceCenter, iServiceInformation, eDVBFrontendParametersSatellite, eDVBFrontendParametersCable
from xml.etree.cElementTree import parse
from Components.config import config

class BLFrontend(VariableText, Renderer):

    def __init__(self):
        Renderer.__init__(self)
        VariableText.__init__(self)
        self.ena = True
        try:
            self.ena = config.plugins.stein17skins
        except: pass
        if not self.ena:
            try:
                self.allSat = {}
                satellites = parse("/etc/tuxbox/satellites.xml").getroot()
                if satellites is not None:
                    for x in satellites.findall("sat"):
                        name = x.get("name") or None
                        position = x.get("position") or None
                        if name is not None and position is not None:
                            position = "%s.%s" % (position[:-1], position[-1:])
                            if position.startswith("-"):
                                position = "%sW" % position[1:]
                            else:
                                position = "%sE" % position
                            if position.startswith("."):
                                position = "0%s" % position
                            self.allSat[position] = str(name.encode("utf-8"))
            except: pass
    GUI_WIDGET = eLabel

    def connect(self, source):
        Renderer.connect(self, source)
        self.changed((self.CHANGED_DEFAULT,))

    def changed(self, what):
        if self.instance:
            if what[0] == self.CHANGED_CLEAR:
                self.text = "Transporder info detect failed !"
            else:
                serviceref = self.source.service
                info = eServiceCenter.getInstance().info(serviceref)
                if info and serviceref:
                    sname = info.getInfoObject(serviceref, iServiceInformation.sTransponderData)
                    fq = pol = fec = sr = orb = ""
                    try:
                        if "frequency" in sname:
                            tmp = int(sname["frequency"])/1000
                            fq = str(tmp) + "  "
                        if "polarization" in sname:
                            try:
                                pol = {
                                        eDVBFrontendParametersSatellite.Polarisation_Horizontal : "H  ",
                                        eDVBFrontendParametersSatellite.Polarisation_Vertical : "V  ",
                                        eDVBFrontendParametersSatellite.Polarisation_CircularLeft : "CL  ",
                                        eDVBFrontendParametersSatellite.Polarisation_CircularRight : "CR  "}[sname["polarization"]]
                            except:
                                pol = "N/A  "
                        if "fec_inner" in sname:
                            try:
                                fec = {
                                        eDVBFrontendParametersSatellite.FEC_None : _("None  "),
                                        eDVBFrontendParametersSatellite.FEC_Auto : _("Auto  "),
                                        eDVBFrontendParametersSatellite.FEC_1_2 : "1/2  ",
                                        eDVBFrontendParametersSatellite.FEC_2_3 : "2/3  ",
                                        eDVBFrontendParametersSatellite.FEC_3_4 : "3/4  ",
                                        eDVBFrontendParametersSatellite.FEC_5_6 : "5/6  ",
                                        eDVBFrontendParametersSatellite.FEC_7_8 : "7/8  ",
                                        eDVBFrontendParametersSatellite.FEC_3_5 : "3/5  ",
                                        eDVBFrontendParametersSatellite.FEC_4_5 : "4/5  ",
                                        eDVBFrontendParametersSatellite.FEC_8_9 : "8/9  ",
                                        eDVBFrontendParametersSatellite.FEC_9_10 : "9/10  "}[sname["fec_inner"]]
                            except:
                                fec = "N/A  "
                            if fec == "N/A  ":
                                try:
                                    fec = {
                                            eDVBFrontendParametersCable.FEC_None: _("None  "),
                                            eDVBFrontendParametersCable.FEC_Auto: _("Auto  "),
                                            eDVBFrontendParametersCable.FEC_1_2: "1/2  ",
                                            eDVBFrontendParametersCable.FEC_2_3: "2/3  ",
                                            eDVBFrontendParametersCable.FEC_3_4: "3/4  ",
                                            eDVBFrontendParametersCable.FEC_5_6: "5/6  ",
                                            eDVBFrontendParametersCable.FEC_7_8: "7/8  ",
                                            eDVBFrontendParametersCable.FEC_8_9: "8/9  ",}[sname["fec_inner"]]
                                except:
                                    fec = "N/A  "
                        if "symbol_rate" in sname:
                            tmp = int(sname["symbol_rate"])/1000
                            sr = str(tmp) + "  "
                        if "orbital_position" in sname:
                            numSat = sname["orbital_position"]
                            if numSat > 1800:
                                idx = str((float(3600 - numSat))/10.0) + "W"
                            else:
                                idx = str((float(numSat))/10.0) + "E"
                            if not self.ena:
                                if idx in self.allSat:
                                    orb = self.allSat.get(idx)
                                else:
                                    orb = "Sat on position: %s" % idx
                            else:
                                orb = idx
                    except:
                        pass
                    if fq != "":
                        try:
                            self.text = fq + pol + fec + sr + orb.replace("E)", "\xc2\xb0E)").replace("W)", "\xc2\xb0W)")
                        except:
                            self.text = fq + pol + fec + sr + orb
                    else:
                        self.text = "Transporder info not detected"
