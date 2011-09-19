#!/usr/bin/python

import urllib, urllib2
import urlparse
import HttpFormPost
import sys

Proxies = { 'http' : 'http://proxy.upf.edu:8080', 'ftp' : 'http://proxy.upf.edu:8080' }
NoProxiesFor = ["localhost", "127.0.0.1", "10.55.0.40"]
useragent = 'simac-services-stub'

class ServiceStub :
	def __init__(self, serviceLocation, proxies=Proxies) :
		self.serviceUrl = serviceLocation
		self.proxies = proxies
		if urlparse.urlparse (self.serviceUrl)[1] in NoProxiesFor :
			self.proxies={}
		self.proxies = {}
		self.proxy_support = urllib2.ProxyHandler( self.proxies )

	def remoteCall(self, serviceName, **fields):
		opener = urllib2.build_opener( self.proxy_support )
		urllib2.install_opener(opener)

		try:
			content_type, body = HttpFormPost.encode_multipart_formdata_dictionary(fields)
			headers = {
				'User-Agent': useragent,
				'Content-Type': content_type,
				}
			req=urllib2.Request(
				self.serviceUrl+"/"+serviceName, body, headers)
			result= urllib2.urlopen(req).read()
			return result
		except Exception, msg:
			raise Exception( "ERROR GETTING DATA FROM SERVICE: %s\n%s" % (msg,sys.exc_info()))


class ContentLocator(ServiceStub) :
	def LocateId(self, id) :
		return self.remoteCall( "LocateId", id=id )

	def IdentifyUrl(self, url) :
		return self.remoteCall( "IdentifyUrl", url=url )

	def AddUrl(self, url) :
		return self.remoteCall( "AddUrl", url=url )


class MetadataProvider(ServiceStub) :
	def QueryIdByUrl(self, url) :
		return self.remoteCall( "QueryIdByUrl", url=url )

	def QuerySchema(self, descriptors) :
		return self.remoteCall( "QuerySchema", descriptors=descriptors )

	def QueryDescriptors(self, id, descriptors) :
		return self.remoteCall( "QueryDescriptors", id=id, descriptors=descriptors)

	def UploadPackedDescriptors(self, file) :
		return self.remoteCall( "UploadPackedDescriptors", packedpoolfile=open(file, 'rb') )

	def AvailableDescriptors(self, source=None) :
		if source == None:
			return self.remoteCall("AvailableDescriptors")
		else:
			return self.remoteCall("AvailableDescriptors", source=source)
	
	def CheckMissingDescriptors(self, ids, descriptors=None):
		if descriptors==None:
			return self.remoteCall("CheckMissingDescriptors",ids=ids)	
		else:
			return self.remoteCall("CheckMissingDescriptors",ids=ids, descriptors=descriptors)

	def GetSimilarIds(self, id, count="20"):
		return self.remoteCall("GetSimilarIds",id=id, count=count)



if __name__ == "__main__" :
	webservice = ServiceStub("http://localhost:8051/ContentLocator")
	print webservice.remoteCall("Version")
	print webservice.remoteCall("LocateId", id="4871335")
	print webservice.remoteCall("LocateId", id=["4871335","lala"])
	print webservice.remoteCall("_private")
#	print webservice.remoteCall("LocateId", id=open(__file__,'rb'))
#	print webservice.remoteCall("LocateId", id=open("/home/vokimon/0002.jpg",'rb'))
	

	"""
	contentLocator = ContentLocator("https://localhost/ContentLocator")
	print contentLocator.LocateId(24), "should be 'NotFound'"
	print contentLocator.LocateId(4871335), "should be 'http://www.threegutrecords.com/mp3/Is This It.mp3\n'"
	print contentLocator.IdentifyUrl("http://www.threegutrecords.com/mp3/Is This It.mp3") , "should be '4871335'"
	print contentLocator.AddUrl("http://www.threegutrecords.com/mp3/Is This It.mp3"), "should be '4871335'"
	
	metadataProvider = MetadataProvider("https://localhost/MetadataProvider")
	print metadataProvider.QueryIdByUrl("http://www.threegutrecords.com/mp3/Is This It.mp3"), "should be '4871335'"
	"""
