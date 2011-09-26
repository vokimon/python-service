#!/usr/bin/python

import decorator
import inspect


def check_signature(signature, **kwd) :
	print "check_signature", signature, kwd

def check_signature2(signature, id, **kwd) :
	print "check_signature2", signature, id, kwd


def expand_decorator(checker) :
	def decorator(f) :
		checkerfunc = checker
		checkerargs = inspect.getargspec(checker)
		targetargs = inspect.getargspec(f)
		# TODO: checker with optional
		wrapperspec = ", ".join(
			[arg for arg in checkerargs.args if arg not in targetargs.args] + 
			[ inspect.formatargspec(*targetargs)[1:-1] ])
		targetcall = ["%s=%s"%(arg,arg) for arg in targetargs.args]
		checkercall = targetcall+["%s=%s"%(arg,arg) for arg in checkerargs.args]
		if targetargs.varargs : targetcall.append("*%s"%targetargs.varargs)
		if targetargs.keywords : targetcall.append("**%s"%targetargs.keywords)
		checkercall=", ".join(checkercall)
		targetcall=", ".join(targetcall)
		source = """\
def wrapper ({wrapperspec}) :
#	print "wrapper locals", locals()
	checkerfunc({checkercall})
	return f({targetcall})
""".format(**locals())
		exec source in locals(), globals()
		return wrapper
	return decorator

if __name__ == "__main__" :
		@expand_decorator(check_signature2)
		def f(a,b=3, *pos, **kwd) :
			print a, b, pos, kwd

		f(signature="boo",id="tu",a=1,b=2,c=3,d=4)
		f("boo","tu","a","b",c=3,d=4)


