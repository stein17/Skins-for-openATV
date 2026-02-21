<!-- UNIVERSELLE SKIN INTEGRATION für GradientFHD Plugin -->
<!-- Funktioniert mit ALLEN Enigma2 Sources -->

<!-- ================================================== -->
<!-- EPG INTEGRATION (source="Event") -->
<!-- ================================================== -->

<!-- EPG  Event -->
		<widget source="Event" render="GradientParental" position="1266,889" size="40,40" alphatest="blend" zPosition="105" transparent="1" />
		<widget source="Event" render="GradientPosterX" position="1130,670" cornerRadius="6" size="177,260" zPosition="2" />
		<widget source="Event" render="GradientBackdropX" position="42,153" size="348,196" zPosition="11" cornerRadius="6" />
		<widget source="Event" render="GradientStarX" position="1126,934" size="185,19" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />

<!-- ================================================== -->
<!-- INFOBAR INTEGRATION (session.Event_Now/Next) -->
<!-- ================================================== -->

<!-- Aktuelles Event -->
		<!-- Backdrop -->
		<widget source="session.Event_Now" render="GradientBackdropX" position="20,558" size="300,169" zPosition="11" cornerRadius="6" />
		<!-- Parental -->
		<widget source="session.Event_Now" render="GradientParental" position="257,664" size="60,60" alphatest="blend" zPosition="110" transparent="1" />
		<!-- ImdbRating -->
		<widget source="session.Event_Now" render="GradientStarX" position="20,730" size="300,31" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />
	

<!-- Nächstes Event -->
	<!-- Backdrop -->
		<widget source="session.Event_Next" render="GradientBackdropX" position="1510,558" size="300,169" zPosition="11" cornerRadius="6" />
		<!-- Parental -->
		<widget source="session.Event_Next" render="GradientParental" position="1747,664" size="60,60" alphatest="blend" zPosition="110" transparent="1" />
		<!-- ImdbRating -->
		<widget source="session.Event_Next" render="GradientStarX" position="1510,730" size="300,31" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" />

<!-- ================================================== -->
<!-- KOMPLETTES BEISPIEL:Infobar INTEGRATION  -->
<!-- ================================================== -->

	<!-- "InfoBar_Poster_X" -->
		<!-- Parental -->
		<widget source="session.Event_Now" render="GradientParental" position="144,677" size="60,60" alphatest="blend" zPosition="110" transparent="1" />
		<widget source="session.Event_Next" render="GradientParental" position="1749,677" size="60,60" alphatest="blend" zPosition="110" transparent="1" />
		<!-- Poster -->
		<widget source="session.Event_Now" render="GradientPosterX" position="20,460" size="185,278" cornerRadius="6" zPosition="2" />
		<widget source="session.Event_Next" render="GradientPosterX" position="1625,460" size="185,278" cornerRadius="6" zPosition="2" />
		<!-- ImdbRating -->
		<widget source="session.Event_Now" render="GradientStarX" position="20,742" size="185,19" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />
		<widget source="session.Event_Next" render="GradientStarX" position="1625,742" size="185,19" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />

	<!-- InfoBar_Backdrop_X -->
		<!-- Backdrop -->
		<widget source="session.Event_Now" render="GradientBackdropX" position="20,558" size="300,169" zPosition="11" cornerRadius="6" />
		<widget source="session.Event_Next" render="GradientBackdropX" position="1510,558" size="300,169" zPosition="11" cornerRadius="6" />
		<!-- Parental -->
		<widget source="session.Event_Now" render="GradientParental" position="257,664" size="60,60" alphatest="blend" zPosition="110" transparent="1" />
		<widget source="session.Event_Next" render="GradientParental" position="1747,664" size="60,60" alphatest="blend" zPosition="110" transparent="1" />
		<!-- ImdbRating -->
		<widget source="session.Event_Now" render="GradientStarX" position="20,730" size="300,31" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />
		<widget source="session.Event_Next" render="GradientStarX" position="1510,730" size="300,31" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" />

	<!-- InfoBar_Poster_Backdrop_X -->
		<!-- Backdrop -->
		<widget source="session.Event_Now" render="GradientBackdropX" position="220,520" size="300,169" zPosition="11" cornerRadius="6" />
		<widget source="session.Event_Next" render="GradientBackdropX" position="1310,520" size="300,169" zPosition="11" cornerRadius="6" />
		<!-- Parental -->
		<widget source="session.Event_Now" render="GradientParental" position="144,677" size="60,60" alphatest="blend" zPosition="110" transparent="1" />
		<widget source="session.Event_Next" render="GradientParental" position="1749,677" size="60,60" alphatest="blend" zPosition="110" transparent="1" />
		<!-- 	Poster -->
		<widget source="session.Event_Now" render="GradientPosterX" position="20,460" size="185,278" cornerRadius="6" zPosition="2" />
		<widget source="session.Event_Next" render="GradientPosterX" position="1625,460" size="185,278" cornerRadius="6" zPosition="2" />
		<!-- ImdbRating -->
		<widget source="session.Event_Now" render="GradientStarX" position="20,742" size="185,19" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />
		<widget source="session.Event_Next" render="GradientStarX" position="1625,742" size="185,19" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />
