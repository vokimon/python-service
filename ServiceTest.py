#!/usr/bin/python

_serviceCode = """\
#!/usr/bin/python

import sys # not used, just to try to call it

Protocol="TestingProtocol"
_private = "Private content"
Numeric = 13

def Function0() :
	return "Function0 content"

def Function0_html() :
	return "Function0_html <b>content</b>"
Function0_html.content_type = 'text/html'

def ErrorFunction() :
	return [][0]

def Function1(param1) :
	return "param1 = %s"%param1

def Function1Optional(param1="defaultValue") :
	return "param1 = %s"%param1

def FunctionKeyword(**kwd) :
	return str(kwd)

def FunctionPositional(a, *b) :
	return "a = '%s'\\nargs = %s"%(a,b)

def FunctionRequest(request, a, b) :
	return request.method

def FunctionRequestKeyword(request, **kwd) :
	return request.method


"""

import wsgi_intercept.urllib2_intercept
import unittest
import urllib2
import HttpFormPost
import os

class ServiceTest(unittest.TestCase) :

	def setUp(self) :
		source = open("TestingService.py",'w')
		source.write(_serviceCode)
		source.close()
		del source
		import Service
		self.app = Service.Reload(Service.Service([
			"TestingService",
			]))
		def createApp() : return self.app
		wsgi_intercept.urllib2_intercept.install_opener()
		wsgi_intercept.add_wsgi_intercept('myhost', 80, createApp)


	def tearDown(self) :
		wsgi_intercept.urllib2_intercept.uninstall_opener()
		os.unlink("TestingService.py")
		if os.path.exists("TestingService.pyc") :
			os.unlink("TestingService.pyc")

	def request(self, query, postdata=None) :
		body = None
		headers = {}
		if postdata is not None :
			content_type, body = HttpFormPost.encode_multipart_formdata_dictionary(postdata)
			headers['Content-Type'] = content_type
		req=urllib2.Request('http://myhost:80/'+query, body, headers)
		return urllib2.urlopen(req)

	def assertContent(self, query, body=None, headers=None, post=None) :
		try :
			req = self.request(query, post)
			if body is not None :
				self.assertEquals(body, req.read())
			if headers is not None :
				self.assertEquals(headers, str(req.headers))
		except urllib2.HTTPError, e :
			print e.read()
			raise

	def assertError(self, query, code, body=None, headers=None, post=None) :
		try :
			res = self.request(query, post)
			self.fail("HTTP error expected. Received '%s'"%res.read())
		except urllib2.HTTPError,e :
			if body is not None :
				self.assertEquals(body, e.read())
			self.assertEquals(code, e.getcode())
			if headers is not None:
				self.assertEquals(headers, str(e.headers))



	def testMissingModule(self) :
		self.assertError(
			'BadModule/Protocol',
			code = 404,
			body = "NotFound: Bad service BadModule\n",
			headers = "Content-Type: text/plain\n",
			)

	def testMissingTarget(self) :
		self.assertError(
			'TestingService/MissingTarget',
			code = 404,
			body = "NotFound: Bad function TestingService.MissingTarget\n",
			headers = "Content-Type: text/plain\n",
			)

	def testGetAttributes(self) :
		self.assertContent(
			'TestingService/Protocol',
			body="TestingProtocol",
			)

	def testGetAttributes_defaultsToPlainText(self) :
		self.assertContent(
			'TestingService/Protocol',
			headers = "Content-Type: text/plain\n",
			)

	def testPrivateObject(self) :
		self.assertError(
			'TestingService/_private',
			code = 403,
			body = "Forbidden: Private object\n",
			headers = "Content-Type: text/plain\n",
			)

	def testNumericAttribute(self) :
		self.assertContent(
			"TestingService/Numeric",
			'13')

	def testModule_failsNotFound(self) :
		self.assertError(
			'TestingService/sys',
			code = 404,
			body = "NotFound: Bad function TestingService.sys\n",
			headers = "Content-Type: text/plain\n",
			)

	def testFunction0(self) :
		self.assertContent(
			"TestingService/Function0",
			'Function0 content',
			headers = "Content-Type: text/plain\n",
			)

	def testFunction0_html(self) :
		self.assertContent(
			"TestingService/Function0_html",
			'Function0_html <b>content</b>',
			headers = "Content-Type: text/html\n",
			)

	def testErrorFunction0_html(self) :
		self.assertError(
			"TestingService/ErrorFunction",
			500,
			'IndexError: list index out of range\n',
			)

	def testFunction1_withNoParams(self) :
		self.assertError(
			"TestingService/Function1",
			400,
			'BadRequest: Missing parameters: param1\n',
			headers = "Content-Type: text/plain\n",
			)

	def testFunction1_usingGet(self) :
		self.assertContent(
			"TestingService/Function1?param1=value1",
			body = 'param1 = value1',
			headers = "Content-Type: text/plain\n",
			)

	def testFunction1_usingMultipleGet_lastWins(self) :
		self.assertContent(
			"TestingService/Function1?param1=value1&param1=value2",
			body = 'param1 = value2',
			headers = "Content-Type: text/plain\n",
			)

	def testFunction1_usingPost(self) :
		self.assertContent(
			"TestingService/Function1",
			post = dict(param1='post value'),
			body = 'param1 = post value',
			headers = "Content-Type: text/plain\n",
			)

	def testFunction1_usingPostAndUri_getWins(self) :
		self.assertContent(
			"TestingService/Function1?param1=get",
			post = dict(param1='post'),
			body = 'param1 = get',
			headers = "Content-Type: text/plain\n",
			)

	def testFunction0_withParams(self) :
		self.assertError(
			"TestingService/Function0?param=value",
			400,
			'BadRequest: Unavailable parameter: param\n',
			headers = "Content-Type: text/plain\n",
			)

	def testFunction1Optional_withoutTheParam(self) :
		self.assertContent(
			"TestingService/Function1Optional",
			body = 'param1 = defaultValue',
			headers = "Content-Type: text/plain\n",
			)

	def testFunctionKeyword_withoutParams(self) :
		self.assertContent(
			"TestingService/FunctionKeyword",
			body = '{}',
			headers = "Content-Type: text/plain\n",
			)

	def testFunctionKeyword_withParams(self) :
		self.assertContent(
			"TestingService/FunctionKeyword?a=1&b=2",
			body = "{'a': u'1', 'b': u'2'}",
			headers = "Content-Type: text/plain\n",
			)

	def testFunctionPositional(self) :
		self.assertContent(
			"TestingService/FunctionPositional?a=1",
			body = "a = '1'\nargs = ()",
			headers = "Content-Type: text/plain\n",
			)

	def testFunctionPositional_withExtraParam(self) :
		self.assertError(
			"TestingService/FunctionPositional?a=1&c=2",
			code = 400,
			body = "BadRequest: Unavailable parameter: c\n",
			headers = "Content-Type: text/plain\n",
			)

	def testFunctionPositional_withExtraParamNamedLikeThePositional(self) :
		self.assertError(
			"TestingService/FunctionPositional?a=1&b=2",
			code = 400,
			body = "BadRequest: Unavailable parameter: b\n",
			headers = "Content-Type: text/plain\n",
			)

	def testFunctionRequest(self) :
		self.assertContent(
			"TestingService/FunctionRequest?a=1&b=2",
			body = "GET",
			headers = "Content-Type: text/plain\n",
			)

	def testFunctionRequest_requestHijack(self) :
		self.assertError(
			"TestingService/FunctionRequest?a=1&b=2&request='hijack'",
			400,
			body = "BadRequest: Unavailable parameter: request\n",
			headers = "Content-Type: text/plain\n",
			)

	def testFunctionRequest(self) :
		self.assertContent(
			"TestingService/FunctionRequestKeyword?a=1&b=2",
			body = "GET",
			headers = "Content-Type: text/plain\n",
			)

	def testFunctionRequestKeyword_requestHijack(self) :
		self.assertError(
			"TestingService/FunctionRequestKeyword?request='hijack'",
			400,
			body = "BadRequest: Unavailable parameter: request\n",
			headers = "Content-Type: text/plain\n",
			)

	def testReload(self) :
		import time
		script = "TestingService.py"
		self.request("TestingService/Function0").read()
		creationtime = os.stat(script).st_mtime
		while True : # mtime has just one second of resolution
			source = open(script,'w')
			source.write(
				"print 'Loading'\n"
				"def Function0() : return 'Reloaded!!'\n"
				)
			source.close()
			if os.stat(script).st_mtime != creationtime : break

		self.assertContent(
			"TestingService/Function0",
			body = "Reloaded!!",
			headers = "Content-Type: text/plain\n",
			)

if __name__=="__main__" :
	unittest.main()


