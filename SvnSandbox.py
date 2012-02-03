#!/usr/bin/python

import xml.etree.cElementTree as ET
#import xml.etree.ElementTree as ET # Python 2.5
import utils


class SvnSandbox(object) :
	def __init__(self, sandbox ) :
		self.sandbox = sandbox

	def state(self) :
		xml = utils.output("svn --xml info %(sandbox)s"%self.__dict__)
		info = ET.fromstring(xml)
		return info.find("entry").get('revision')
		# text based implementation (needs LANG and risky)
		return utils.output("LANG=C svn info %(sandbox)s | grep ^Revision: "%self.__dict__).split()[-1]

	def pendingUpdates(self) :
		xml = utils.output("svn --xml log %(sandbox)s -rBASE:HEAD"%self.__dict__)
		log = ET.fromstring(xml)
		return [logentry.get('revision') for logentry in log.findall("logentry") ][1:]

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

import os
import unittest

class SvnSandboxTest(unittest.TestCase) :
	def x(self, command) :
		return utils.run(command%self.defs)
	def inSandbox(self, file) :
		return os.path.join(self.defs['sandbox'],file)
	def addFile(self, file, commit=True) :
		self.x('touch %%(sandbox)s/%s'%file)
		self.x('svn add %%(sandbox)s/%s'%file)
		if commit :
			self.x('svn commit %%(sandbox)s/%s -m"added %s"'%(file,file))
	def removeFile(self, file, commit=True) :
		self.x('svn rm %%(sandbox)s/%s'%file)
		if commit :
			self.x('svn commit %%(sandbox)s/%s -m"removed %s"'%(file,file))
	def addRevisions(self, file, n, commit=True) :
		for i in xrange(n) :
			self.x('echo Change %s >> %%(sandbox)s/%s'%(i,file))
			if commit :
				self.x('svn commit %%(sandbox)s/%s -m"change %i of %s"'%(file,i,file))
	def commitAll(self, message) :
		self.x('svn commit %%(sandbox)s/ -m"%s"'%(message))
		

	def setUp(self) :
		self.defs = dict(
			username = "myuser",
			testdir = os.path.join(os.getcwd(),'testdir'),
			repo    = os.path.join(os.getcwd(),'testdir/repo'),
			sandbox = os.path.join(os.getcwd(),'testdir/sandbox1'),
			)
		self.x('rm -rf %(testdir)s')
		self.x('mkdir -p %(testdir)s')
		self.x('svnadmin create %(repo)s')
		self.x('svn co --username %(username)s file://%(repo)s %(sandbox)s')

	def tearDown(self) :
		""" """
