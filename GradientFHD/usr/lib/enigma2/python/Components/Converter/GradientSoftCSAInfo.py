# -*- coding: utf-8 -*-
#
# =============================================================================
#  DEUTSCH / GERMAN
# =============================================================================
#  IsSoftCSA Converter for Enigma2 Skins
#
#  Copyright (c) 2026  @WXbet, @stein17
#
#  Freeware:
#  Dieses Projekt ist Freeware. Die private Nutzung ist erlaubt.
#  Anpassungen für eigene Skins/Setups (z.B. OpenATV/Enigma2) sind ausdrücklich
#  erlaubt.
#
#  Bedingungen:
#  1) Dieser Copyright-/Lizenz-Header muss in allen Kopien und abgeleiteten
#     Versionen vollständig erhalten bleiben und darf nicht entfernt oder
#     unkenntlich gemacht werden.
#  2) Eine Weitergabe (unverändert oder geändert) ist erlaubt, sofern dieser
#     Header erhalten bleibt und die ursprünglichen Urheber genannt werden.
#  3) Eine kommerzielle Nutzung (Verkauf, Paywall, bezahlte Images/Feeds,
#     kommerzielle Bundles) ist ohne vorherige schriftliche Zustimmung der
#     Urheber nicht gestattet.
#
#  Haftungsausschluss:
#  Die Software wird „wie sie ist“ bereitgestellt, ohne jegliche Garantie.
#  Die Nutzung erfolgt auf eigene Gefahr. Für Schäden oder Datenverlust wird
#  keine Haftung übernommen.
#
#
#  ENGLISH
# =============================================================================
#  IsSoftCSA Converter for Enigma2 Skins
#
#  Copyright (c) 2026  @WXbet, @stein17
#
#  Freeware:
#  This project is freeware. Private use is permitted.
#  Modifications for your own skins/setups (e.g. OpenATV/Enigma2) are explicitly
#  allowed.
#
#  Conditions:
#  1) This copyright/license header must be kept fully intact in all copies and
#     derivative works and must not be removed or obscured.
#  2) Redistribution (modified or unmodified) is permitted as long as this header
#     is retained and the original authors are credited.
#  3) Commercial use (sale, paywall, paid images/feeds, commercial bundles) is
#     not permitted without prior written consent from the authors.
#
#  Disclaimer:
#  This software is provided “as is”, without warranty of any kind.
#  Use at your own risk. The authors are not liable for any damages or data loss.
# =============================================================================
# 
# This standalone converter can be used in skins to show/hide elements
# based on whether SoftCSA (software descrambling) is active.
#
# Works on both SoftCSA-enabled and standard Enigma2 builds:
# - On SoftCSA builds: Returns True when SW descrambling is active
# - On standard builds: Always returns False (element stays hidden)
# =============================================================================
#   SoftCSAInfo Converter (extended)
# - IsSoftCSA (default): True if SoftCSA is active
# - IsCryptedNoSoftCSA : True if service is crypted AND SoftCSA is NOT active
# - IsCrypted          : True if service is crypted
#
# Usage examples in skin.xml:
#   <convert type="SoftCSAInfo" />
#   <convert type="SoftCSAInfo">IsSoftCSA</convert>
#   <convert type="SoftCSAInfo">IsCryptedNoSoftCSA</convert>
#   <convert type="SoftCSAInfo">IsCrypted</convert>
#
# Crypt-Icon nur wenn crypted UND NICHT SoftCSA:
#
# <widget source="session.CurrentService" render="Pixmap" pixmap="icons/ico_crypt_on.png" position="1021,885" size="37,45" zPosition="2" alphatest="blend">
#    <convert type="SoftCSAInfo">IsCryptedNoSoftCSA</convert>
#    <convert type="ConditionalShowHide" />
# </widget>
#
# SoftCSA-Icon wie gehabt:
#
# <widget source="session.CurrentService" render="Pixmap" pixmap="icons/ico_softcsa.png" position="974,885" size="84,45" zPosition="2" alphatest="blend">
#    <convert type="SoftCSAInfo" />
#    <convert type="ConditionalShowHide" />
# </widget>
#

from enigma import iServiceInformation, iPlayableService

from Components.Converter.Converter import Converter
from Components.Element import cached


class GradientSoftCSAInfo(Converter):
    def __init__(self, type):
        Converter.__init__(self, type)

        self._mode = (type or "").strip() or "IsSoftCSA"

        # SoftCSA exists only in certain OpenATV builds
        self._hasSoftCSA = hasattr(iServiceInformation, "sIsSoftCSA")
        # IsCrypted is standard in most builds
        self._hasIsCrypted = hasattr(iServiceInformation, "sIsCrypted")

    def _getServiceInfo(self):
        service = getattr(self.source, "service", None)
        if service:
            try:
                return service.info()
            except Exception:
                return None
        return None

    def _isSoftCSA(self, info):
        if not self._hasSoftCSA or not info:
            return False
        try:
            return info.getInfo(iServiceInformation.sIsSoftCSA) == 1
        except Exception:
            return False

    def _isCrypted(self, info):
        if not self._hasIsCrypted or not info:
            return False
        try:
            return info.getInfo(iServiceInformation.sIsCrypted) == 1
        except Exception:
            return False

    @cached
    def getBoolean(self):
        info = self._getServiceInfo()

        if self._mode in ("", "IsSoftCSA", "SoftCSA"):
            return self._isSoftCSA(info)

        if self._mode in ("IsCryptedNoSoftCSA", "CryptedNoSoftCSA"):
            # show crypt-icon only if crypted AND SoftCSA is NOT active
            return self._isCrypted(info) and (not self._isSoftCSA(info))

        if self._mode in ("IsCrypted", "Crypted"):
            return self._isCrypted(info)

        # Unknown mode -> safe False
        return False

    boolean = property(getBoolean)

    def changed(self, what):
        # refresh when service info updates
        if what[0] == self.CHANGED_SPECIFIC:
            if what[1] == iPlayableService.evUpdatedInfo:
                Converter.changed(self, what)
        elif what[0] != self.CHANGED_SPECIFIC:
            Converter.changed(self, what)