<!-- ================================================== -->
	<!-- SecondInfobar_Poster_X -->
<!-- ================================================== -->
		<!-- Parental -->
		<widget source="session.Event_Now" render="GradientParental" position="878,658" size="60,60" alphatest="blend" zPosition="110" transparent="1" />
		<widget source="session.Event_Next" render="GradientParental" position="1808,658" size="60,60" alphatest="blend" zPosition="110" transparent="1" />
		<!-- Poster -->
		<widget source="session.Event_Now" render="GradientPosterX" position="600,220" size="340,500" cornerRadius="6" zPosition="2" />
		<widget source="session.Event_Next" render="GradientPosterX" position="1530,220" size="340,500" cornerRadius="6" zPosition="2" />
		<!-- ImdbRating -->
		<widget source="session.Event_Now" render="GradientStarX" position="610,725" size="315,32" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />
		<widget source="session.Event_Next" render="GradientStarX" position="1542,725" size="315,32" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />

<!-- ================================================== -->
<!-- SENDERLISTE/CHANNELLIST (source="ServiceEvent")    -->
<!-- Bis zu 6 Events pro Sender möglich mit nexts="0-5" -->
<!-- KOMPLETTES BEISPIEL: CHANNELLIST                   -->
<!-- ================================================== -->
    
    <!-- Senderliste mit bis zu 6 Events -->
	    <!-- Event 1 -->
		<widget source="ServiceEvent" render="GradientBackdropX" nexts="1" position="1601,147" size="270,150" zPosition="6" cornerRadius="9" />
		<!-- Event 2 -->
		<widget source="ServiceEvent" render="GradientBackdropX" nexts="2" position="1601,372" size="270,150" zPosition="6" cornerRadius="9" />
		<!-- Event 3 -->
		<widget source="ServiceEvent" render="GradientBackdropX" nexts="3" position="1601,597" size="270,150" zPosition="6" cornerRadius="9" />
		<!-- Event 4 -->
		<widget source="ServiceEvent" render="GradientBackdropX" nexts="4" position="1601,822" size="270,150" zPosition="6" cornerRadius="9" />
		<!-- Event  (aktuell) -->
		<widget source="ServiceEvent" render="GradientPosterX" nexts="0" position="832,90" size="183,274" zPosition="6" cornerRadius="6" />
		<widget source="ServiceEvent" render="GradientParental" position="953,302" size="60,60" alphatest="blend" zPosition="10" transparent="1" />
		<widget source="ServiceEvent" render="GradientStarX" position="831,370" size="185,19" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />
		
		<!-- Event  (aktuell) -->
		<widget source="ServiceEvent" nexts="0" render="GradientPosterX" position="850,300" size="200,300" cornerRadius="6" zPosition="6" />
		<!-- Event 1 -->
		<widget source="ServiceEvent" nexts="1" render="GradientPosterX" position="880,700" size="180,270" cornerRadius="6" zPosition="5" />
		<!-- Event 2 -->
		<widget source="ServiceEvent" nexts="2" render="GradientPosterX" position="1146,700" size="180,270" cornerRadius="6" zPosition="5" />
		<!-- Event 3 -->
		<widget source="ServiceEvent" nexts="3" render="GradientPosterX" position="1412,700" size="180,270" cornerRadius="6" zPosition="5" />
		<!-- Event 4 -->
		<widget source="ServiceEvent" nexts="4" render="GradientPosterX" position="1678,700" size="180,270" cornerRadius="6" zPosition="5" />
		<!-- Event  (aktuell) -->
		<widget source="ServiceEvent" render="GradientParental" position="980,532" size="60,60" alphatest="blend" zPosition="10" transparent="1" />
		<widget source="ServiceEvent" render="GradientStarX" position="858,610" size="185,19" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />
		<widget source="ServiceEvent" render="GradientBackdropX" position="840,80" size="1060,596" zPosition="3" />
		<ePixmap name="vod_backdrop" pixmap="screens/backdrop.png" position="840,79" size="1060,614" alphatest="blend" zPosition="5" />	
		
		<!-- Senderliste now next Events -->
		<widget source="ServiceEvent" render="GradientPosterX" nexts="0" position="816,118" size="240,360" cornerRadius="6" zPosition="2" />
		<widget source="ServiceEvent" render="GradientPosterX" nexts="1" position="1086,118" size="240,360" cornerRadius="6" zPosition="2" />

