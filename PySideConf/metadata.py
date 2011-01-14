from buildbot.steps.shell import ShellCommand
from buildbot.steps.transfer import FileDownload
import config

def downloadCommand(sourceFile, destFile):
    update_command = ['sudo','rsync', '-a', 'rsync://%s%s/%s'%(config.fileServerName, config.fileServerBaseDir, sourceFile), destFile]
    cmd = ShellCommand(name='download',
		   description=['download'],
		   command=update_command,
		   haltOnFailure=True)
    return cmd

def uploadCommand(sourceFile):
    pass

class PySideBootstrap():
    ARCHS = ['amd64', 'armel', 'powerpc', 'i386', 'debug', 'FREMANTLE_ARMEL', 'FREMANTLE_X86']
    def __init__(self, work_dir):
        self.archs    = { 'amd64'     : 'debian',
                    'armel'     : 'debian',
                    'i386'     : 'debian',
                    'powerpc'     : 'debian',
                    'debug'	: 'ubuntu',
                    'FREMANTLE_ARMEL'   : 'sbox',
                    'FREMANTLE_X86'    : 'sbox' }

        self.dists = {'debian' : 'debian',
                   'ubuntu' : 'maverick',
                   'fedora' : 'fedora-13-i386',
                   'sbox'   : 'sbox'  }

        self.paths = {'debian' : '/opt/chroot/debian',
                      'ubuntu' : '/opt/chroot/ubuntu',
                      'sbox'   : '/scratchbox/users/pyside/targets/',
                      'fedora' : '/var/lib/mock/fedora-13-i386'}

        self.urls = {'debian' : 'http://ftp.br.debian.org/',
                     'ubuntu' : 'http://archive.ubuntu.com/ubuntu/'}

        self.installCmds = {'debian' : ['apt-get', 'install', '-y'],
                   'ubuntu' : ['apt-get', 'install', '-y'],
                   'sbox'   : ['apt-get', 'install', '--force-yes', '-y'] }

        self.base_pkgs = {'debian' : ['git-arch', 'g++', 'cmake', 'make', 'python'],
                   'ubuntu' : ['git', 'g++', 'cmake', 'make', 'python'],
                   'sbox'   : ['g++', 'cmake', 'make'],
                   'fedora' : ['git-arch',  'gcc-c++', 'cmake', 'make'] }

        self.work_dir = work_dir


    def workDir(self, arch):
        dist = self.archs[arch]
        return self.work_dir + dist + '_' + arch + '/'

    def installPrefix(self):
        return "/usr/"

    def getDistByArch(self, arch):
        return self.archs[arch]

    def libraryDir(self):
        return self.installPrefix() + "lib/";

    def chrootPath(self, dist, arch):
        if dist == 'fedora':
            return self.paths[dist]
	if dist == 'sbox':
	    return '%s/%s'%(self.paths['sbox'], arch)
        else:
            return self.paths[dist] + '/' + arch

    def initalizeDebianLike(self, dist, arch):
        commands = []

        #init vars
	chroot_name = 'chroot-%s-%s.tar.bz2'%(arch, dist)

        #dowload files
        commands.append(downloadCommand('scripts/umount_chroot.sh', '/tmp/umount_chroot.sh'))

        #append commands
        update_command = ['sudo','/tmp/umount_chroot.sh', '%s/proc' % self.chrootPath(dist, arch)]
        cmd = ShellCommand(name='umount proc',
                           description=['umoutn proc'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

	"""
        update_command = ['sudo', '/tmp/umount_chroot.sh', '%s/dev' % self.chrootPath(dist, arch)]
        cmd = ShellCommand(name='umount dev',
                           description=['umoutn dev'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)
 	"""

        update_command = ['sudo','rm', '-rf', '/tmp/%s'%(chroot_name), self.chrootPath(dist, arch)]
        cmd = ShellCommand(name='clenup',
                           description=['clenup'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

        update_command = ['sudo','mkdir', '-p', self.chrootPath(dist, arch)]
        cmd = ShellCommand(name='mkdir',
                           description=['mkdir'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

        """
                update_command = ['sudo','/usr/sbin/debootstrap',
                     '--arch', arch,
                      self.dists[dist],
                      self.chrootPath(dist, arch),
                      self.urls[dist]]
        """

        commands.append(downloadCommand('data/%s'%chroot_name, '/tmp/%s'%chroot_name))
        update_command = ['sudo','tar', '-jxvf',
                          '/tmp/%s'%chroot_name,
                          '-C', self.chrootPath(dist, arch)]
        cmd = ShellCommand(name='debootstrap',
                           description=['initialize'],
                           descriptionDone=['initialized'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

        update_command = ['sudo', 'mount', '-o', 'bind', '/proc', '%s/proc' % self.chrootPath(dist, arch)]
        cmd = ShellCommand(name='mount proc',
                           description=['mount proc'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

        """
        update_command = ['sudo', 'mount', '-o', 'bind', '/dev', '%s/dev' % self.chrootPath(dist, arch)]
        cmd = ShellCommand(name='mount dev',
                           description=['mout dev'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)
        """

        update_command = self.commandPrefix(dist, arch) + ['apt-get', 'update']
        cmd = ShellCommand(name='update-source-list',
                                description=['update source list'],
                                descriptionDone=['updated'],
                                command = update_command,
                                haltOnFailure=True)
        commands.append(cmd)

        update_command = self.commandPrefix(dist, arch) + ['apt-get', 'install', '-y'] + self.base_pkgs[dist]
        cmd = ShellCommand(name='install-base-packages',
                                description=['Install core packages'],
                                descriptionDone=['updated'],
                                command = update_command,
                                haltOnFailure=True)
        commands.append(cmd)
        return commands

    def initializeFedora(self, arch):
        commands = []
        update_command = ['rm', '-rf', '/var/lib/fedora-13-i386']
        cmd = ShellCommand(name='clenup',
                                description=['clenup'],
                                    command=update_command,
                            haltOnFailure=True)
        commands.append(cmd)

        update_command = ['mock', '--init', '-r', 'fedora-13-i386', '--arch', arch]
        cmd = ShellCommand(name='debootstrap',
                                description=['initialize'],
                            descriptionDone=['initialized'],
                                    command=update_command,
                            haltOnFailure=True)
        commands.append(cmd)

        update_command = ['mock', '-r', 'fedora-13-i386', '--install'] + self.base_pkgs['fedora']
        cmd = ShellCommand(name='install-base-packages',
                                description=['Install core packages'],
                                descriptionDone=['updated'],
                                command = update_command,
                                haltOnFailure=True)
        commands.append(cmd)
        return commands

    def initializeSbox(self, arch):
        commands = []

        #dowload files
        commands.append(downloadCommand('scripts/clenup-sbox.sh', '/tmp/clenup-sbox.sh'))
        commands.append(downloadCommand('data/scratchbox-rootstrap.tar.bz2', '/tmp/scratchbox-rootstrap-%s.tar.bz2'%arch))

        #append commands
        update_command = ['sudo', '/tmp/clenup-sbox.sh']
        cmd = ShellCommand(name='clenup',
                           description=['clenup: sbox'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

        update_command = ['sudo', 'tar', 'jxf', '/tmp/scratchbox-rootstrap-%s.tar.bz2'%arch, '-C', '/']
        cmd = ShellCommand(name='install maemo-sdk',
                           description=['maemo'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

        update_command = ['sudo', '/scratchbox/sbin/sbox_ctl', 'start']
        cmd = ShellCommand(name='initialize sbox',
                                description=['sbox'],
                                    command=update_command,
                            haltOnFailure=True)
        commands.append(cmd)

        update_command = ['/scratchbox/tools/bin/sb-conf', 'se', arch]
        cmd = ShellCommand(name='prepare distro',
                                description=['prepare'],
                                    command=update_command,
                            haltOnFailure=True)
        commands.append(cmd)


        update_command = self.commandPrefix('sbox', arch) + ['apt-get', '-y', 'update']
        cmd = ShellCommand(name='update sourcelist',
                                description=['update'],
                                    command=update_command,
                            haltOnFailure=True)
        commands.append(cmd)

        update_command = self.commandPrefix('sbox', arch) + ['apt-get', '-y', '--force-yes',  'upgrade']
        cmd = ShellCommand(name='update sourcelist',
                                description=['update'],
                                    command=update_command,
                            haltOnFailure=True)
        commands.append(cmd)

        update_command = self.commandPrefix('sbox', arch) + ['apt-get', 'install', '-y', '--force-yes'] + self.base_pkgs['sbox']
        cmd = ShellCommand(name='install-base-packages',
                                description=['Install core packages'],
                                descriptionDone=['updated'],
                                command = update_command,
                                haltOnFailure=True)
        commands.append(cmd)


        return commands

    def createDir(self, arch, path):
        dist = self.archs[arch]
        cmd = self.commandPrefix(dist, arch) + ['mkdir', '-p', path ]
        return ShellCommand(name='mkdir',
                description=['create build dir'],
                command=cmd,
                haltOnFailure=True)

    #inmplement this
    def buildVars(self, dist, arch, path):
        env = {'LD_LIBRARY_PATH' : self.libraryDir(), 'DISPLAY' : ':5'}
        return env


    #implement this
    def commandPrefix(self, dist, arch, path="/"):
        if dist == 'fedora':
            return ['mock', '-v', '-r', self.dists[dist], '--cwd=' + path, '--chroot', '--']
        elif dist == 'debian' or dist == 'ubuntu':
            return ['schroot', '-p', '-c', '%s-%s' % (self.dists[dist], arch), '-d', path, '-u', 'root', '--']
        elif dist == 'sbox':
            return ['/scratchbox/login', '-d', path, '--']
        return []

    #implement this
    def initializeEnviroment(self, arch):
        work_dir = self.workDir(arch)
        #TODO detect enviroment
        dist = self.archs[arch]

        commands = []

        if dist == "debian" or dist == "ubuntu":
            commands = self.initalizeDebianLike(dist, arch)
        elif dist == "fedora":
            commands = self.initializeFedora(arch)
        elif dist == "sbox":
            commands = self.initializeSbox(arch)

        cmd = self.commandPrefix(dist, arch) + ['mkdir', '-p', work_dir ]
        commands.append(ShellCommand(name='mkdir',
                        description=['create work dir: ' + work_dir],
                        command=cmd,
                        haltOnFailure=True))
        return commands

    #implemet this
    def installPackages(self, arch, packages):
        dist = self.archs[arch]
        update_command = ""

        if dist == 'debian' or dist == 'sbox' or dist == 'ubuntu':
            update_command = self.commandPrefix(self.archs[arch], arch) + self.installCmds[dist] + packages
        elif dist == 'fedora':
            update_command = ['mock', '-r', 'fedora-13-i386', '--install'] + packages


        cmd = ShellCommand(name='install dependencies',
                           description=['Install Packages'],
                           descriptionDone=['Packages installed'],
                           command = update_command,
                           haltOnFailure=True)
        return [cmd,]


class Package(object):
    name = ''
    gitUrl = ''
    version = ''
    deps = []
    moduleDeps = []

    def depends(self, dist):
        result = []
        for m in self.moduleDeps:
            result += m().depends(dist)

        if dist in self.deps:
            result += self.deps[dist]

        return result

class ApiExtractor(Package):
    name = 'ApiExtractor'
    gitUrl = '%s/pyside/apiextractor.git' % config.baseGitURL
    version = '0.9.2'
    deps = {'debian': ['libxslt1-dev', 'libxml2-dev', 'libqt4-dev'],
        'sbox'  : ['libxslt1-dev', 'libxml2-dev', 'libqt4-dev'],
        'ubuntu': ['libxslt1-dev', 'libxml2-dev', 'libqt4-dev'],
        'fedora': ['libxslt-devel', 'libxml2-devel', 'qt-devel'] }

class GeneratorRunner(Package):
    name = 'GeneratorRunner'
    gitUrl = '%s/pyside/generatorrunner.git' % config.baseGitURL
    version = '0.9.2'
    moduleDeps = [ApiExtractor]

class Shiboken(Package):
    name = 'Shiboken'
    gitUrl = '%s/pyside/shiboken.git' % config.baseGitURL
    version = '1.0.0'
    moduleDeps = [GeneratorRunner, ApiExtractor]
    deps = {'debian'    : ['python2.6-dev'],
        'sbox'       : ['python2.5-dev'],
        'ubuntu'     : ['python2.6-dev', 'python2.6-dbg'],
        'fedora'     : ['python-devel'] }

class PySide(Package):
    name = 'PySide'
    gitUrl = '%s/pyside/pyside.git' % config.baseGitURL
    version = '1.0.0'
    deps = {'debian'     : ['libqt4-sql-sqlite'],
        'sbox'      : ['libqt4-sql-sqlite'],
        'ubuntu'    : ['libqt4-sql-sqlite'],
        'fedora'    : ['xvfb'] }
    moduleDeps = [Shiboken, GeneratorRunner, ApiExtractor]

BuildPackages = [ApiExtractor(), GeneratorRunner(), Shiboken(), PySide()]
