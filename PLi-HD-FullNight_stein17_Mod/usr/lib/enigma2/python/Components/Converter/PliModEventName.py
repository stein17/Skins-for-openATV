# based on EventName.py from VTI 4.1
# Copy to /usr/lib/enigma2/python/Components/Converter/
from __future__ import absolute_import
from Components.Converter.Converter import Converter
from Components.Element import cached

class PliModEventName(Converter, object):
	NAME = 0					# return Name of Event, i.e. Title
	SHORT_DESCRIPTION = 1		# return Short Description of Event. This is often the title of a series or gives extra information about an event
	EXTENDED_DESCRIPTION = 2	# return Extended Description, i.e., a long text describing the content of the event
	ID = 3						# return the ID of the event
	BOTH_DESCRIPTIONS = 4		# return Short Description and Extended Description separated by a blank line. If there is no Short Description defined,
								#	 only Extended Description is returned without leading blank line.
	BOTH_DESCRIPTIONS_FILTERED = 5 # like 4, but result does not contain Short Description if it is equal to the name of the event.
	NAME_AND_SHORT_DESC_FILTERED = 6 # returns Name and Short Description, if Short Description is not equal the Name. If it is equal, only returns Title.
	
	def __init__(self, type):
		_type = type
		Converter.__init__(self, _type)
		if _type == "Description":
			self.type = self.SHORT_DESCRIPTION
		elif _type == "ExtendedDescription":
			self.type = self.EXTENDED_DESCRIPTION
		elif _type == "ID":
			self.type = self.ID
		elif _type == "BothDescriptions":
			self.type = self.BOTH_DESCRIPTIONS
		elif _type == "BothDescriptionsFiltered":
			self.type = self.BOTH_DESCRIPTIONS_FILTERED
		elif _type == "NameAndShortDescFiltered":
			self.type = self.NAME_AND_SHORT_DESC_FILTERED
		else:
			self.type = self.NAME

	@cached
	def getText(self):
		event = self.source.event
		if event is None:
			return ""
		
		if self.type == self.NAME:
			return event.getEventName()
		elif self.type == self.SHORT_DESCRIPTION:
			return event.getShortDescription()
		elif self.type == self.EXTENDED_DESCRIPTION:
			return event.getExtendedDescription()		
		elif self.type == self.BOTH_DESCRIPTIONS:
			desc = event.getShortDescription() or ""
			if desc != "":
				desc = desc + '\n\n'
			desc = desc + event.getExtendedDescription() or ""
			return desc
		elif self.type == self.BOTH_DESCRIPTIONS_FILTERED:
			name = event.getEventName() or ""
			desc = event.getShortDescription() or ""
			if name == desc:
			   desc = ""
			if desc != "":
				desc = desc + '\n\n'
			desc = desc + event.getExtendedDescription() or ""
			return desc
		elif self.type == self.NAME_AND_SHORT_DESC_FILTERED:
			name = event.getEventName() or ""
			desc = event.getShortDescription() or ""
			if name == desc:
			   desc = ""
			if desc != "":
				name = name + ' - ' + desc or ""
			return name
		elif self.type == self.ID:
			return str(event.getEventId())
		
	text = property(getText)
