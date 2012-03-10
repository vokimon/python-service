#!/usr/bin/python
"""
Copyright 2012 David Garcia Garzon

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

__doc__ = """\
This module provides functions to convert terminal output including
ansi terminal codes to stylable html.

The main entry point are 'deansi(input)' which performs the conversion
on an input string and 'styleSheet' which provides a minimal style sheet.
You can overwrite stylesheets by placing new rules after this minimal one.
"""

# TODO: Support empty m, being like 0m
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

variations = [ # normal, pale, bright
	('black', 'black', 'gray'), 
	('red', 'darkred', 'red'), 
	('green', 'darkgreen', 'green'), 
	('yellow', 'orange', 'yellow'), 
	('blue', 'darkblue', 'blue'), 
	('magenta', 'purple', 'magenta'), 
	('cyan', 'darkcyan', 'cyan'), 
	('white', 'lightgray', 'white'), 
]

def styleSheet(brightColors=True) :
	"""\
	Returns a minimal css stylesheet so that deansi output 
	could be displayed properly in a browser.
	You can append more rules to modify this default
	stylesheet.

	brightColors: set it to False to use the same color
		when bright attribute is set and when not.
	"""

	simpleColors = [
		".ansi_%s { color: %s; }" % (normal, normal)
		for normal, pale, bright in variations]
	paleColors = [
		".ansi_%s { color: %s; }" % (normal, pale)
		for normal, pale, bright in variations]
	lightColors = [
		".ansi_bright.ansi_%s { color: %s; }" % (normal, bright)
		for normal, pale, bright in variations]
	bgcolors = [
		".ansi_bg%s { background-color: %s; }" % (normal, normal)
		for normal, pale, bright in variations]

	attributes = [
		".ansi_bright { font-weight: bold; }",
		".ansi_faint { opacity: .5; }",
		".ansi_italic { font-style: italic; }",
		".ansi_underscore { text-decoration: underline; }",
		".ansi_blink { text-decoration: blink; }",
		".ansi_reverse { border: 1pt solid; }",
		".ansi_hide { opacity: 0; }",
		".ansi_strike { text-decoration: line-through; }",
	]

	return '\n'.join(
		[ ".ansi_terminal { white-space: pre; font-family: monospace; }", ]
		+ (paleColors+lightColors if brightColors else simpleColors)
		+ bgcolors
		+ attributes
		)

def ansiAttributes(block) :
	"""Given a sequence "[XX;XX;XXmMy Text", where XX are ansi 
	attribute codes, returns a tuple with the list of extracted
	ansi codes and the remaining text 'My Text'"""

	attributeRe = re.compile( r'^[[](\d+(?:;\d+)*)?m')
	match = attributeRe.match(block)
	if not match : return [], block
	if match.group(1) is None : return [0], block[2:]
	return [int(code) for code in match.group(1).split(";")], block[match.end(1)+1:]


def ansiState(code, attribs, fg, bg) :
	"""Keeps track of the ansi attribute state given a new code"""

	if code == 0 : return set(), None, None   # reset all
	if code == 39 : return attribs, None, bg   # default fg
	if code == 49 : return attribs, fg, None   # default bg
	# foreground color
	if code in xrange(30,38) :
		return attribs, colorCodes[code-30], bg
	# background color
	if code in xrange(40,48) :
		return attribs, fg, colorCodes[code-40]
	# attribute setting
	if code in attribCodes :
		attribs.add(attribCodes[code])
	# attribute resetting
	if code in xrange(21,30) and code-20 in attribCodes :
		toRemove = attribCodes[code-20] 
		if toRemove in attribs :
			attribs.remove(toRemove)
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
			(("<span class='%s'>"%classes) + plain + "</span>")
			if classes else plain
			)
	text = "".join(ansiBlocks)
	return text


# From here onwards it is just test code


if __name__ == "__main__" :
	import sys
	html_template = """\
