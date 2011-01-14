#! /usr/bin/python

import sys
import commands
import random
import os.path
import feedparser
import time
import re

from twisted.spread import pb
from twisted.cred import credentials
from twisted.internet import reactor
from twisted.python import log

buildbot_host = 'localhost'
buildbot_port = 9989

gitorious_url = 'http://qt.gitorious.org'
project_name  = 'pyside'
module_names  = ['apiextractor', 'generatorrunner', 'boostpythongenerator', 'pyside']
branch        = 'master'
sleep_interval= 5 

#code
pending_changes = []

class GitChange:
    def __init__(self, user, branch, new_hash, comment, module_name):
        self.user = user
        self.new_hash = new_hash
	self.branch = branch
	self.comment = comment
	self.module_name = module_name

def done(*args):
    reactor.stop()

def parse_last_change(module_name):
    url = '%s/%s/%s/commits/%s/feed.atom' % (gitorious_url, project_name, module_name, branch)
    print url
    d = feedparser.parse(url)
    regex_hash = re.compile('Grit::Commit/(\w+)')
    for entry in d.entries:
        data = entry.id
        results = regex_hash.search(data)
        if results:
            git_hash = results.group(1)
            return GitChange(entry.author, branch, git_hash, entry.title, module_name)
    return None

def add_change(dummy, remote):
    if len(pending_changes) > 0:
        c = pending_changes.pop(0)
    else:
	return None

    change = {'who'     : c.user,
              'project' : c.module_name,
              'files'   : ["unknow"],
              'comments': c.comment,
              'branch'  : 'master',
              'revision': 'origin/master',
              '%s_hashtag'%c.module_name : c.new_hash }

    d = remote.callRemote('addChange', change)
    d.addCallback(add_change, remote)
    return d

def connect_failed(error):
    print "Could not connect to %s: %s" % (buildbot_host, error.getErrorMessage())
    return error

def connected(remote):
    return add_change(None, remote)

def send_change(chs):
    global pending_changes
    pending_changes.extend(chs)

    f = pb.PBClientFactory()
    d = f.login(credentials.UsernamePassword("change", "changepw"))
    reactor.connectTCP(buildbot_host, buildbot_port, f)

    d.addErrback(connect_failed)
    d.addCallback(connected)
    d.addBoth(done)
    
    reactor.run()


last_changes = {}
for m in module_names:
    last_changes[m] = None

while(True):
    print "check for updates"
    changes = []
    for m in module_names:
        ch = parse_last_change(m)
        if last_changes[m] == None or (ch and (ch.new_hash != last_changes[m].new_hash)):
            last_changes[m] = ch
            changes.append(ch)

    if len(changes) > 0:
        send_change(changes)

    print "wait for : %d minutes." % sleep_interval
    time.sleep(60 * sleep_interval)

