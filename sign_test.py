#!/usr/bin/python

from Crypto.Hash import MD5
from Crypto.PublicKey import RSA
from Crypto import Random
from sign import SignatureValidator
from sign import MessageSigner
from sign import FSClientKeyRing
import os
import unittest

class ClientKeyRingTest(unittest.TestCase) :
	"""This TestCase is to ensure that FSClientKeyRing
	has the same behaviour than a dictionary as key ring.
	"""

	def keyRing(self) :
		return dict()

	def test_contains_whenMissing(self) :
		ring = self.keyRing()
		self.assertFalse(("project1","client1") in ring)
	def test_contains_whenExists(self) :
		ring = self.keyRing()
		ring["project1","client1"] = "inventedkey"
		self.assertTrue(
			("project1","client1") in ring)

	def test_getitem_whenExists(self) :
		ring = self.keyRing()
		ring["project1","client1"] = "inventedkey"
		self.assertEqual("inventedkey",
			ring["project1","client1"])

	def test_getitem_whenMissing(self) :
		ring = self.keyRing()
		try :
			ring["project1","client1"]
			self.fail("exception expected")
		except KeyError as e :
			self.assertEqual(e.message,
				('project1', 'client1'))

class FSClientKeyRingTest(ClientKeyRingTest) :
	def setUp(self) :
		try :
			os.system("rm -rf fixture")
		except Exception, e: 
			print e
		os.mkdir("fixture")
		os.mkdir("fixture/project1")
		os.mkdir("fixture/project1/client1")

	def tearDown(self) :
		os.system("rm -rf fixture")
		
	def keyRing(self) :
		return FSClientKeyRing("fixture")

	def test_set_whenProjectMissing(self) :
		ring = self.keyRing()
		try :
			ring["badproject","client1"] = "newkey"
			self.fail("exception expected")
		except KeyError as e :
			self.assertEqual(e.message,
				('badproject', 'client1'))

	def test_contains_whenProjectMissing(self) :
		ring = self.keyRing()
		self.assertFalse(("badproject","client1") in ring)

class MessageSignerTest(unittest.TestCase) :
	def setUp(self) :
		self.RSAkey = RSA.generate(1024)
		self.publicKey = self.RSAkey.publickey().exportKey()
		self.privateKey = self.RSAkey.exportKey()

	def isValid(self, **signed) :
		def md5(**kwds) :
			plaintext = repr(kwds)
			return MD5.new(plaintext).digest()

		key = RSA.importKey(self.publicKey)
		signature = signed['signature']
		del signed['signature']
		hash = md5(**signed)
		return key.verify(hash, signature)

	def test_validSignature(self) :
		signer = MessageSigner(self.privateKey)
		message = dict(
			key1="value1",
			key2=[4,5,3,"hola"],
			)
		result = signer.sign(**message)
		self.assertTrue("signature" in result)
		self.assertTrue(self.isValid(**result))

	def test_wrongSignature(self) :
		signer = MessageSigner(self.privateKey)
		message = dict(
			key1="value1",
			key2=[4,5,3,"hola"],
			)
		result = signer.sign(**message)
		result.update(extraKey="extravalue")
		self.assertFalse(self.isValid(**result))

	def test_badKey(self) :
		try :
			MessageSigner("BadKey")
		except ValueError as e :
			self.assertEqual(e.message,
				"RSA key format is not supported")


class SignatureValidatorTest(unittest.TestCase) :
	def setUp(self) :
		self.RSAkey = RSA.generate(1024)
		self.publicKey = self.RSAkey.publickey().exportKey()
		self.privateKey = self.RSAkey.exportKey()

	def signed(self, **kwds) :
		plaintext = repr(kwds)
		hash = MD5.new(plaintext).digest()
		signature = self.RSAkey.sign(hash, None)
		kwds.update(signature=signature)
		return kwds

	def testDefault_noClient(self) :
		s = SignatureValidator()
		self.assertEqual(
			[]
			, s.clients())

	def test_addClientKey(self) :
		s = SignatureValidator()
		s.addClient(
			name = "A client", 
			publicKey = self.publicKey,
			)
		self.assertEqual(
			["A client"]
			, s.clients())
		self.assertEqual(
			self.publicKey,
			s.clientKey("A client")
		)

	def test_validateMessage_whenNoClientInMessage(self) :
		s = SignatureValidator()
		with self.assertRaises(SignatureValidator.SignatureError) as cm:
			s.validateClientMessage(boo='lalala')
		self.assertEqual(
			"Client not specified in message"
			, cm.exception.message)

	def test_validateMessage_whenBadClient(self) :
		s = SignatureValidator()
		with self.assertRaises(SignatureValidator.SignatureError) as cm:
			s.validateClientMessage(
				client="badclient",
				)
		self.assertEqual(
			"Client not registered in server"
			, cm.exception.message)

	def test_validateMessage_whenNoSignature(self) :
		s = SignatureValidator()
		s.addClient(
			name = "A client", 
			publicKey = self.publicKey,
			)
		with self.assertRaises(SignatureValidator.SignatureError) as cm:
			s.validateClientMessage(
				client="A client",
				)
		self.assertEqual(
			"Message not signed"
			, cm.exception.message)

	def test_validateMessage_whenBadSignature(self) :
		s = SignatureValidator()
		s.addClient(
			name = "A client",
			publicKey = self.publicKey,
			)
		message = dict(
			client="A client",
			signature = [1L,2L,3L,4L],
			)
		with self.assertRaises(SignatureValidator.SignatureError) as cm:
			s.validateClientMessage(**message)
		self.assertEqual(
			"Invalid signature"
			, cm.exception.message)

	def test_validateMessage_whenGoodSignature(self) :
		s = SignatureValidator()
		s.addClient(
			name = "A client",
			publicKey = self.publicKey,
			)
		message = dict(
			client="A client",
			)
		result = s.validateClientMessage(**self.signed(**message))
		self.assertEqual(
			True
			, result)

	def test_validateMessage_afterModified(self) :
		s = SignatureValidator()
		s.addClient(
			name = "A client",
			publicKey = self.publicKey,
			)
		message = dict(
			client="A client",
			)
		signed = self.signed(**message)
		signed['new key'] = "unsigned value"
		with self.assertRaises(SignatureValidator.SignatureError) as cm:
			s.validateClientMessage(**signed)
		self.assertEqual(
			"Invalid signature"
			, cm.exception.message)

	def test_validateMessage_afterSettingWithTheSameValue(self) :
		s = SignatureValidator()
		s.addClient(
			name = "A client",
			publicKey = self.publicKey,
			)
		message = dict(
			client="A client",
			)
		signed = self.signed(**message)
		signed['client'] = "A client"
		result = s.validateClientMessage(**signed)
		self.assertEqual(
			True
			, result)

if __name__ == "__main__" :
	unittest.main()