<style>
.ansi_terminal { background-color: #222; color: #cfc; }
%s
</style>
<div class='ansi_terminal'>%s</div>
"""
	if '--test' not in sys.argv :
		inputFile = file(sys.argv[1]) if sys.argv[1:] else sys.stdin
		print html_template % (styleSheet(), deansi(inputFile.read()))
		sys.exit(0)

	sys.argv.remove('--test')
	import unittest
	
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

		def test_ansiAttributes_emptyReturnsZero(self) :
			self.assertEquals(
				([0], 'text'),
				ansiAttributes("[mtext")
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

		def test_ansiState_noForeground(self) :
			self.assertEquals(
				(set(['blink','inverse']), None, 'red'),
				ansiState(39, set(['blink','inverse']), 'green', 'red')
				)

		def test_ansiState_noBackground(self) :
			self.assertEquals(
				(set(['blink','inverse']), 'green', None),
				ansiState(49, set(['blink','inverse']), 'green', 'red')
				)

		def test_ansiState_resetAttribute(self) :
			self.assertEquals(
				(set(['inverse']), 'green', 'red'),
				ansiState(25, set(['blink','inverse']), 'green', 'red')
				)

		def test_ansiState_resetAttributeNotInThere(self) :
			self.assertEquals(
				(set(['inverse']), 'green', 'red'),
				ansiState(25, set(['inverse']), 'green', 'red')
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

		def test_deansi_emptyAttributeClears(self) :
			self.assertEquals(
				'this should be <span class=\'ansi_red\'>red</span> and this not',
				deansi('this should be \033[31mred\033[m and this not'),
			)

		def test_deansi_withComplexCodes(self) :
			self.assertEquals(
				'this should be <span class=\'ansi_red\'>red</span>'
				'<span class=\'ansi_bright ansi_red ansi_bggreen\'> and green background</span> and this not',
				deansi('this should be \033[31mred\033[42;1m and green background\033[0m and this not'),
			)

		def test_deansi_takesMultiline(self) :
			self.assertEquals(
				'this should be <span class=\'ansi_red\'>\nred</span>'
				'<span class=\'ansi_bright ansi_red ansi_bggreen\'> and green \nbackground\n</span> and this not',
				deansi('this should be \033[31m\nred\033[42;1m and green \nbackground\n\033[0m and this not'),
			)

		def test_backToBack(self) :
			terminalInput = """\
Normal colors:
	\033[30mblack\033[0m\
	\033[31mred\033[0m\
	\033[32mgreen\033[0m\
	\033[33myellow\033[0m\
	\033[34mblue\033[0m\
	\033[35mmagenta\033[0m\
	\033[36mcyan\033[0m\
	\033[37mwhite\033[0m\
	\033[39mdefault\033[0m
Bright colors:
	\033[1;30mblack\033[0m\
	\033[1;31mred\033[0m\
	\033[1;32mgreen\033[0m\
	\033[1;33myellow\033[0m\
	\033[1;34mblue\033[0m\
	\033[1;35mmagenta\033[0m\
	\033[1;36mcyan\033[0m\
	\033[1;37mwhite\033[0m\
	\033[1;39mdefault\033[0m
Background colors:
	\033[40mblack\033[0m\
	\033[41mred\033[0m\
	\033[42mgreen\033[0m\
	\033[43myellow\033[0m\
	\033[44mblue\033[0m\
	\033[45mmagenta\033[0m\
	\033[46mcyan\033[0m\
	\033[47mwhite\033[0m\
	\033[49mdefault\033[0m
Attributes:
	\033[1mbright\033[0m
	\033[2mfaint\033[0m
	\033[3mitalic\033[0m
	\033[4munderscore\033[0m
	\033[5mblink\033[0m
	\033[6mdouble blink\033[0m <- not implemented
	\033[7mreverse\033[0m <- TODO: Find a better way to implement it
	\033[8mhide\033[0m <- It's hidden, you can still select and copy it
	\033[9mstrike\033[0m

Activating \033[31mred and then \033[43mdark yellow
background and then activating \033[32mgreen foreground
now changing attribute to \033[1mbright and then
\033[21mreseting it without changing colors.
\033[44mblue background and \033[5mblink attribute,
\033[49mdefault background, unsetting \033[25mblink,
unsetting \033[39m foreground and \033[0mall attribs.
"""
			print terminalInput
			expected = file("deansi-b2b.html").read()
			result = html_template % (styleSheet(), deansi(terminalInput))

			if (result!=expected) :
				file("deansi-failed.html","w").write(result)
			self.assertEquals(expected, result)

	unittest.main()


