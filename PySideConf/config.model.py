#Project information
projectName = ""
projectURL  = ""
buildbotURL = ""

#RSync server
fileServerName  = ''
fileServerBaseDir = ''

#IRC server
ircServerName   = ''

#Git config
baseGitURL  = ''
gitCustomers = {
    'user' : {
        'project' : '~user/url/project.git'
    },
}

#slaves config
from buildbot.buildslave import BuildSlave
slavePortNum= 000
slaveNames = [
              BuildSlave("name", "password"),
             ]

slavesByArch = {
    'amd64'             : 'slave-name',
    'i386'              : 'slave-name',
    #'armel'             : 'slave-name',
    'FREMANTLE_ARMEL'   : 'slave-name',
    'FREMANTLE_X86'     : 'slave-name',
    'debug'             : 'slave-name'
}

