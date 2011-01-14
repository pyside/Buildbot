#!/usr/bin/python
# -*- python -*-

import shlex
from buildbot import interfaces
from buildbot.sourcestamp import SourceStamp
from buildbot.process.base import BuildRequest
from buildbot.process.properties import Properties
from buildbot.status.words import IRC, IRCContact, IrcStatusBot, IrcBuildRequest

from PySideConf.metadata import *
from PySideConf import config


class PySideContact(IRCContact):

    def command_OI(self, args, who):
        if who == 'hugopl':
            self.send('diga meu filho')
        else:
            self.send('que foi?')

    def command_CUSTOMERS(self, args, who):
        names = config.gitCustomers.keys()
        last = names.pop()
        names = ', '.join(names)
        if names:
            names += ' and '
            txt = 's are '
        else:
            txt = ' is '
        names += last
        string = who + ', my customer' + txt + names
        self.send(string)

    def command_BUILD(self, args, who):
        args = shlex.split(args)
        repos = { 'apiextractor' : None,
                  'generatorrunner' : None,
                  'shiboken' : None,
                  'pyside' : None
                }

        if not who in config.gitCustomers:
            self.send('%s, I\'ll not make this build for you. Do you think I found my genitalia in the trash?' % who)
            return

        builder = None
        for arg in args:
            try:
                repo, target = arg.split('=')
            except:
                self.send('Usage: ' + PySideContact.command_BUILD.usage)
                return
            if repo == 'builder':
                builder = target
            else:
                if not repo in repos:
                    self.send('%s, there is no "%s" repository' % (who, repo))
                    return
                repos[repo] = target

        slaves = ['build-pyside-' + arch for arch in config.slavesByArch.keys() + ['macosx', 'win32']]

        if builder:
            if builder not in slaves:
                self.send("%s, the slave '%s' that you asked for doesn't exist." % (who, builder))
                return
            slaves = [builder]

        for which in slaves:
            bc = self.getControl(which)

            build_properties = Properties()
            build_properties.setProperty('owner', who, 'Build requested from IRC bot on behalf of %s.' % who)
            for propName, propValue in [(pName, pValue) for pName, pValue in repos.items() if pValue]:
                build_properties.setProperty(propName + '_hashtag', propValue, 'Build requested from IRC bot.')

            for repoName, gitUrl in config.gitCustomers[who].items():
                build_properties.setProperty(repoName.lower() + '_gitUrl', config.baseGitURL + gitUrl,
                                             'Personal %s repository of %s.' % (repoName, who))

            r = "forced: by %s: %s" % (self.describeUser(who), 'He had his reasons.')
            s = SourceStamp(branch='BRANCH', revision='REVISION')
            req = BuildRequest(r, s, which, properties=build_properties)
            try:
                bc.requestBuildSoon(req)
            except interfaces.NoSlaveError:
                self.send("%s, sorry, I can't force a build: all slaves are offline" % who)
                return
            ireq = IrcBuildRequest(self)
            req.subscribe(ireq.started)

    command_BUILD_USAGE = " [builder=<BUILDER_NAME>] [apiextractor=<HASH|TAG|BRANCH>] [generatorrunner=<HASH|TAG|BRANCH>] [shiboken=<HASH|TAG|BRANCH>] [pyside=<HASH|TAG|BRANCH>]... - builds the whole PySide toolchain for the user's repositories; if any of them is omitted the buildbot will use HEAD."
    command_BUILD.usage = "build" + command_BUILD_USAGE

    def command_BUILDA(self, args, who):
        self.command_BUILD(args, who)
    command_BUILDA.usage = "builda" + command_BUILD_USAGE

    def command_COMPILA(self, args, who):
        self.command_BUILD(args, who)
    command_COMPILA.usage = "compila" + command_BUILD_USAGE


IrcStatusBot.contactClass = PySideContact

class Meretriz(IRC):
    def __init__(self):
        IRC.__init__(self,
                     host=config.ircServerName,
                     nick='meretriz',
                     channels=['#bordel'])


