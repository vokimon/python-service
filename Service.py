#! /usr/bin/env python

import webob
import sys, os
import decorator

class HttpError(Exception) :
	def __init__(self, status, message) :
		self.status = status
		self.message = message

class NotFound(HttpError) :
	def __init__(self, message) :
		HttpError.__init__(self, "404 Not Found", message)

class Forbidden(HttpError) :
	def __init__(self, message) :
		HttpError.__init__(self, "403 Forbidden", message)

class BadRequest(HttpError) :
	def __init__(self, message) :
		HttpError.__init__(self, "400 Bad Request", message)

class query(object) :
	"""Decorator to enhance functions"""
	def __init__(self, content_type='text/plain') :
		self.content_type = content_type

	def __call__(self, f, **kw) :
		f.content_type = self.content_type
		return f
		def wrapper(*args, **kwd) :
			return f(*args, **kwd)
		wrapper.__name__ = f.__name__
		wrapper.__doc__ = f.__doc__
		wrapper.__dict__.update(f.__dict__)
		return wrapper

class Reload:
	""" Module reload middleware """

	def __init__(self, app):
		# TODO: Check is one of our apps
		self.app = app
		self.mtimes = mtimes = {}
		for name in self.app._modules:
			__import__(name)
			moduleFile = sys.modules[name].__file__
			self.mtimes[name] = (
				moduleFile, os.stat(moduleFile).st_mtime)

	def __call__(self, environ, start_response):
		for name, (path, mtime) in self.mtimes.iteritems():
			if os.stat(path).st_mtime == mtime : continue
			print 'Reloading', name, path
			execfile(path, sys.modules[name].__dict__)
			self.mtimes[name] = path, os.stat(path).st_mtime

		return self.app(environ, start_response)

class Service :
	def __init__(self, modules=None) :
		if modules is not None :
			self._modules = modules

	def _webobWrap(f) :
		def wrapper(self, environ, start_response) :
			request = webob.Request(environ)
			# Untested
			if request.charset is None:
				request.charset = 'utf8'
			response = f(self,request)
			return response(environ, start_response)
		return wrapper

	def _handleErrors(f) :
		def wrapper(self, request) :
			try :
				return f(self,request)
			except HttpError, e :
				return webob.Response(
					"%s: %s\n"%(e.__class__.__name__, e.message),
					status = e.status,
					content_type ='text/plain',
					)
			except Exception, e :
				return webob.Response(
					"%s: %s\n"%(e.__class__.__name__, e),
					status = "500 Internal Server Error",
					content_type = 'text/plain',
					)
		return wrapper

	@_webobWrap
	@_handleErrors
	def __call__(self, request):
		""" Handle request """

		moduleName = request.path_info_pop()

		# Not unittested
		if moduleName == 'affero' :
			return webob.Response(
				file(__file__).read(),
				status = "200 OK",
				headers = [
					('Content-Type', 'application/x-python, text/plain') ],
				)

		if moduleName not in self._modules :
			raise NotFound("Bad service %s"%moduleName)

		amodule = __import__(moduleName)

		targetName = request.path_info_pop()

		if not targetName :
			raise BadRequest("Specify a subservice within '%s'"%(
				moduleName))

		if targetName.startswith("_") :
			raise Forbidden("Private object")

		if targetName not in amodule.__dict__ :
			raise NotFound("Bad function %s.%s"%(
				moduleName, targetName))

		target = amodule.__dict__[targetName]

		if target.__class__.__name__ == 'module' :
			raise NotFound("Bad function %s.%s"%(
				moduleName, targetName))

		if not callable(target) :
			return webob.Response(
				str(target),
				content_type = 'text/plain',
				)

		# TODO: Multiple valued
		requestVar = "request"
		paramnames = target.func_code.co_varnames
		hasRequest = requestVar in paramnames and paramnames.index(requestVar)==0
		nDefaults = len(target.func_defaults or ())
		nDeclared = target.func_code.co_argcount
		required = paramnames[1 if hasRequest else 0:nDeclared-nDefaults]
		declared = paramnames[:nDeclared]
		hasKeyword = target.func_code.co_flags & 0x08
		missing = [
			p for p in required
			if p not in request.params
			]
		if missing :
			raise BadRequest("Missing parameters: %s"%(
				", ".join(missing)))
		exceed = [
			p for p in request.params
			if p not in declared 
			]
		if hasRequest and requestVar in request.params :
			raise BadRequest("Unavailable parameter: %s"%requestVar)
		if exceed and not hasKeyword:
			raise BadRequest("Unavailable parameter: %s"%(
				", ".join(exceed)))

		if hasRequest :
			responseBody = target(request=request, **request.params)
		else :
			responseBody = target(**request.params)

		return webob.Response(
			responseBody,
			content_type = getattr(target, 'content_type', 'text/plain'),
			)



if __name__=="__main__" :
	services = sys.argv[1:] or ["TestingService"]
	application = Reload(Service(services))

	print "Loading server"
	from wsgiref.simple_server import make_server
	httpd = make_server(
		'localhost', # Host name.
		8051, # port
		application, # application object
		)
	httpd.serve_forever()


