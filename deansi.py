#!/usr/bin/python

# http://en.wikipedia.org/wiki/ANSI_escape_code
# TODO: Support disable codes: 20 + attribCodes
# TODO: Support 39 and 49 (set default color and bgcolor)
# TODO: Support 38 and 38 (next attrib is a 256 palette color (xterm?))
# TODO: Support 51-55 decorations (framed, encircled, overlined, no frame/encircled, no overline)

import re
import cgi

colorCodes = {
	0 : 'black',
	1 : 'red',
	2 : 'green',
	3 : 'yellow',
	4 : 'blue',
	5 : 'magenta',
	6 : 'cyan',
	7 :	'white',
}
attribCodes = {
	1 : 'bright',
	2 : 'faint',
	3 : 'italic',
	4 : 'underscore',
	5 : 'blink',
# TODO: Chek that 6 is ignored on enable and disable or enable it
#	6 : 'blink_rapid',
	7 : 'reverse',
	8 : 'hide',
	9 : 'strike',
}
def defaultAnsiStyle() :
	return """\
.ansi_terminal {  }
.ansi_black { color: black; }
.ansi_red { color: red; }
.ansi_green { color: green; }
.ansi_yellow { color: yellow; }
.ansi_blue { color: blue; }
.ansi_magenta { color: magenta; }
.ansi_cyan { color: cyan; }
.ansi_white { color: white; }
.ansi_bgblack { background-color: black; }
.ansi_bgred { background-color: red; }
.ansi_bggreen { background-color: green; }
.ansi_bgyellow { background-color: yellow; }
.ansi_bgblue { background-color: blue; }
.ansi_bgmagenta { background-color: magenta; }
.ansi_bgcyan { background-color: cyan; }
.ansi_bgwhite { background-color: white; }
.ansi_bright { font-weight: bold; }
.ansi_faint { opacity: 80%; }
.ansi_italic { font-style: italic; }
.ansi_underscore { text-decoration: underline; }
.ansi_blink { text-decoration: blink; }
.ansi_reverse { border: 1pt solid; }
.ansi_hide { opacity: 0%; }
.ansi_strike { text-decoration: line-through; }
"""

def ansiAttributes(block) :
	"""Extracts ansi attribute codes XX from the begining [XX;XX;XXm and the rest of the text"""

	attributeRe = re.compile( r'^[[](\d+(?:;\d+)*)m(.*)')
	match = attributeRe.match(block)
	if not match : return [], block
	return [int(code) for code in match.group(1).split(";")], match.group(2)


def ansiState(code, attribs, fg, bg) :
	"""Keeps track of the ansi attribute state given a new code"""

	if code == 0 : return set(), None, None
	if code in xrange(30,38) :
		return attribs, colorCodes[code-30], bg
	if code in xrange(40,48) :
		return attribs, fg, colorCodes[code-40]
	if code in attribCodes :
		attribs.add(attribCodes[code])
# TODO: Test me
#	if code-20 in attribCodes :
#		attribs.remove(attribCodes[code-20])
	return attribs, fg, bg


def stateToClasses(attribs, fg, bg) :
	"""Returns css class names given a given ansi attribute state"""

	return " ".join(
		["ansi_"+attrib for attrib in sorted(attribs)]
		+ (["ansi_"+fg] if fg else [])
		+ (["ansi_bg"+bg] if bg else [])
		)

def deansi(text) :
	text = cgi.escape(text)
	blocks = text.split("\033")
	state = set(), None, None
	ansiBlocks = blocks[:1]
	for block in blocks[1:] :
		attributeCodes, plain = ansiAttributes(block)
		for code in attributeCodes : state = ansiState(code, *state)
		classes = stateToClasses(*state)
		ansiBlocks.append(
			(("<span class='%s'>"%stateToClasses(*state)) + plain + "</span>")
			if classes else plain
			)
	text = "".join(ansiBlocks)
	return text



