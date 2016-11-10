from fabric.api import *
from fabric.contrib.files import exists, append
import os
import re
from textwrap import dedent
env.remote_interrupt = True
if os.environ.has_key('FABAC_USER'):
    env.user = os.environ['FABAC_USER']
if os.environ.has_key('FABRIC_PASS'):
    env.password = os.environ['FABAC_PASS']

# While using "execute" to call fabric methods
# this env.hosts is overridden by the passed
# hosts variable (in models.py)
env.hosts = ["localhost"]

env.remote_interrupt = True


#NFS related fabric functions 

def make_test_dir(shareDir = "/opt/share/test"):
    sudo ("mkdir -p " + shareDir)
    sudo ("chown nobody:nogroup" + shareDir)


@task
def idempotent_append(lineStr, filepathcheck, filepathwrite, sudoneeded = False):
    """
    Append a line to a filepathwrite only if lineStr is not in filepathcheck
    look out for lineStr strings with quotes in them.
    """
    cmdStr = " ".join(["grep -q","\""+lineStr+"\"",filepathcheck,"||","echo ","\""+lineStr+"\"", ">>", filepathwrite])
    if sudoneeded:
        sudo(cmdStr)
    else:
        run(cmdStr)


@task
def install_nfsserver (shareDir = "/opt/share", exportip = "192.168.121.1"):
    """
    Install and configure kernel-nfs-server
    Install NFS kernel server and create a directory to serve files from.
    IMPORTANT: Dont let users run this action. Only for sysadmins.
    """
    if package_installed('nfs-kernel-server')==False:
        installpackage('nfs-kernel-server')
    sudo ("mkdir -p " + shareDir)
    sudo ("chown nobody:nogroup " + shareDir)
    #Need to put something in exports because otherwise nfs-kernel-server does not start
    basevol = os.path.join(shareDir,"basevolume")
    sudo ("mkdir -p "+ basevol)
    #sudo (" ".join(["echo '",basevol,exportip+"(ro,no_subtree_check)'"," >> ", "/etc/exports"]))
    _linestr = " ".join([basevol,exportip+"(ro,no_subtree_check)"])
    print _linestr
    idempotent_append(_linestr,"/etc/exports","/etc/exports",True)
    sudo("service nfs-kernel-server restart", pty=False)

@task
def export_volume (exportDir = "/opt/share/test",
    exporthost = "192.168.121.1", 
    options=['rw','no_subtree_check']):
    """
    Create subdirectory if it doesn't already exist and export it via NFS
    """
    sudo ("mkdir -p " + exportDir)
    if isinstance(options,list):
        options = ",".join(options)
    exportfscmd = " ".join(["exportfs","-o",options,exporthost+":"+exportDir])
    sudo (exportfscmd)
    _linestr = " ".join([exportDir,exporthost+"("+options+")"])
    idempotent_append(_linestr,"/etc/exports","/etc/exports",True)

@task
def unexport_volume (volpath):
    """
    Stop sharing the volume at volpath
    Remove the entry from /etc/exports
    """
    sudo ("sed -i '/{}/d' /etc/exports".format(re.escape(volpath)))
    exportfscmd = " ".join(["exportfs","-r"])
    sudo (exportfscmd)

@task
def delete_directory (dirpath):
    """
    Delete the directory dirpath
    """
    #sudo ("rm -rf " + dirpath)
    pass # Add this later - dangerous function


@task
def add_supervisor_process(program_name, django_env, 
    djangomgmtcmd, user, password, *program_args):
    """
    Add a script to supervisor.
    if program_name.conf is not present as 
    /etc/supervisor/conf.d/program_name.conf, then
    copy program_name.sh to /usr/local/bin and create
    /etc/supervisor/conf.d/program_name.conf.
    Signal supervisor to load this new conf file
    """
    env.user = user
    env.password = password
    #Pass if the conf file exists.
    if exists(os.path.join("/etc/supervisor/conf.d/",
        program_name+".conf"),use_sudo = True):
        pass
    else:
        #Install supervisor if needed
        #installpackage("supervisor")
        #sudo ("service  supervisor start")
        
        # Copy script file to /usr/local/bin
        #scriptText = open(program_script).read()
        #scriptPath = os.path.join("/usr/local/bin/",program_name+".sh")
        #append(scriptPath, scriptText, use_sudo = True)
        #sudo("chmod +x "+scriptPath)
        
        cmd = " ".join(["source",django_env + ";", 
		djangomgmtcmd, "rqworker", " ".join(program_args)])
        
        conftext = dedent (
            """
            [program:{}]
            command={}
            user={}
            autostart=true
            autorestart=true
            stderr_logfile=/var/log/{}.err.log
            stdout_logfile=/var/log/{}.out.log
            """.format(program_name,cmd, env.user,
                program_name,program_name))
            #Careful with the sizes of those log files; 
            #rotate them in production

        # Add supervisor conf file
        append(os.path.join("/etc/supervisor/conf.d/",
            program_name+".conf"),conftext,use_sudo = True)
        sudo ("supervisorctl reread; supervisorctl update")


