#!/usr/bin/python
# -*- python -*-

from PySideConf import config
from PySideConf import metadata

from buildbot.process import factory
from buildbot.process.properties import WithProperties
from buildbot.steps.transfer import FileDownload
from buildbot.steps.shell import Compile, ShellCommand

pySideEnv = metadata.PySideBootstrap()

def createFactoriesForAllArchitectures():
    factories = []
    for arch in config.slavesByArch.keys():
        factories.append(createFactoryForArchitecture(arch))
    return factories

def createFactoryForArchitecture(arch):
    if arch not in pySideEnv.archs:
        raise ValueError('%s is an unknown architecture.' % arch)

    dist = pySideEnv.getDistByArch(arch)
    baseMasterDir = '/var/lib/buildbot/master/'
    masterScriptsDir = baseMasterDir + 'scripts/'

    linuxWorkDir = pySideEnv.workDir(arch) if pySideEnv.isLinuxArch(arch) else None

    win32TempDir = 'c:\\WINDOWS\\Temp\\' if pySideEnv.isWin32Arch(arch) else None
    win32PythonExec = 'c:\\Python27\\python.exe' if pySideEnv.isWin32Arch(arch) else None

    macOSXInstallDir = '/Users/buildbot/build/pyside-macosx/build/install/'
    macOSXBuildEnv = { 'DYLD_LIBRARY_PATH' : macOSXInstallDir + 'lib' } if pySideEnv.isMacOSXArch(arch) else None

    # Create build factory object
    fac = factory.BuildFactory()

    # Prepare bootstrap
    for cmd in pySideEnv.initializeEnviroment(arch):
        fac.addStep(cmd)

    # Download git_clone script
    scriptSourcePath = masterScriptsDir + 'git_clone.py'
    if pySideEnv.isWin32Arch(arch):
        gitClonePath = win32TempDir + 'git_clone.py'
    elif pySideEnv.isMacOSXArch(arch):
        gitClonePath = macOSXInstallDir + 'bin/git_clone'
    else:
        gitClonePath = '/tmp/git_clone'
    fac.addStep(FileDownload(mastersrc=scriptSourcePath, slavedest=gitClonePath, mode=0755))
    if pySideEnv.isLinuxArch(arch):
        gitCloneTmpPath = gitClonePath
        gitClonePath = pySideEnv.chrootPath(arch, dist) + '/usr/bin/'
        cmd = ['cp', '-a', gitCloneTmpPath, gitClonePath]
        if dist != 'sbox':
            cmd.insert(0, 'sudo')
        fac.addStep(ShellCommand(name='update-scripts', command=cmd, haltOnFailure=True))

    # Functions to check if step conditions should be executed
    def createCloneStepTest(module_name, inv=False):
        def cloneStepTest(step):
            return inv ^ step.build.getProperties().has_key(module_name.lower() + '_gitUrl')
        return cloneStepTest

    def createCheckoutStepTest(property_name):
        def checkoutStepTest(step):
            return step.build.getProperties().has_key(property_name)
        return checkoutStepTest

    for module in metadata.BuildPackages:
        buildDir = None
        if pySideEnv.isWin32Arch(arch):
            buildDir = 'build\\' + module.name
        elif pySideEnv.isMacOSXArch(arch):
            buildDir = 'build/' + module.name

        # Step: Install needed packages
        for cmd in pySideEnv.installPackages(arch, module.depends(dist)):
            fac.addStep(cmd)

        # Step: Clean module directory
        if not pySideEnv.isLinuxArch(arch):
            if pySideEnv.isWin32Arch(arch):
                cmd = ['if', 'exist', module.name, 'rmdir', '/S', '/Q', module.name]
                halt = False
            elif pySideEnv.isMacOSXArch(arch):
                cmd = ['rm', '-rf', module.name]
                halt = True
            fac.addStep(ShellCommand(name='clean-' + module.name,
                                     description='Clean module ' + module.name,
                                     command=cmd,
                                     haltOnFailure=halt))

        # Step: Clone mainline repository
        if pySideEnv.isWin32Arch(arch):
            cmd = [win32PythonExec, gitClonePath, 'clone', module.gitUrl, module.name]
        elif pySideEnv.isMacOSXArch(arch):
            cmd = [macOSXInstallDir + 'bin/git_clone', 'clone', '--depth', '1', module.gitUrl, module.name]
        else:
            workDir = pySideEnv.workDir(arch)
            cmd = pySideEnv.commandPrefix(arch, dist, workDir) + ['git_clone', 'clone', module.gitUrl, workDir + module.name]
        fac.addStep(ShellCommand(name='git-clone-mainline-' + module.name,
                                 description=['Cloned mainline for module ' + module.name],
                                 doStepIf=createCloneStepTest(module.name, True),
                                 command=cmd,
                                 haltOnFailure=True))

        # Step: Clone personal repository
        module_gitUrl = '%s_gitUrl' % module.name.lower()
        if pySideEnv.isWin32Arch(arch):
            cmd = [win32PythonExec, gitClonePath, 'clone', WithProperties('%(' + module_gitUrl + ')s'), module.name]
        elif pySideEnv.isMacOSXArch(arch):
            cmd = [macOSXInstallDir + 'bin/git_clone', 'clone', '--depth', '1',
                   WithProperties('%(' + module_gitUrl + ')s'), module.name]
        else:
            workDir = pySideEnv.workDir(arch)
            cmd = pySideEnv.commandPrefix(arch, dist, workDir) \
                  + ['git_clone', 'clone', WithProperties('%(' + module_gitUrl + ')s'), workDir + module.name]
        fac.addStep(ShellCommand(name='git-clone-personal-' + module.name,
                                 description=['Clone personal repository for module ' + module.name],
                                 doStepIf=createCloneStepTest(module.name),
                                 command=cmd,
                                 haltOnFailure=True))

        # Step: Checkout to specific branch
        module_hashtag = '%s_hashtag' % module.name.lower()
        if pySideEnv.isLinuxArch(arch):
            cmd = pySideEnv.commandPrefix(arch, dist, linuxWorkDir + module.name) \
                  + ['git', 'checkout', WithProperties('%(' + module_hashtag + ')s')]
        else:
            cmd = ['git', 'checkout', WithProperties('%(' + module_hashtag + ')s')]
        fac.addStep(ShellCommand(name='git-checkout-' + module.name,
                                 description=['checkout hash/tag/branch for module ' + module.name],
                                 doStepIf=createCheckoutStepTest(module_hashtag),
                                 command=cmd,
                                 workdir=buildDir,
                                 haltOnFailure=True))

        # Step: Create build directory
        buildPath = None
        if pySideEnv.isLinuxArch(arch):
            buildPath = linuxWorkDir + module.name + '/build/'
            fac.addStep(pySideEnv.createDir(arch, buildPath))

        # Step: Run CMake on build directory
        environment = None
        if pySideEnv.isWin32Arch(arch):
            cmd = pySideEnv.commandPrefix(arch) + ['cmake', '.', '-DCMAKE_INSTALL_PREFIX=../install', '-G', 'NMake Makefiles']
        elif pySideEnv.isMacOSXArch(arch):
            cmd = ['cmake', '-DCMAKE_INSTALL_PREFIX=../install', '-DALTERNATIVE_QT_INCLUDE_DIR=/Library/Frameworks/', '.']
        else:
            environment = pySideEnv.buildVars(dist, arch, buildPath)
            cmd = pySideEnv.commandPrefix(arch, dist, buildPath) \
                  + ['cmake', linuxWorkDir + module.name, '-DCMAKE_INSTALL_PREFIX=' + pySideEnv.installPrefix()]
        if arch == 'debug':
            cmd.append('-DCMAKE_BUILD_TYPE=Debug')
        else:
            cmd.append('-DCMAKE_BUILD_TYPE=Release')
        fac.addStep(ShellCommand(name='cmake-' + module.name,
                                 description=['Run CMake for module ' + module.name],
                                 command=cmd,
                                 workdir=buildDir,
                                 haltOnFailure=True,
                                 env=environment))

        # Step: Build module
        _name = 'build-' + module.name
        _desc = 'Build module ' + module.name
        if pySideEnv.isMacOSXArch(arch):
            fac.addStep(Compile(name=_name,
                                description=_desc,
                                workdir=buildDir,
                                env=macOSXBuildEnv,
                                haltOnFailure=True))
        else:
            if pySideEnv.isWin32Arch(arch):
                cmd = pySideEnv.commandPrefix(arch) + ['nmake']
                environment = None
            else:
                cmd = pySideEnv.commandPrefix(arch, dist, buildPath) + ['make', '-j2']
                environment = pySideEnv.buildVars(dist, arch, buildPath)
            fac.addStep(ShellCommand(name=_name,
                                     description=_desc,
                                     command=cmd,
                                     workdir=buildDir,
                                     haltOnFailure=True,
                                     timeout=30*60,
                                     env=environment))

        # Step: Test module
        cmd = []
        environment = None
        if pySideEnv.isWin32Arch(arch):
            cmd = pySideEnv.commandPrefix(arch)
        elif pySideEnv.isLinuxArch(arch):
            cmd = pySideEnv.commandPrefix(arch, dist, buildPath)
            environment = pySideEnv.buildVars(dist, arch, buildPath)
        else:
            environment = macOSXBuildEnv
        cmd += ['ctest', '-V']
        fac.addStep(ShellCommand(name='test-' + module.name,
                                 description=['Test module ' + module.name],
                                 command=cmd,
                                 workdir=buildDir,
                                 haltOnFailure=False,
                                 env=environment))

        # Step: Install module
        cmd = []
        environment = None
        if pySideEnv.isWin32Arch(arch):
            cmd = pySideEnv.commandPrefix(arch) + ['nmake']
        elif pySideEnv.isLinuxArch(arch):
            cmd = pySideEnv.commandPrefix(arch, dist, buildPath) + ['make']
            environment = pySideEnv.buildVars(dist, arch, buildPath)
        else:
            cmd += ['make']
            environment = macOSXBuildEnv
        cmd += ['install/fast']

        fac.addStep(ShellCommand(name='install-' + module.name,
                                 description=['Install module ' + module.name],
                                 command=cmd,
                                 workdir=buildDir,
                                 haltOnFailure=True,
                                 env=environment))

        # Step: ABI compliance check
        for cmd in pySideEnv.abiComplianceCheck(arch, dist, module):
            fac.addStep(cmd)


    if pySideEnv.isWin32Arch(arch):
        buildDir = 'pyside-win32'
    elif pySideEnv.isMacOSXArch(arch):
        buildDir = 'piupiu-mac'
    else:
        buildDir = 'build-' + arch + '-' + module.name

    builder = {
        'name'      : 'build-pyside-' + arch,
        'slavename' : config.slavesByArch[arch],
        'builddir'  : buildDir,
        'factory'   : fac
    }
    return builder

