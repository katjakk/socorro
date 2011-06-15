import unittest
import os
import sys
import re
try:
  import json
except ImportError:
  import simplejson as json

## WARNING: in next line, if you get
## ERROR: Failure: ImportError (No module named thrift)
## You can fix it by checking out https://socorro.googlecode.com/svn/trunk/thirdparty
## and adding .../thirdparty to your PYTHONPATH (or equivalent)
try:
  import socorro.storage.crashstorage as cstore
except ImportError,x:
  print>> sys.stderr,"""
## If you see "Failure: ImportError (No module named thrift) ... ERROR"
## * check out https://socorro.googlecode.com/svn/trunk/thirdparty
## * read .../thirdparty/README.txt
## * add .../thirdparty to your PYTHONPATH (or equivalent)
  """
  raise
import socorro.unittest.testlib.expectations as exp
import socorro.lib.util as util

import socorro.unittest.testlib.loggerForTest as loggerForTest

def testCrashStorageSystem__init__():
  d = util.DotDict()
  d.benchmark = False
  css = cstore.CrashStorageBase(d)
  assert css.config == d, 'config not saved'

def testCrashStorageSystem_makeJsonDictFromForm():
  d = util.DotDict()
  d.dumpField = 'd'
  fakeValue = util.DotDict()
  fakeValue.value = 2
  f = util.DotDict()
  f.a = '1'
  f.b = fakeValue
  f.c = '3'
  f.d = '4'
  f.e = '5'
  expectedTime = '12:00:01'
  fakeTimeModule = exp.DummyObjectWithExpectations('fakeTimeModule')
  fakeTimeModule.expect('time', (), {}, expectedTime, None)
  css = cstore.CrashStorageBase(d)
  resultJson = css.makeJsonDictFromForm(f, fakeTimeModule)
  assert resultJson.a == '1'
  assert resultJson.b == 2
  assert resultJson.c == '3'
  assert 'd' not in resultJson
  assert resultJson.e == '5'

def testCrashStorageSystem_save():
  css = cstore.CrashStorageBase(util.DotDict({'logger': util.SilentFakeLogger()}))
  result = css.save_raw('fred', 'ethel', 'lucy')
  assert result == cstore.CrashStorageBase.NO_ACTION

def testHBaseCrashStorage___init__():
  d = util.DotDict()
  j = util.DotDict()
  d.hbaseHost = 'fred'
  d.hbasePort = 'ethel'
  d.hbaseTimeout = 9000
  j.root = d.hbaseFallbackFS = '.'
  d.throttleConditions = []
  j.maxDirectoryEntries = d.hbaseFallbackDumpDirCount = 1000000
  j.jsonSuffix = d.jsonFileSuffix = '.json'
  j.dumpSuffix = d.dumpFileSuffix = '.dump'
  j.dumpGID = d.hbaseFallbackdumpGID = 666
  j.dumpPermissions = d.hbaseFallbackDumpPermissions = 660
  j.dirPermissions = d.hbaseFallbackDirPermissions = 770
  j.logger = d.logger = util.SilentFakeLogger()
  fakeHbaseConnection = exp.DummyObjectWithExpectations('fakeHbaseConnection')
  fakeHbaseConnection.expect('hbaseThriftExceptions', (), {}, [], None)
  fakeHbaseModule = exp.DummyObjectWithExpectations('fakeHbaseModule')
  fakeHbaseModule.expect('HBaseConnectionForCrashReports', (d.hbaseHost, d.hbasePort, d.hbaseTimeout), {"logger":d.logger}, fakeHbaseConnection, None)
  fakeJsonDumpStore = exp.DummyObjectWithExpectations('fakeJsonDumpStore')
  fakeJsonDumpModule = exp.DummyObjectWithExpectations('fakeJsonDumpModule')
  fakeJsonDumpModule.expect('JsonDumpStorage', (), j, fakeJsonDumpStore, None)
  css = cstore.HBaseCrashStorage(d,
                                 hbaseClient=fakeHbaseModule,
                                 jsonDumpStorage=fakeJsonDumpModule)
  assert css.hbaseConnection == fakeHbaseConnection

