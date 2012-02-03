#!/usr/bin/python

#import elementtree.ElementTree as ET
#import cElementTree as ET
#import lxml.etree as ET
import xml.etree.ElementTree as ET # Python 2.5
import utils


class Subversion(object) :
	def __init__(self, sandbox ) :
		self.sandbox = sandbox

	def state(self) :
		return utils.output("svn info %(sandbox)s | grep ^Revision: "%self.__dict__).split()[-1]

	def pendingCommits(self) :
		xml = utils.output("svn --xml log %(sandbox)s -rBASE:HEAD"%self.__dict__)
		log = ET.fromstring(xml)
		return [logentry.get('revision') for logentry in log.findall("logentry") ][1:]
	def guilty(self) :
		xml = utils.output("svn --xml log %(sandbox)s -rBASE:HEAD"%self.__dict__)
		log = ET.fromstring(xml)
		print xml
		return [(
			logentry.get('revision'),
			logentry.find('author').text,
			logentry.find('msg').text,
			) for logentry in log.findall("logentry") ][1:]
	def pendingChanges(self) :
		xml = utils.output("svn status --xml -u %(sandbox)s "%self.__dict__)
		log = ET.fromstring(xml)
		print xml
		result = []
		for entry in log.getiterator("entry") :
			wcstatus = entry.find("wc-status")
			print wcstatus
			wcstatus = ",".join([wcstatus.get('item'), wcstatus.get('props')]) if wcstatus else ","
			print wcstatus
			repostatus = entry.find("repo-status")
			print repostatus
			repostatus = ",".join([repostatus.get('item'), repostatus.get('props')]) if repostatus else ","
			print repostatus
		return [(
			entry.get('path'),
			entry.find('repos-status').get("item") if entry.find('repos-status') else "",
			entry.find('repos-status').get("props") if entry.find('repos-status') else "",
			entry.find('wc-status').get("item") if entry.find('wc-status') else "",
			entry.find('wc-status').get("props") if entry.find('wc-status') else "",
			) for entry in log.getiterator("entry") ]

import os
import unittest

class SubversionTest(unittest.TestCase) :
	def x(self, command) :
		return utils.run(command%self.defs)
	def addFile(self, file) :
		self.x('touch %%(sandbox)s/%s'%file)
		self.x('svn add %%(sandbox)s/%s'%file)
		self.x('svn commit %%(sandbox)s/%s -m"added %s"'%(file,file))

	def addRevisions(self, file, n) :
		for i in xrange(n) :
			self.x('echo Change %s >> %%(sandbox)s/%s'%(i,file))
			self.x('svn commit %%(sandbox)s/%s -m"change %i of %s"'%(file,i,file))

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
		self.x('svn log %(sandbox)s')
		self.x('rm -rf %(testdir)s')

	def _test_state(self) :
		self.addFile('file')
		self.addRevisions('file',3)
		s = Subversion(self.defs['sandbox'])
		self.assertEquals('0', s.state())
		self.x('svn up %(sandbox)s') # go to HEAD
		self.assertEquals('4', s.state())
		self.x('svn up -r1 %(sandbox)s') # go to r1
		self.assertEquals('1', s.state())

	def _test_pendingCommits(self) :
		self.addFile('file')
		self.addRevisions('file',3)
		self.x('svn up -r1 %(sandbox)s') # go to r1
		s = Subversion(self.defs['sandbox'])
		self.assertEquals(
			['2','3','4'], s.pendingCommits())

	def _test_guilty(self) :
		self.addFile('file')
		self.addRevisions('file',3)
		self.x('svn up -r1 %(sandbox)s') # go to r1
		s = Subversion(self.defs['sandbox'])
		self.assertEquals(
			[
				('2','myuser',"change 0 of file"),
				('3','myuser',"change 1 of file"),
				('4','myuser',"change 2 of file"),
			], s.guilty())

	def test_pendingChanges(self) :
		self.addFile('file')
		self.addRevisions('file',3)
		self.x('svn up -r1 %(sandbox)s') # go to r1
		self.x('touch %(sandbox)s/added')
		self.x('svn add %(sandbox)s/added')
		self.x('touch %(sandbox)s/notadded')
		s = Subversion(self.defs['sandbox'])
		self.assertEquals(
			[
				('2','myuser',"change 0 of file"),
				('3','myuser',"change 1 of file"),
				('4','myuser',"change 2 of file"),
			], s.pendingChanges())


if __name__ == '__main__' :
	unittest.main()