#Other Fabric functions for e.g. package management, server perf testing etc.
#(Not wired up to the Hootie Django application currently)

def package_installed(pkg_name):
    """
	Check if a package is installed.
	ref: http:superuser.com/questions/427318/#comment490784_427339
	Currently only for Debian/Ubuntu 
	"""
    cmd_f = 'dpkg-query -l "%s" | grep -q ^.i'
    cmd = cmd_f % (pkg_name)
    with settings(warn_only=True):
        result = run(cmd)

    return result.succeeded

@task
def installpackage(pkg_name):
    """
    Install package (Debian/Ubuntu only) if not already installed
    ref: http://stackoverflow.com/a/10439058/1093087
    """
    run("date")
    if package_installed(pkg_name)==False:
        sudo('apt-get --force-yes --yes install %s' % (pkg_name))

@task
def uptime():
    """
    Look for system reboots (time since reboot) as well as load averages.
    """
    sudo("date")
    run("uptime")

@task
def vmstat (delay = 1, count = 3):
    """
    vmstat reports information about processes, memory, paging, block IO, traps, disks and cpu activity.
    The  first report produced gives averages since the last reboot.  
    Additional reports give information on a sampling period of length delay.  
    The process and memory reports are instantaneous in either case.
    """
    run("date")
    run("vmstat {} {} -SM".format(delay,count))


@task
def dmesg (numLines = 20):
    """
    Print out the last numLines of dmesg
    """
    run("date")
    run("dmesg -T | tail -n {}".format(numLines))


@task
def mpstat (processors='ALL', delay = 1, count = 3):
    """
    The  mpstat command writes to standard output activities for each available processor, processor 0 being the first one. 
    """
    run("date")
    if package_installed('sysstat')==False:
		installpackage('sysstat')

    run("mpstat -P {} {} {}".format(processors,delay,count))


@task
def pidstat (delay = 5, count = 1, regex = "."):
    """
    The pidstat command is used for monitoring individual tasks currently being managed by the Linux kernel.
    """
    run("pidstat {} {} -C {}".format(delay,count,regex))

@task
def iostat (delay = 1, count = 3):
    """
    Report Central Processing Unit (CPU) statistics and input/output statistics for devices and partitions.
    """
    if package_installed('sysstat')==False:
		installpackage('sysstat')
    run("date")
    run("iostat -kxz {} {}".format(delay,count))

@task
def free():
    """
    Display amount of free and used memory in the system
    """
    run("date")
    run("free -m -h")

@task
def sarnet_dev (delay = 1, count = 3):
    """
    Report network statistics of all interfaces
    """
    if package_installed('sysstat')==False:
		installpackage('sysstat')
    run("date")
    run("sar -n DEV {} {}".format(delay,count))

@task
def sarnet_tcp (delay = 1, count = 3):
    """
    TCP statistics: number of incoming and outgoing TCP connections and restransmissions, a measure of server load
    The active and passive counts are often useful as a rough measure of server load: 
    number of new accepted connections (passive), and number of downstream connections (active). 
    Retransmits are a sign of a network or server issue; it may be an unreliable network 
    (e.g., the public Internet), or it may be due a server being overloaded and dropping packets. 
    """
    if package_installed('sysstat')==False:
		installpackage('sysstat')
    run("sar -n TCP,ETCP {} {}".format(delay,count))

@task
def top ():
    """
    display Linux processes
    """
    run ("top -b -n 1")