def testHBaseCrashStorage_save_1():
  """straight save into hbase with no trouble"""
  currentTimestamp = 'now'
  expectedDumpResult = '1234567890/n'

  jdict = util.DotDict({'ProductName':'FireFloozy', 'Version':'3.6', 'legacy_processing':1})

  d = util.DotDict()
  j = util.DotDict()
  d.hbaseHost = 'fred'
  d.hbasePort = 'ethel'
  d.hbaseTimeout = 9000
  j.root = d.hbaseFallbackFS = '.'
  d.throttleConditions = []
  j.maxDirectoryEntries = d.hbaseFallbackDumpDirCount = 1000000
  j.jsonSuffix = d.jsonFileSuffix = '.json'
  j.dumpSuffix = d.dumpFileSuffix = '.dump'
  j.dumpGID = d.hbaseFallbackdumpGID = 666
  j.dumpPermissions = d.hbaseFallbackDumpPermissions = 660
  j.dirPermissions = d.hbaseFallbackDirPermissions = 770
  d.logger = util.SilentFakeLogger()

  fakeHbaseConnection = exp.DummyObjectWithExpectations('fakeHbaseConnection')
  fakeHbaseConnection.expect('hbaseThriftExceptions', (), {}, [], None)
  fakeHbaseConnection.expect('put_json_dump', ('uuid', jdict, expectedDumpResult), {"number_of_retries":2}, None, None)

  fakeHbaseModule = exp.DummyObjectWithExpectations('fakeHbaseModule')
  fakeHbaseModule.expect('HBaseConnectionForCrashReports', (d.hbaseHost, d.hbasePort, d.hbaseTimeout), {"logger":d.logger}, fakeHbaseConnection, None)

  fakeJsonDumpStore = exp.DummyObjectWithExpectations('fakeJsonDumpStore')
  fakeJsonDumpModule = exp.DummyObjectWithExpectations('fakeJsonDumpModule')
  fakeJsonDumpModule.expect('JsonDumpStorage', (), j, fakeJsonDumpStore, None)

  css = cstore.HBaseCrashStorage(d,
                                 hbaseClient=fakeHbaseModule,
                                 jsonDumpStorage=fakeJsonDumpModule)
  expectedResult = cstore.CrashStorageBase.OK
  result = css.save_raw('uuid', jdict, expectedDumpResult, currentTimestamp)
  assert result == expectedResult, 'expected %s but got %s' % (expectedResult, result)

#def testHBaseCrashStorage_save_2():
  #"""hbase fails, must save to fallback"""
  #currentTimestamp = 'now'
  #expectedDumpResult = '1234567890/n'
  #jdict = util.DotDict({'ProductName':'FireFloozy', 'Version':'3.6', 'legacy_processing':1})

  #d = util.DotDict()
  #j = util.DotDict()
  #d.hbaseHost = 'fred'
  #d.hbasePort = 'ethel'
  #d.hbaseTimeout = 9000
  #j.root = d.hbaseFallbackFS = '.'
  #d.throttleConditions = []
  #j.maxDirectoryEntries = d.hbaseFallbackDumpDirCount = 1000000
  #j.jsonSuffix = d.jsonFileSuffix = '.json'
  #j.dumpSuffix = d.dumpFileSuffix = '.dump'
  #j.dumpGID = d.hbaseFallbackDumpGID = 666
  #j.dumpPermissions = d.hbaseFallbackDumpPermissions = 660
  #j.dirPermissions = d.hbaseFallbackDirPermissions = 770
  #j.logger = d.logger = util.SilentFakeLogger()

  #fakeHbaseConnection = exp.DummyObjectWithExpectations('fakeHbaseConnection')
  #fakeHbaseConnection.expect('hbaseThriftExceptions', (), {}, [], None)
  ##fakeHbaseConnection.expect('create_ooid', ('uuid', jdict, expectedDumpResult), {}, None, Exception())
  #fakeHbaseConnection.expect('put_json_dump', ('uuid', jdict, expectedDumpResult), {"number_of_retries":1}, None, Exception())

  #fakeHbaseModule = exp.DummyObjectWithExpectations('fakeHbaseModule')
  #fakeHbaseModule.expect('HBaseConnectionForCrashReports', (d.hbaseHost, d.hbasePort, d.hbaseTimeout), {"logger":d.logger}, fakeHbaseConnection, None)

  #class FakeFile(object):
    #def write(self, x): pass
    #def close(self): pass

  #fakeJsonFile = FakeFile()
  #fakeDumpFile = exp.DummyObjectWithExpectations('fakeDumpFile')
  #fakeDumpFile.expect('write', (expectedDumpResult,), {})
  #fakeDumpFile.expect('close', (), {})

  #fakeJsonDumpStore = exp.DummyObjectWithExpectations('fakeJsonDumpStore')
  #fakeJsonDumpStore.expect('newEntry', ('uuid', os.uname()[1], currentTimestamp), {}, (fakeJsonFile, fakeDumpFile))
  #fakeJsonDumpModule = exp.DummyObjectWithExpectations('fakeJsonDumpModule')
  #fakeJsonDumpModule.expect('JsonDumpStorage', (), j, fakeJsonDumpStore, None)

  #cstore.logger = loggerForTest.TestingLogger()
  #css = cstore.HBaseCrashStorage(d, fakeHbaseModule, fakeJsonDumpModule)
  #expectedResult = cstore.CrashStorageBase.OK
  #result = css.save_raw('uuid', jdict, expectedDumpResult, currentTimestamp)

  #assert result == expectedResult, 'expected %s but got %s' % (expectedResult, result)