#		self.x('svn log %(sandbox)s')
		self.x('rm -rf %(testdir)s')

	def test_state(self) :
		self.addFile('file')
		self.addRevisions('file',3)
		s = SvnSandbox(self.defs['sandbox'])
		self.assertEquals('0', s.state())
		self.x('svn up %(sandbox)s') # go to HEAD
		self.assertEquals('4', s.state())
		self.x('svn up -r1 %(sandbox)s') # go to r1
		self.assertEquals('1', s.state())

	def test_pendingCommits(self) :
		self.addFile('file')
		self.addRevisions('file',3)
		self.x('svn up -r1 %(sandbox)s') # go to r1
		s = SvnSandbox(self.defs['sandbox'])
		self.assertEquals(
			['2','3','4'], s.pendingUpdates())

	def test_guilty(self) :
		self.addFile('file')
		self.addRevisions('file',3)
		self.x('svn up -r1 %(sandbox)s') # go to r1
		s = SvnSandbox(self.defs['sandbox'])
		self.assertEquals(
			[
				('2','myuser',"change 0 of file"),
				('3','myuser',"change 1 of file"),
				('4','myuser',"change 2 of file"),
			], s.guilty())

	def test_pendingChanges(self) :
		self.addFile('remoteChange', False)
		self.addFile('remoteRemove', False)
		self.addFile('localRemove', False)
		self.addFile('localChange', False)
		self.addFile('nonsvnRemove', False)
		self.commitAll("State were we want to go back")

		self.addRevisions('remoteChange',1, False)
		self.addFile('remoteAdd', False)
		self.removeFile('remoteRemove', False)
		self.commitAll("State we want to update to")
		self.x('svn up -r1 %(sandbox)s') # going back

		# local modifications
		self.addRevisions('localChange', 1, False)
		self.removeFile('localRemove', False)
		self.addFile('localAdd', False)
		self.x('echo nonsvnAdd > %(sandbox)s/nonsvnAdd')
		self.x('rm %(sandbox)s/nonsvnRemove')

		s = SvnSandbox(self.defs['sandbox'])
		self.maxDiff = None
		self.assertEquals(
			[
				(self.defs['sandbox'],           ('normal', 'none', 'modified', 'none')),
				(self.inSandbox('localAdd'),     ('added', 'none', 'none', 'none')),
				(self.inSandbox('localChange'),  ('modified', 'none', 'none', 'none')),
				(self.inSandbox('localRemove'),  ('deleted', 'none', 'none', 'none')),
				(self.inSandbox('nonsvnAdd'),    ('unversioned', 'none', 'none', 'none')),
				(self.inSandbox('nonsvnRemove'), ('missing', 'none', 'none', 'none')),
				(self.inSandbox('remoteAdd'),    ('none', 'none', 'added', 'none')),
				(self.inSandbox('remoteChange'), ('normal', 'none', 'modified', 'none')),
				(self.inSandbox('remoteRemove'), ('normal', 'none', 'deleted', 'none')),

			], sorted(s._pendingChanges()))

	def test_hasPendingChanges_whenNoPendingChanges(self) :
		self.addFile('remoteChange', False)
		self.addFile('remoteRemove', False)
		self.addFile('localRemove', False)
		self.addFile('localChange', False)
		self.addFile('nonsvnRemove', False)
		self.commitAll("State were we want to go back")

		s = SvnSandbox(self.defs['sandbox'])
		self.assertFalse(s.hasPendingChanges())

	def test_hasPendingChanges_whenMissingFile(self) :
		self.addFile('nonsvnRemove')
		self.x('rm %(sandbox)s/nonsvnRemove')

		s = SvnSandbox(self.defs['sandbox'])
		self.assertTrue(s.hasPendingChanges())

	def test_hasPendingChanges_whenPendingModification(self) :
		self.addFile('remoteChange')
		self.addRevisions('remoteChange',1)
		self.x('svn up -r1 %(sandbox)s') # going back

		s = SvnSandbox(self.defs['sandbox'])
		self.assertTrue(s.hasPendingChanges())

	def test_hasPendingChanges_whenPendingRemove(self) :
		self.addFile('remoteRemove')
		self.removeFile('remoteRemove')
		self.x('svn up -r1 %(sandbox)s') # going back

		s = SvnSandbox(self.defs['sandbox'])
		self.assertTrue(s.hasPendingChanges())

	def test_hasPendingChanges_whenPendingAdd(self) :
		self.addFile('remoteAdd')
		self.x('svn up -r0 %(sandbox)s') # going back

		s = SvnSandbox(self.defs['sandbox'])
		self.assertTrue(s.hasPendingChanges())

	def test_hasPendingChanges_whenLocalChanges(self) :
		self.addFile('localRemove', False)
		self.addFile('localChange', False)
		self.commitAll("State were we want to go back")

		# any local modifications (but non-svn deletion)
		self.addRevisions('localChange', 1, False)
		self.removeFile('localRemove', False)
		self.addFile('localAdd', False)
		self.x('echo nonsvnAdd > %(sandbox)s/nonsvnAdd')

		s = SvnSandbox(self.defs['sandbox'])
		self.maxDiff = None
		self.assertFalse(s.hasPendingChanges())


if __name__ == '__main__' :
	unittest.main()


