#!/usr/bin/python

import decorator
import inspect


def check_signature(signature, **kwd) :
	print "check_signature", signature, kwd

def check_signature2(signature, id, **kwd) :
	print "check_signature2", signature, id, kwd


def require_signature(checker) :
	def decorator(f) :
		checkerfunc = checker
		checkerargs = inspect.getargspec(checker)
		targetargs = inspect.getargspec(f)
		wrapperspec = ", ".join(checkerargs.args + [ inspect.formatargspec(*targetargs)[1:-1] ])
		checkercall = ["%s=%s"%(arg,arg) for arg in checkerargs.args]
		targetcall = ["%s=%s"%(arg,arg) for arg in targetargs.args]
		if targetargs.varargs : targetcall.append("*%s"%targetargs.varargs)
		if targetargs.keywords : targetcall.append("**%s"%targetargs.keywords)
		checkercall=", ".join(checkercall)
		targetcall=", ".join(targetcall)
		source = """\
def wrapper ({wrapperspec}) :
	checkerfunc({checkercall}, {targetcall} )
	return f({targetcall})
""".format(**locals())
		print source
		exec source in locals(), globals()
		return wrapper
	return decorator

@require_signature(check_signature2)
def f(a,b=3, *pos, **kwd) :
	print a, b, pos, kwd

f(signature="boo",id="tu",a=1,b=2,c=3,d=4)
f("boo","tu","a","b",c=3,d=4)


