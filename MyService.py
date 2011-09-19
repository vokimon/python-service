#! /usr/bin/env python

import cgi
import Service

print "Loading MyService"


Version = "0.1"
Protocol = "ServiceTesting"

def _private() :
	raise Exception("Running a private!!")

@Service.query(content_type="text/plain")
def LocateId(request, id=None):
	if isinstance(id, cgi.FieldStorage) :
		return id.file.read()
	return "Mi id is {id}".format(id=id)

@Service.query(content_type="image/jpg")
def Image(request, id=None):
	return file("/home/vokimon/0002.jpg").read()
	return file("/home/vokimon/tux-rocker.png").read()
	return file("/home/vokimon/Rayuela0068.jpg").read()

def forceError(request) :
	raise Service.NotFound("lala")
	
def requestless(req, ) :
	return "Ok '%s'"%b