def testHBaseCrashStorage_save_3():
  """hbase fails but there is no filesystem fallback - expecting fail return"""
  currentTimestamp = 'now'
  expectedDumpResult = '1234567890/n'
  jdict = {'a':2, 'b':'hello'}

  d = util.DotDict()
  d.hbaseHost = 'fred'
  d.hbasePort = 'ethel'
  d.hbaseTimeout = 9000
  d.hbaseFallbackFS = ''
  d.throttleConditions = []
  d.hbaseFallbackDumpDirCount = 1000000
  d.jsonFileSuffix = '.json'
  d.dumpFileSuffix = '.dump'
  d.hbaseFallbackDumpGID = 666
  d.hbaseFallbackDumpPermissions = 660
  d.hbaseFallbackDirPermissions = 770
  d.logger = util.SilentFakeLogger()

  fakeHbaseConnection = exp.DummyObjectWithExpectations('fakeHbaseConnection')
  fakeHbaseConnection.expect('hbaseThriftExceptions', (), {}, [], None)
  #fakeHbaseConnection.expect('create_ooid', ('uuid', jdict, expectedDumpResult), {}, None, Exception())
  fakeHbaseConnection.expect('put_json_dump', ('uuid', jdict, expectedDumpResult), {"number_of_retries":1}, None, Exception())

  fakeHbaseModule = exp.DummyObjectWithExpectations('fakeHbaseModule')
  fakeHbaseModule.expect('HBaseConnectionForCrashReports', (d.hbaseHost, d.hbasePort, d.hbaseTimeout), {"logger":d.logger}, fakeHbaseConnection, None)

  fakeJsonDumpModule = exp.DummyObjectWithExpectations('fakeJsonDumpModule')

  cstore.logger = loggerForTest.TestingLogger()
  css = cstore.HBaseCrashStorage(d, fakeHbaseModule, fakeJsonDumpModule)
  expectedResult = cstore.CrashStorageBase.ERROR
  result = css.save_raw('uuid', jdict, expectedDumpResult, currentTimestamp)

  assert result == expectedResult, 'expected %s but got %s' % (expectedResult, result)

#def testCrashStorageSystemForNFS__init__():
  #d = util.DotDict()
  #d.storageRoot = '/tmp/std'
  #d.dumpDirCount = 42
  #d.jsonFileSuffix = '.json'
  #d.dumpFileSuffix = '.dump'
  #d.dumpGID = 23
  #d.dumpPermissions = 777
  #d.dirPermissions = 777
  #d.deferredStorageRoot = '/tmp/def'
  #d.throttleConditions = [
    #("Version", lambda x: x[-3:] == "pre" or x[3] in 'ab', 100.0), # queue 100% of crashes with version ending in "pre" or having 'a' or 'b'
    ##("Add-ons", re.compile('inspector\@mozilla\.org\:1\..*'), 75.0), # queue 75% of crashes where the inspector addon is at 1.x
    ##("UserID", "d6d2b6b0-c9e0-4646-8627-0b1bdd4a92bb", 100.0), # queue all of this user's crashes
    ##("SecondsSinceLastCrash", lambda x: 300 >= int(x) >= 0, 100.0), # queue all crashes that happened within 5 minutes of another crash
    #(None, True, 10.0) # queue 10% of what's left
  #]

  #css = cstore.LegacyCrashStorage(d)
  #assert css.standard_storage.root == d.storageRoot
  #assert css.deferred_storage.root == d.deferredStorageRoot
  #assert css.hostname == os.uname()[1]

