#!/usr/bin/python

import utils

class GitSandbox(object) :
	def __init__(self, sandbox ) :
		self.sandbox = sandbox

	def state(self) :
		return file("%s/.git/refs/heads/master"%self.sandbox).read().strip()

	def pendingUpdates(self) :
		output = utils.output('cd %(sandbox)s && git log HEAD..origin/master --pretty=oneline'%self.__dict__)
		return [line.split()[0] for line in reversed(output.split('\n')) if line]

	def guilty(self) :
		xml = utils.output("svn --xml log %(sandbox)s -rBASE:HEAD"%self.__dict__)
		log = ET.fromstring(xml)
		return [(
			logentry.get('revision'),
			logentry.find('author').text,
			logentry.find('msg').text,
			) for logentry in log.findall("logentry") ][1:]

	def _pendingChanges(self) :
		xml = utils.output("svn status --xml -u %(sandbox)s "%self.__dict__)
		log = ET.fromstring(xml)
		result = []
		def get(elementOrNot, xmlProperty) :
			return 'none' if elementOrNot is None else elementOrNot.get(xmlProperty, 'none')
		for entry in log.getiterator("entry") :
			lstatus = entry.find("wc-status")
			rstatus = entry.find("repos-status")
			litem = get(lstatus,'item')
			lprop = get(lstatus,'prop')
			ritem = get(rstatus,'item')
			rprop = get(rstatus,'prop')
			result.append( ( entry.get('path'), ( litem, lprop, ritem, rprop)))
		return result

	def hasPendingChanges(self) :
		for path, (litem, lprop, ritem, rprop) in self._pendingChanges() :
			if litem == 'missing' : return True
			if ritem != 'none' : return True
			if rprop != 'none' : return True
		return False


