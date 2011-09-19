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

	@decorator.decorator
	def catchErrors(f, self, environ, start_response) :
		try :
			return f(self, environ, start_response)
		except HttpError, e :
			start_response(
				status = e.status,
				headers = [
					('Content-Type', 'text/plain'),
				],
			)
			return "%s: %s\n"%(e.__class__.__name__, e.message)
		except Exception, e :
			start_response(
				status = "500 Internal Server Error",
				headers = [
					('Content-Type', 'text/plain'),
				],
			)
			return "%s: %s\n"%(
				e.__class__.__name__, e)

	@catchErrors
	def __call__(self, environ, start_response):
		""" Handle wsgi request """
		request = webob.Request(environ)
		# Untested
		if request.charset is None:
			request.charset = 'utf8'

		moduleName = request.path_info_pop()

		if moduleName == 'affero' :
			start_response(
				status = "200 OK",
				headers = [ ('Content-Type', 'application/x-python, text/plain') ],
			)
			return file(__file__).read()

		if moduleName not in self._modules :
			raise NotFound("Bad service %s"%moduleName)
		amodule = __import__(moduleName)

		targetName = request.path_info_pop()

		if targetName.startswith("_") :
			raise Forbidden("Private object")

		if targetName not in amodule.__dict__ :
			raise NotFound("Bad function %s.%s"%(
				moduleName, targetName))
		target = amodule.__dict__[targetName]
		if target.__class__.__name__ == 'module' :
			raise NotFound("Bad function %s.%s"%(
				moduleName, targetName))

		if callable(target) :
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
				result = target(request=request, **request.params)
			else :
				result = target(**request.params)
			content_type = getattr(target, 'content_type', 'text/plain')
		else :
			result = target
			content_type = 'text/plain'

		start_response(
			status = "200 OK",
			headers = [ ('Content-Type', content_type) ],
		)
		return str(result)


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


