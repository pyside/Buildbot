#Project information
projectName = 'PySide'
projectURL  = 'http://www.pyside.org/'
buildbotURL = 'http://127.0.0.1:8010/'

#RSync server
fileServerName  = '127.0.0.1'
fileServerBaseDir = '/pub'

#IRC server
ircServerName   = '127.0.0.1'

#Git configuration
baseGitURL  = 'git://127.0.0.1/'
gitCustomers = {
    'user' : {
        'repository' : '~user/project/repository.git',
    }
}

#slaves configuration
from buildbot.buildslave import BuildSlave
slavePortNum = 000
slaveNames = [
    BuildSlave('name', 'password'),
]

slavesByArch = {
    'arch' : 'slave-hostname',
}