<!-- ================================================== -->
<!-- EVENTVIEW INTEGRATION (source="Event") -->
<!-- ================================================== -->
<!-- Eventview verwendet Event -->
		<widget source="Event" render="GradientBackdropX" position="50,517" size="530,298" zPosition="11" cornerRadius="6" />
		<widget source="Event" render="GradientParental" position="835,732" size="60,60" alphatest="blend" zPosition="105" transparent="1" />
		<widget source="Event" render="GradientPosterX" position="635,517" cornerRadius="6" size="185,278" zPosition="2" />
		<widget source="Event" render="GradientStarX" position="635,795" size="185,19" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />

<!-- ================================================== -->
<!-- EMC SELECTION & MOVIE SELECTION (source="Service") -->
<!-- ================================================== -->

<!-- Movie Selection - für Aufnahmen und Movies -->
		<!--  Poster -->
		<widget source="Service" render="GradientPosterXEMC" position="498,620" cornerRadius="6" size="218,320" zPosition="3"  />
		<!--  Backdrop -->
		<widget source="Service" render="GradientBackdropXEMC" position="30,90" cornerRadius="6" size="685,388" zPosition="3"  />
		<!-- Banner -->
		<widget source="Service" render="GradientBannerXEMC" position="center,620" size="1000,185" zPosition="14" alphatest="blend" />
		<!-- Parental -->
		<widget source="Service" render="GradientParental" position="652,875" size="60,60" alphatest="blend" zPosition="110" transparent="1" />
		<!-- ImdbRating -->
		<widget source="Service" render="GradientStarX" position="497,947" size="220,22" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />

<!-- EMC Enhanced Movie Center -->
		<!--  Poster -->
		<widget source="Service" render="GradientPosterXEMC" position="498,620" cornerRadius="6" size="218,320" zPosition="3"  />
		<!--  Backdrop -->
		<widget source="Service" render="GradientBackdropXEMC" position="30,90" cornerRadius="6" size="685,388" zPosition="3"  />
		<!-- Banner -->
		<widget source="Service" render="GradientBannerXEMC" position="center,620" size="1000,185" zPosition="14" alphatest="blend" />
		<!-- Parental -->
		<widget source="Service" render="GradientParental" position="652,875" size="60,60" alphatest="blend" zPosition="110" transparent="1" />
		<!-- ImdbRating -->
		<widget source="Service" render="GradientStarX" position="497,947" size="220,22" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />

<!-- ================================================== -->
<!-- Movie-EMC-Player INTEGRATION -->
<!-- ================================================== -->
	<!-- Player verwendet auch session.Event_Now -->
		<widget source="session.CurrentService" render="GradientPosterXEMC" position="1580,440" size="204,300" zPosition="4" alphatest="blend" />
		<widget source="session.CurrentService" render="GradientBackdropXEMC" position="23,440" size="569,320" zPosition="1" alphatest="blend" />
		<widget source="session.CurrentService" render="GradientBannerXEMC" position="center,620" size="1000,185" zPosition="4" alphatest="blend" />
		<widget source="session.Event_Now" render="GradientParental" position="1508,701" size="60,60" alphatest="blend" zPosition="5" transparent="1" />
		<widget source="session.Event_Now" render="GradientStarX" position="1580,740" size="204,21" alphatest="blend" zPosition="10" pixmap="icons/starbar_filled.png" backgroundPixmap="icons/starbar_empty.png" />

<!-- ================================================== -->

<!-- WICHTIGE ATTRIBUTE:
- nexts="0" = Aktuelles Event (Standard, kann weggelassen werden)
- nexts="1" = Nächstes Event  
- nexts="2" bis nexts="5" = Events 3-6 (nur bei ServiceEvent verfügbar)
- alphatest="on" = Transparenz-Unterstützung
- position="x,y" = Position in Pixeln
- size="width,height" = Größe in Pixeln -->

<!-- VERFÜGBARE RENDERER:
- GradientPosterX = Poster anzeigen
- GradientBackdropX = Hintergrundbilder 
- GradientParental = FSK/USK Altersbewertungen
- GradientStarX = Sterne-Bewertungen (0-10)
- GradientPosterXEMC = Speziell für EMC/Movies
- GradientBackdropXEMC = Speziell für EMC/Movies
- GradientBannerXEMC = Horizontale Banner/Logos (Nur MovieList/Player) -->

<!-- UNTERSTÜTZTE SOURCES:
- Event = EPG Single Events, EventView
- session.Event_Now = Aktuelles TV-Event (Infobar, Player)
- session.Event_Next = Nächstes TV-Event (Infobar) 
- ServiceEvent = Service-Events (Channellist, bis zu 6 Events)
- Service = Movie/Recording Services (EMC, MovieSelection) -->

<!-- UNIVERSAL KOMPATIBILITÄT:
Alle Renderer sind universal und funktionieren mit ALLEN Sources!
Die Renderer erkennen automatisch den Source-Typ und extrahieren
die entsprechenden Event/Service-Informationen. -->

<!-- ================================================== -->




