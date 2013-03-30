#!/usr/bin/python

from Crypto.Hash import MD5
from Crypto.PublicKey import RSA
from Crypto import Random
import os
import glob

class FSClientKeyRing(object) :
	"""
	Dictionary like interface to client public keys
	for signing message, which are stored in the
	testfarm log filesystem.
	"""
	def __init__(self, path) :
		self.path = path

	def _keypath(self, key) :
		project, client = key
		return os.path.join(
			self.path, project, client, "pubkey")
		
	def __setitem__(self, key, value) :
		try :
			with open(self._keypath(key), "w") as f :
				f.write(value)
		except IOError as e :
			raise KeyError(key)

	def __getitem__(self, key) :
		try :
			with open(self._keypath(key)) as f :
				return f.read()
		except IOError as e :
			raise KeyError(key)

	def __contains__(self, key) :
		project, client = key
		return os.access(self._keypath(key), os.R_OK)

	def keys(self) :
		return [
			tuple(item.split("/")[-3:-1])
			for item in glob.glob(
				self._keypath(("*","*")))
			]

class MessageSigner(object) :
	def __init__(self, privateKey) :
		self.privateKey = RSA.importKey(privateKey)

	def sign(self, **kwds) :
		plaintext = repr(kwds)
		hash = MD5.new(plaintext).digest()
		signature = self.privateKey.sign(hash, None)
		kwds.update(signature=signature)
		return kwds


class SignatureValidator(object) :
	"""This class contains the public keys of a set of clients
	and validates signed messages in the form of dictionaries
	containing at least a key value for 'client' and a key value for
	the 'signature' of the rest of the key values.
	"""

	def __init__(self, keyring={}) :
		self._clientKeys = keyring

	def addClient(self, project, client, publicKey) :
		self._clientKeys[project,client] = publicKey

	def clients(self) :
		return self._clientKeys.keys()

	def clientKey(self, name) :
		return self._clientKeys[name]

	def validateClientMessage(self, signature='', **kwds) :
		if 'client' not in kwds :
			self._validationFailed("Client not specified in message")

		client = kwds['client']
		project = kwds['project']

		if (project,client) not in self._clientKeys :
			self._validationFailed("Client not registered in server")

		if not signature :
			self._validationFailed("Message not signed")

		hash = self._md5(**kwds)
		keyimport = RSA.importKey(self._clientKeys[project,client])
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


