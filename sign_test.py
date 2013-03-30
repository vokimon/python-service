#!/usr/bin/python

from Crypto.Hash import MD5
from Crypto.PublicKey import RSA
from Crypto import Random
from sign import SignatureValidator
from sign import MessageSigner
from sign import FSClientKeyRing
import os
import unittest

# TODO: Project not specified in message

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

	def test_keys(self) :
		ring = self.keyRing()
		ring["project1","client1"] = "inventedkey1"
		ring["project2","client1"] = "inventedkey2"
		ring["project2","client2"] = "inventedkey3"
		self.assertEqual(sorted(ring.keys()), [
			("project1","client1"),
			("project2","client1"),
			("project2","client2"),
			])

class FSClientKeyRingTest(ClientKeyRingTest) :
	def setUp(self) :
		try :
			os.system("rm -rf fixture")
		except Exception, e:
			print e
		os.mkdir("fixture")
		os.mkdir("fixture/project1")
		os.mkdir("fixture/project1/client1")
		os.mkdir("fixture/project2")
		os.mkdir("fixture/project2/client1")
		os.mkdir("fixture/project2/client2")

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
		try :
			os.system("rm -rf fixture")
		except Exception as e: 
			print (e)

		os.mkdir("fixture")
		os.mkdir("fixture/project1")
		os.mkdir("fixture/project1/client1")

		self.RSAkey = RSA.generate(1024)
		self.publicKey = self.RSAkey.publickey().exportKey()
		self.privateKey = self.RSAkey.exportKey()

	def tearDown(self) :
		os.system("rm -rf fixture")
		
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
		try :
			os.system("rm -rf fixture")
		except Exception, e: 
			print e
		os.mkdir("fixture")
		os.mkdir("fixture/project1")
		os.mkdir("fixture/project1/client1")
		os.mkdir("fixture/project2")
		os.mkdir("fixture/project2/client1")
		os.mkdir("fixture/project2/client2")

	def tearDown(self) :
		os.system("rm -rf fixture")

	def signed(self, **kwds) :
		plaintext = repr(kwds)
		hash = MD5.new(plaintext).digest()
		signature = self.RSAkey.sign(hash, None)
		kwds.update(signature=signature)
		return kwds

	def test_default_noClient(self) :
		s = SignatureValidator()
		self.assertEqual(
			[]
			, s.clients())

	def test_addClientKey(self) :
		s = SignatureValidator(FSClientKeyRing("fixture"))
		s.addClient(
			"project1","client1",
			publicKey = self.publicKey,
			)
		self.assertEqual([
			("project1","client1"),
			], s.clients())
		self.assertEqual(
			self.publicKey,
			s.clientKey(("project1","client1")),
		)

	def test_validateMessage_whenNoClientInMessage(self) :
		s = SignatureValidator()
		with self.assertRaises(SignatureValidator.SignatureError) as cm:
			s.validateClientMessage(
				project='project1',
				boo='lalala',
				)
		self.assertEqual(
			"Client not specified in message"
			, cm.exception.message)

	def test_validateMessage_whenNoProjectInMessage(self) :
		s = SignatureValidator()
		with self.assertRaises(SignatureValidator.SignatureError) as cm:
			s.validateClientMessage(client='client1')
		self.assertEqual(
			"Project not specified in message"
			, cm.exception.message)

	def test_validateMessage_whenBadProject(self) :
		s = SignatureValidator()
		with self.assertRaises(SignatureValidator.SignatureError) as cm:
			s.validateClientMessage(
				project="badproject",
				client="badclient",
				)
		self.assertEqual(
			"Project or client not registered in server"
			, cm.exception.message)

	def test_validateMessage_whenBadClient(self) :
		s = SignatureValidator()
		with self.assertRaises(SignatureValidator.SignatureError) as cm:
			s.validateClientMessage(
				project="project1",
				client="badclient",
				)
		self.assertEqual(
			"Project or client not registered in server"
			, cm.exception.message)

	def test_validateMessage_whenNoSignature(self) :
		s = SignatureValidator()
		s.addClient(
			project = "project1",
			client="client1",
			publicKey = self.publicKey,
			)
		with self.assertRaises(SignatureValidator.SignatureError) as cm:
			s.validateClientMessage(
				project = "project1",
				client="client1",
				)
		self.assertEqual(
			"Message not signed"
			, cm.exception.message)

	def test_validateMessage_whenBadSignature(self) :
		s = SignatureValidator()
		s.addClient(
			project = "project1",
			client="client1",
			publicKey = self.publicKey,
			)
		message = dict(
			project = "project1",
			client="client1",
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
			project = "project1",
			client="client1",
			publicKey = self.publicKey,
			)
		message = dict(
			project = "project1",
			client="client1",
			)
		result = s.validateClientMessage(**self.signed(**message))
		self.assertEqual(
			True
			, result)

	def test_validateMessage_afterModified(self) :
		s = SignatureValidator()
		s.addClient(
			"project1","client1",
			publicKey = self.publicKey,
			)
		message = dict(
			project = "project1",
			client="client1",
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
			project = "project1",
			client="client1",
			publicKey = self.publicKey,
			)
		message = dict(
			project = "project1",
			client="client1",
			)
		signed = self.signed(**message)
		signed['client'] = "client1"
		result = s.validateClientMessage(**signed)
		self.assertEqual(
			True
			, result)

if __name__ == "__main__" :
	unittest.main()