#def testCrashStorageForDualHbaseCrashStorageSystem01():
  #d = util.DotDict()
  #j = util.DotDict()
  #d.hbaseHost = 'fred'
  #d.secondaryHbaseHost = 'barney'
  #d.hbasePort = 'ethel'
  #d.secondaryHbasePort = 'betty'
  #d.hbaseTimeout = 3000
  #d.secondaryHbaseTimeout = 10000
  #j.root = d.hbaseFallbackFS = '.'
  #d.throttleConditions = []
  #j.maxDirectoryEntries = d.hbaseFallbackDumpDirCount = 1000000
  #j.jsonSuffix = d.jsonFileSuffix = '.json'
  #j.dumpSuffix = d.dumpFileSuffix = '.dump'
  #j.dumpGID = d.hbaseFallbackdumpGID = 666
  #j.dumpPermissions = d.hbaseFallbackDumpPermissions = 660
  #j.dirPermissions = d.hbaseFallbackDirPermissions = 770
  #j.logger = d.logger = util.SilentFakeLogger()
  #fakeHbaseConnection1 = exp.DummyObjectWithExpectations('fakeHbaseConnection1')
  #fakeHbaseConnection2 = exp.DummyObjectWithExpectations('fakeHbaseConnection2')
  #fakeHbaseConnection1.expect('hbaseThriftExceptions', (), {}, [], None)
  #fakeHbaseConnection2.expect('hbaseThriftExceptions', (), {}, [], None)
  #fakeHbaseConnection1.expect('get_json', ('fakeOoid1',), {'number_of_retries':2}, 'fake_json1')
  #import socorro.storage.hbase_client as hbc
  #fakeHbaseConnection1.expect('get_json', ('fakeOoid2',), {'number_of_retries':2}, None, hbc.OoidNotFoundException())
  #fakeHbaseConnection2.expect('get_json', ('fakeOoid2',), {'number_of_retries':2}, 'fake_json2')
  #fakeHbaseModule = exp.DummyObjectWithExpectations('fakeHbaseModule')
  #fakeHbaseModule.expect('HBaseConnectionForCrashReports', (d.hbaseHost, d.hbasePort, d.hbaseTimeout), {"logger":d.logger}, fakeHbaseConnection1, None)
  #fakeHbaseModule.expect('HBaseConnectionForCrashReports', (d.secondaryHbaseHost, d.secondaryHbasePort, d.secondaryHbaseTimeout), {"logger":d.logger}, fakeHbaseConnection2, None)
  ##fakeHbaseModule.expect('OoidNotFoundException', (), {}, hbc.OoidNotFoundException)
  #fakeJsonDumpStore = exp.DummyObjectWithExpectations('fakeJsonDumpStore')
  #fakeJsonDumpModule = exp.DummyObjectWithExpectations('fakeJsonDumpModule')
  #fakeJsonDumpModule.expect('JsonDumpStorage', (), j, fakeJsonDumpStore, None)
  #fakeJsonDumpModule.expect('JsonDumpStorage', (), j, fakeJsonDumpStore, None)
  #css = cstore.DualHbaseCrashStorageSystem(d,
                                           #hbaseClient=fakeHbaseModule,
                                           #jsonDumpStorage=fakeJsonDumpModule)
  #assert css.hbaseConnection == fakeHbaseConnection1
  #assert css.fallbackHBase.hbaseConnection == fakeHbaseConnection2
  #result = css.get_meta('fakeOoid1')
  #assert result == 'fake_json1'
  #result = css.get_meta('fakeOoid2')
  #assert result == 'fake_json2'

