#!/usr/bin/python

from Crypto.Hash import MD5
from Crypto.PublicKey import RSA
from Crypto import Random

"""
projects
	- Name
	- Skeletton?
	clients
		- publicKey
		- Platform description
		- Task description
		executions
			revisions
				logs
					authors
			tasks
				subtasks
					commands
"""

class SignatureValidator(object) :
	"""This class contains the public keys of a set of clients
	and validates signed messages in the form of dictionaries
	containing at least a key value for 'client' and a key value for
	the 'signature' of the rest of the key values.
	"""

	def __init__(self) :
		self._clientKeys = {}

	def addClient(self, name, publicKey) :
		self._clientKeys[name] = publicKey

	def clients(self) :
		return self._clientKeys.keys()

	def clientKey(self, name) :
		return self._clientKeys[name]

	def validateClientMessage(self, signature='', **kwds) :
		if 'client' not in kwds :
			self._validationFailed("Client not specified in message")

		client = kwds['client']

		if client not in self._clientKeys :
			self._validationFailed("Client not registered in server")

		if not signature :
			self._validationFailed("Message not signed")

		hash = self._md5(**kwds)
		keyimport = RSA.importKey(self._clientKeys[client])
		if not keyimport.verify(hash, signature) :
			self._validationFailed("Invalid signature")

		return True

	class SignatureError(Exception) :
		def __init__(self, message) :
			self.message = message
		def __str__(self) :
			return self.message

	def _validationFailed(self, message) :
		raise SignatureValidator.SignatureError(message)

	def _md5(self, **kwds) :
		plaintext = repr(kwds)
		return MD5.new(plaintext).digest()


import unittest

class SignatureValidatorTest(unittest.TestCase) :
	def setUp(self) :
		rng = Random.new().read
		self.RSAkey = RSA.generate(1024, rng)
		self.publicKey = self.RSAkey.publickey().exportKey()
		self.privateKey = self.RSAkey.exportKey()

	def signed(self, **kwds) :
		rng = Random.new().read
		plaintext = str(kwds)
		hash = MD5.new(plaintext).digest()
		signature = self.RSAkey.sign(hash, rng)
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
			, str(cm.exception))

	def test_validateMessage_whenBadClient(self) :
		s = SignatureValidator()
		with self.assertRaises(SignatureValidator.SignatureError) as cm:
			s.validateClientMessage(
				client="badclient",
				)
		self.assertEqual(
			"Client not registered in server"
			, str(cm.exception))

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
			, str(cm.exception))

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
			, str(cm.exception))

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
			, str(cm.exception))

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


class MessageSigner(object) :
	def __init__(self, privateKey) :
		self.privateKey = RSA.importKey(privateKey)

	def sign(self, **kwds) :
		rng = Random.new().read
		plaintext = str(kwds)
		hash = MD5.new(plaintext).digest()
		signature = self.privateKey.sign(hash, rng)
		kwds.update(signature=signature)
		return kwds

class MessageSignerTest(unittest.TestCase) :
	def setUp(self) :
		rng = Random.new().read
		self.RSAkey = RSA.generate(1024, rng)
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

	def test_right(self) :
		signer = MessageSigner(self.privateKey)
		message = dict(
			key1="value1",
			key2=[4,5,3,"hola"],
			)
		result = signer.sign(**message)
		self.assertTrue("signature" in result)
		self.assertTrue(self.isValid(**result))

	def test_wrong(self) :
		signer = MessageSigner(self.privateKey)
		message = dict(
			key1="value1",
			key2=[4,5,3,"hola"],
			)
		result = signer.sign(**message)
		result.update(extraKey="extravalue")
		self.assertFalse(self.isValid(**result))


if __name__ == "__main__" :
	unittest.main()


