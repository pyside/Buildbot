from buildbot.steps.shell import ShellCommand
from buildbot.steps.transfer import FileUpload
import config

def downloadCommand(sourceFile, destFile):
    src = 'rsync://%s%s/%s'%(config.fileServerName, config.fileServerBaseDir, sourceFile)
    update_command = ['sudo','rsync', '-a', src, destFile]
    cmd = ShellCommand(name='download',
                       description=['Download from file server.', src],
                       command=update_command,
                       haltOnFailure=True)
    return cmd

def uploadCommand(sourceFile):
    pass

class PySideBootstrap():
    def __init__(self, workDirPrefix='/tmp/work/'):
        self.workDirPrefix = workDirPrefix
        self.archs = {
            'amd64'             : 'debian',
            'armel'             : 'debian',
            'i386'              : 'debian',
            'powerpc'           : 'debian',
            'debug'             : 'ubuntu',
            'FREMANTLE_ARMEL'   : 'sbox',
            'FREMANTLE_X86'     : 'sbox',
            'macosx'            : None,
            'win32'             : None
        }

        self.dists = {
            'debian' : 'debian',
            'ubuntu' : 'maverick',
            'fedora' : 'fedora-13-i386',
            'sbox'   : 'sbox'
        }

        self.paths = {
            'debian' : '/opt/chroot/debian',
            'ubuntu' : '/opt/chroot/ubuntu',
            'sbox'   : '/scratchbox/users/pyside/targets/',
            'fedora' : '/var/lib/mock/fedora-13-i386'
        }

        self.urls = {
            'debian' : 'http://ftp.br.debian.org/',
            'ubuntu' : 'http://archive.ubuntu.com/ubuntu/'
        }

        self.installCmds = {
            'debian' : ['apt-get', 'install', '-y'],
            'ubuntu' : ['apt-get', 'install', '-y'],
            'sbox'   : ['apt-get', 'install', '--force-yes', '-y']
        }

        self.base_pkgs = {
            'debian' : ['git-arch', 'g++', 'cmake', 'make', 'python'],
            'ubuntu' : ['git', 'g++', 'cmake', 'make', 'python'],
            'sbox'   : ['g++', 'cmake', 'make'],
            'fedora' : ['git-arch',  'gcc-c++', 'cmake', 'make']
        }

    def isLinuxArch(self, arch):
        return arch in self.archs and self.archs[arch] is not None

    def isUnixArch(self, arch):
        return arch in self.archs and arch != 'win32'

    def isMacOSXArch(self, arch):
        return arch == 'macosx'

    def isWin32Arch(self, arch):
        return arch == 'win32'

    def workDir(self, arch):
        dist = self.archs[arch]
        if not dist:
            return ''
        return self.workDirPrefix + dist + '_' + arch + '/'

    def installPrefix(self):
        return '/usr/'

    def getDistByArch(self, arch):
        return self.archs[arch]

    def libraryDir(self):
        return self.installPrefix() + 'lib/';

    def chrootPath(self, arch, dist):
        if dist == 'fedora':
            return self.paths[dist]
        if dist == 'sbox':
            return '%s/%s'%(self.paths['sbox'], arch)
        return self.paths[dist] + '/' + arch

    def initializeWin32(self):
        cmd = ShellCommand(name='cleanup',
                           description='clean up',
                           command=['if', 'exist', 'install', 'rmdir', '/S', '/Q', 'install'],
                           haltOnFailure=False)
        return [cmd]

    def initializeMacOSX(self):
        cmd = ShellCommand(name='cleanup',
                           description='clean up',
                           command=['rm', '-rf', 'install'],
                           haltOnFailure=True)
        return [cmd]


    def initializeDebianLike(self, dist, arch):
        commands = []

        #init vars
        chroot_name = 'chroot-%s-%s.tar.bz2' % (arch, dist)

        #download files
        commands.append(downloadCommand('scripts/umount_chroot.sh', '/tmp/umount_chroot.sh'))

        #append commands
        update_command = ['sudo','/tmp/umount_chroot.sh', '%s/proc' % self.chrootPath(arch, dist)]
        cmd = ShellCommand(name='umount proc',
                           description=['umoutn proc'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

        '''
        update_command = ['sudo', '/tmp/umount_chroot.sh', '%s/dev' % self.chrootPath(arch, dist)]
        cmd = ShellCommand(name='umount dev',
                           description=['umoutn dev'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)
        '''

        update_command = ['sudo','rm', '-rf', '/tmp/%s'%(chroot_name), self.chrootPath(arch, dist)]
        cmd = ShellCommand(name='clenup',
                           description=['clenup'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

        update_command = ['sudo','mkdir', '-p', self.chrootPath(arch, dist)]
        cmd = ShellCommand(name='mkdir',
                           description=['mkdir'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

        '''
        update_command = ['sudo','/usr/sbin/debootstrap',
                          '--arch', arch,
                          self.dists[dist],
                          self.chrootPath(arch, dist),
                          self.urls[dist]]
        '''

        commands.append(downloadCommand('data/%s' % chroot_name, '/tmp/%s' % chroot_name))
        update_command = ['sudo','tar', '-jxvf',
                          '/tmp/%s' % chroot_name,
                          '-C', self.chrootPath(arch, dist)]
        cmd = ShellCommand(name='debootstrap',
                           description=['initialize'],
                           descriptionDone=['initialized'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

        update_command = ['sudo', 'mount', '-o', 'bind', '/proc', '%s/proc' % self.chrootPath(arch, dist)]
        cmd = ShellCommand(name='mount proc',
                           description=['mount proc'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

        '''
        update_command = ['sudo', 'mount', '-o', 'bind', '/dev', '%s/dev' % self.chrootPath(arch, dist)]
        cmd = ShellCommand(name='mount dev',
                           description=['mout dev'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)
        '''

        update_command = self.commandPrefix(arch, dist) + ['apt-get', 'update']
        cmd = ShellCommand(name='update-source-list',
                                description=['update source list'],
                                descriptionDone=['updated'],
                                command = update_command,
                                haltOnFailure=True)
        commands.append(cmd)

        update_command = self.commandPrefix(arch, dist) + ['apt-get', 'install', '-y'] + self.base_pkgs[dist]
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

        #download files
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


        update_command = self.commandPrefix(arch, 'sbox') + ['apt-get', '-y', 'update']
        cmd = ShellCommand(name='update sourcelist',
                           description=['update'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

        update_command = self.commandPrefix(arch, 'sbox') + ['apt-get', '-y', '--force-yes',  'upgrade']
        cmd = ShellCommand(name='update sourcelist',
                           description=['update'],
                           command=update_command,
                           haltOnFailure=True)
        commands.append(cmd)

        update_command = self.commandPrefix(arch, 'sbox') + ['apt-get', 'install', '-y', '--force-yes'] + self.base_pkgs['sbox']
        cmd = ShellCommand(name='install-base-packages',
                           description=['Install core packages'],
                           descriptionDone=['updated'],
                           command = update_command,
                           haltOnFailure=True)
        commands.append(cmd)


        return commands

    def createDir(self, arch, path):
        dist = self.archs[arch]
        cmd = self.commandPrefix(arch, dist) + ['mkdir', '-p', path ]
        return ShellCommand(name='mkdir',
                            description=['create build dir'],
                            command=cmd,
                            haltOnFailure=True)



    #implement this
    def buildVars(self, dist, arch, path):
        env = {
            'LD_LIBRARY_PATH'   : self.libraryDir(),
            'DISPLAY'           : ':5'
        }
        return env

    #implement this
    def commandPrefix(self, arch, dist=None, path='/'):
        if arch == 'win32':
            return ['c:\\buildbot\\slave\\setenv.bat', '&&']
        elif dist == 'fedora':
            return ['mock', '-v', '-r', self.dists[dist], '--cwd=' + path, '--chroot', '--']
        elif dist == 'debian' or dist == 'ubuntu':
            return ['schroot', '-p', '-c', '%s-%s' % (self.dists[dist], arch), '-d', path, '-u', 'root', '--']
        elif dist == 'sbox':
            return ['/scratchbox/login', '-d', path, '--']
        return []

    #implement this
    def initializeEnviroment(self, arch):
        #TODO detect environment
        dist = self.archs[arch]
        commands = []
        if dist:
            if dist == 'debian' or dist == 'ubuntu':
                commands = self.initializeDebianLike(dist, arch)
            elif dist == 'fedora':
                commands = self.initializeFedora(arch)
            elif dist == 'sbox':
                commands = self.initializeSbox(arch)
            workDir = self.workDir(arch)
            cmd_line = self.commandPrefix(arch, dist) + ['mkdir', '-p', workDir]
            cmd = ShellCommand(name='mkdir',
                               description=['create work dir: ' + workDir],
                               command=cmd_line,
                               haltOnFailure=True)
            commands.append(cmd)
        elif self.isWin32Arch(arch):
            commands = self.initializeWin32()
        elif self.isMacOSXArch(arch):
            commands = self.initializeMacOSX()
        return commands

    #implement this
    def installPackages(self, arch, packages):
        commands = []

        dist = self.archs[arch]
        if dist:
            if arch == 'debug' and 'abi-compliance-checker' in packages:
                packages.remove('abi-compliance-checker')
            update_command = ''
            if dist in ('debian', 'sbox', 'ubuntu'):
                update_command = self.commandPrefix(arch, self.archs[arch]) + self.installCmds[dist] + packages
            elif dist == 'fedora':
                update_command = ['mock', '-r', 'fedora-13-i386', '--install'] + packages

            cmd = ShellCommand(name='install dependencies',
                               description=['Install Packages'],
                               descriptionDone=['Packages installed'],
                               command = update_command,
                               haltOnFailure=True)
            commands.append(cmd)

        return commands

    def abiComplianceCheck(self, arch, dist, module):
        commands = []

        if not arch in config.workDirByArch:
            return commands

        workDir = config.workDirByArch[arch]

        if not workDir:
            return commands

        chrootDir = self.chrootPath(arch, dist)
        abiref = '%s-%s' % (module.name.lower(), module.version)

        # 1. Download abi-checker reference files
        abitarball =  '%s.tar.gz' % abiref
        src = 'abi-compliance/%s/%s' % (arch, abitarball)
        dst = chrootDir + '/tmp/%s' % abitarball
        commands.append(downloadCommand(src, dst))

        # 2. Unpack reference tarball
        cmd = self.commandPrefix(arch, dist) + ['tar', 'xvf', '/tmp/' + abitarball, '-C', '/tmp']
        commands.append(ShellCommand(name='unpack-abi-files',
                                     description=['Unpack ABI compliance check files.'],
                                     command=cmd,
                                     haltOnFailure=True))

        # 3. Download abi-checker files

        # 3.1. Download abi-checker acc xml template
        acc_xml_file = module.name.lower() + '-acc.xml.in'
        src = 'abi-compliance/' + acc_xml_file
        dst = chrootDir + '/tmp/' + acc_xml_file
        commands.append(downloadCommand(src, dst))

        # 3.2. Prepare description files for module ABI checking
        src = 'abi-compliance/prepare_acc_xml.py'
        dst = chrootDir + '/tmp/prepare_acc_xml.py'
        commands.append(downloadCommand(src, dst))

        cmd = self.commandPrefix(arch, dist) +\
              ['python', '/tmp/prepare_acc_xml.py', module.name.lower(), module.version, '/tmp/' + abiref]
        commands.append(ShellCommand(name='prepare-acc-files',
                                     description=['Prepare acc xml files.'],
                                     command=cmd,
                                     haltOnFailure=True))

        # 4. Run abi-compliance-checker
        cmd = self.commandPrefix(arch, dist) \
              + ['abi-compliance-checker', '-l', module.name.lower(),
                 '-d1', '/tmp/%s-acc-ref.xml' % module.name.lower(),
                 '-d2', '/tmp/%s-acc-new.xml' % module.name.lower()]
        commands.append(ShellCommand(name='abi-check',
                                     description=['Run ABI check'],
                                     command=cmd,
                                     workdir=chrootDir + '/tmp/',
                                     haltOnFailure=True))

        # 5. Upload HTML report to master
        master_report_dir = '~/master/public_html/abi-reports/%s/%s/' % (arch, module.name.lower())
        slave_abi_report = chrootDir + \
                           '/compat_reports/%(module)s/%(version)s-reference_to_%(version)s-new/abi_compat_report.html' % \
                           { 'module' : module.name.lower(), 'version' : module.version }
        commands.append(FileUpload(slavesrc=slave_abi_report,
                                   masterdest=master_report_dir + 'abi_compat_report.html',
                                   mode=0644))

        # 6. Add link to report on the master HTML status
        link = 'http://10.60.5.198:8010/abi-reports/%s/%s/abi_compat_report.html' % (arch, module.name.lower())
        commands.append(ShellCommand(name='abi-report-link',
                                     description=['ABI Report', '<a href="%s">%s ABI Report</a>' % (link, module.name)],
                                     command=['echo'],
                                     haltOnFailure=True))

        return commands


class Package(object):
    name = ''
    gitUrl = ''
    version = ''
    deps = {
        'debian' : ['abi-compliance-checker'],
        'sbox'   : [],
        'ubuntu' : ['abi-compliance-checker'],
        'fedora' : []
    }
    moduleDeps = []

    def depends(self, dist):
        result = []
        for m in self.moduleDeps:
            result += m().depends(dist)
        if dist in self.deps:
            result += self.deps[dist]
        if dist in Package.deps:
            result += Package.deps[dist]
        return result

class ApiExtractor(Package):
    name = 'ApiExtractor'
    gitUrl = '%s/pyside/apiextractor.git' % config.baseGitURL
    version = '0.10.0'
    deps = {
        'debian': ['libxslt1-dev', 'libxml2-dev', 'libqt4-dev'],
        'sbox'  : ['libxslt1-dev', 'libxml2-dev', 'libqt4-dev'],
        'ubuntu': ['libxslt1-dev', 'libxml2-dev', 'libqt4-dev'],
        'fedora': ['libxslt-devel', 'libxml2-devel', 'qt-devel']
    }

class GeneratorRunner(Package):
    name = 'GeneratorRunner'
    gitUrl = '%s/pyside/generatorrunner.git' % config.baseGitURL
    version = '0.6.7'
    moduleDeps = [ApiExtractor]

class Shiboken(Package):
    name = 'Shiboken'
    gitUrl = '%s/pyside/shiboken.git' % config.baseGitURL
    version = '1.0.0'
    moduleDeps = [GeneratorRunner, ApiExtractor]
    deps = {
        'debian'    : ['python2.6-dev'],
        'sbox'      : ['python2.5-dev'],
        'ubuntu'    : ['python2.6-dev', 'python2.6-dbg'],
        'fedora'    : ['python-devel']
    }

class PySide(Package):
    name = 'PySide'
    gitUrl = '%s/pyside/pyside.git' % config.baseGitURL
    version = '1.0.0'
    deps = {
        'debian'    : ['libqt4-sql-sqlite'],
        'sbox'      : ['libqt4-sql-sqlite'],
        'ubuntu'    : ['libqt4-sql-sqlite'],
        'fedora'    : ['xvfb']
    }
    moduleDeps = [Shiboken, GeneratorRunner, ApiExtractor]

BuildPackages = [ApiExtractor(), GeneratorRunner(), Shiboken(), PySide()]