if __name__ == "__main__" :
	import unittest
	import sys
	
	class DeansiTest(unittest.TestCase) :
		def assertDeansiEquals(self, expected, inputText) :
			return self.assertEquals(expected, deansi(inputText))

		def test_html(self) :
			self.assertDeansiEquals(
				'weee&lt;&gt;&amp;',
				'weee<>&',
			)

		def test_ansiAttributes_withSingleAttribute(self) :
			self.assertEquals(
				([45],'text'),
				ansiAttributes("[45mtext")
			)

		def test_ansiAttributes_withManyAttributes(self) :
			self.assertEquals(
				([45,54,2],'text'),
				ansiAttributes("[45;54;2mtext")
			)

		def test_ansiAttributes_withNoAttributes(self) :
			self.assertEquals(
				([], 'text'),
				ansiAttributes("text")
			)

		def test_ansiAttributes_withNoNumbers(self) :
			self.assertEquals(
				([], '[a;bmtext'),
				ansiAttributes("[a;bmtext")
			)

		def test_ansiState_bright(self) :
			self.assertEquals(
				(set(['bright']), None, None),
				ansiState(1, set(), None, None),
			)

		def test_ansiState_faint(self) :
			self.assertEquals(
				(set(['faint']), None, None),
				ansiState(2, set(), None, None),
			)

		def test_ansiState_italic(self) :
			self.assertEquals(
				(set(['italic']), None, None),
				ansiState(3, set(), None, None),
			)

		def test_ansiState_underscore(self) :
			self.assertEquals(
				(set(['underscore']), None, None),
				ansiState(4, set(), None, None),
			)

		def test_ansiState_blink(self) :
			self.assertEquals(
				(set(['blink']), None, None),
				ansiState(5, set(), None, None),
			)

		def test_ansiState_reverse(self) :
			self.assertEquals(
				(set(['reverse']), None, None),
				ansiState(7, set(), None, None),
			)
		def test_ansiState_hide(self) :
			self.assertEquals(
				(set(['hide']), None, None),
				ansiState(8, set(), None, None),
			)

		def test_ansiState_addTwoAttributes(self) :
			self.assertEquals(
				(set(['bright', 'blink']), None, None),
				ansiState(1, set(['blink']), None, None),
			)

		def test_ansiState_clear_clearsBits(self) :
			self.assertEquals(
				(set(), None, None),
				ansiState(0, set(['blink', 'whatever']), None, None),
			)

		def test_ansiState_setForeground(self) :
			self.assertEquals(
				(set(), 'green', None),
				ansiState(32, set(), 'green', None),
			)

		def test_ansiState_setForegroundTwice(self) :
			self.assertEquals(
				(set(), 'red', None),
				ansiState(31, set(), 'green', None),
			)

		def test_ansiState_setBackground(self) :
			self.assertEquals(
				(set(), None, 'yellow'),
				ansiState(43, set(), None, None),
			)

		def test_ansiState_clearClearsFore(self) :
			self.assertEquals(
				(set(), None, None),
				ansiState(0, set(), 'green', None),
			)

		def test_ansiState_clearClearsBack(self) :
			self.assertEquals(
				(set(), None, None),
				ansiState(0, set(), None, 'green'),
			)

		def test_stateToClasses_withAttribs(self) :
			self.assertEquals(
				"ansi_blink ansi_bright",
				stateToClasses(set(['bright','blink']), None, None)
				)

		def test_stateToClasses_withFore(self) :
			self.assertEquals(
				"ansi_red",
				stateToClasses(set(), 'red', None)
				)

		def test_stateToClasses_withBack(self) :
			self.assertEquals(
				"ansi_bgred",
				stateToClasses(set(), None, 'red')
				)

		def test_stateToClasses_withAll(self) :
			self.assertEquals(
				"ansi_blink ansi_inverse ansi_green ansi_bgred",
				stateToClasses(set(['blink','inverse']), 'green', 'red')
				)

		def test_deansi_withCodes(self) :
			self.assertEquals(
				'this should be <span class=\'ansi_red\'>red</span> and this not',
				deansi('this should be \033[31mred\033[0m and this not'),
			)

		def test_deansi_withComplexCodes(self) :
			self.assertEquals(
				'this should be <span class=\'ansi_red\'>red</span>'
				'<span class=\'ansi_bright ansi_red ansi_bggreen\'> and green background</span> and this not',
				deansi('this should be \033[31mred\033[42;1m and green background\033[0m and this not'),
			)

	
	print """\
<style>
%s
</style>
<div class='ansi_console'>
%s
</div>
"""%(defaultAnsiStyle(), deansi("""\
Some colors:
	\033[31mred\033[0m
	\033[32mgreen\033[0m
	\033[33myellow\033[0m
	\033[34mblue\033[0m
	\033[34mmagenta\033[0m
	\033[36mcyan\033[0m
	\033[37mwhite\033[0m
	\033[39mdefault\033[0m
Some background colors:
	\033[41mred\033[0m
	\033[42mgreen\033[0m
	\033[43myellow\033[0m
	\033[44mblue\033[0m
	\033[44mmagenta\033[0m
	\033[46mcyan\033[0m
	\033[47mwhite\033[0m
	\033[49mdefault\033[0m
"""))
	result = unittest.main()




