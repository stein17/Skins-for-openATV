
maintype = [_('Reserved'),
 _('Movie/Drama'),
 _('News Current Affairs'),
 _('Show Games show'),
 _('Sports'),
 _('Children/Youth'),
 _('Music/Ballet/Dance'),
 _('Arts/Culture'),
 _('Social/Political/Economics'),
 _('Education/Science/...'),
 _('Leisure hobbies'),
 _('Other')]
subtype = {}
subtype[1] = [_('Movie'),
 _('Detective'),
 _('Adventure'),
 _('Science'),
 _('Comedy'),
 _('Serie'),
 _('Romance'),
 _('Serious'),
 _('Adult')]
subtype[2] = [_('News'),
 _('Weather'),
 _('Magazine'),
 _('Docu'),
 _('Disc')]
subtype[3] = [_('Show'),
 _('Quiz'),
 _('Variety'),
 _('Talk')]
subtype[4] = [_('Sports'),
 _('Special'),
 _('Sports Magazine'),
 _('Football'),
 _('Tennis'),
 _('Team Sports'),
 _('Athletics'),
 _('Motor Sport'),
 _('Water Sport'),
 _('Winter Sport'),
 _('Equestrian'),
 _('Martial Sports')]
subtype[5] = [_("Childrens"),
 _("Children"),
 _('(6-14)'),
 _('(10-16)'),
 _('Information'),
 _('Cartoon')]
subtype[6] = [_('Music'),
 _('Rock/Pop'),
 _('Classic Music'),
 _('Folk'),
 _('Jazz'),
 _('Musical/Opera'),
 _('Ballet')]
subtype[7] = [_('Arts'),
 _('Performing Arts'),
 _('Fine Arts'),
 _('Religion'),
 _('PopCulture'),
 _('Literature'),
 _('Cinema'),
 _('ExpFilm'),
 _('Press'),
 _('New Media'),
 _('Culture'),
 _('Fashion')]
subtype[8] = [_('Social'),
 _('Magazines'),
 _('Economics'),
 _('Remarkable People')]
subtype[9] = [_('Education'),
 _('Nature/Animals/'),
 _('Technology'),
 _('Medicine'),
 _('Expeditions'),
 _('Social'),
 _('Further Education'),
 _('Languages')]
subtype[10] = [_('Hobbies'),
 _('Travel'),
 _('Handicraft'),
 _('Motoring'),
 _('Fitness'),
 _('Cooking'),
 _('Shopping'),
 _('Gardening')]
subtype[11] = [_('Original Language'),
 _('Black & White'),
 _('Unpublished'),
 _('Live Broadcast')]

def getGenreStringMain(hn, ln):
	if hn == 15:
		return _('User defined')
	if 0 < hn < len(maintype):
		return maintype[hn]
	return ''

def getGenreStringSub(hn, ln):
	if 0 < hn < len(maintype):
		if ln < len(subtype[hn]):
			return subtype[hn][ln]
	return ''

