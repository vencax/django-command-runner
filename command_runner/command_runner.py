'''
Created on Mar 9, 2012

@author: vencax 
'''
import os
import re
from paramiko.ssh_exception import SSHException

def get_username():
    import pwd
    info = pwd.getpwuid(os.getuid())
    return info[5]

class ParamikoRuner(object):
    """
    Base class for paramiko based runners.
    """
    known_hosts = os.path.join(get_username(), '.ssh/known_hosts')
    
    def __init__(self, settings):
        import paramiko
        self._settings = settings
        self._client = paramiko.SSHClient()
        if os.path.exists(self.known_hosts):
            self._client.load_host_keys(self.known_hosts)
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        from lockfile import FileLock
        self._lock = FileLock('%s/__lock' % settings.PROJECT_ROOT)

    def run(self, command):
        if not hasattr(self, 'shell'):
            try:
                server = self._settings.COMMAND_TARGET_SERVER
                user = self._settings.COMMAND_TARGET_USER
                passwd = self._settings.COMMAND_TARGET_PASSWD
                self._client.connect(server, username=user, password=passwd)
            except SSHException, e:
                raise Exception('Unable to connect to %s as %s, (%s)' % \
                                (server, user, str(e)))
            self.shell = self._client.invoke_shell()
        with self._lock:
            return self.runCommand(command)
      
class SudoBasedParamikoRuner(ParamikoRuner):
    """
    This is a bit problematic since there is many ways how to login as root.
    That's why this class.
    """
    retvalRe = re.compile(r'\r\n(?P<rv>[0-9]{1,})\r\n')
        
    def runCommand(self, command):
        self.shell.send('sudo -i\n')
        self._waitForPrompt()
        self.shell.send('%s\n' % command)
        self._waitForPrompt()
        self.shell.send('echo $?\n')
        return self._waitForPrompt(True)
        
    def _waitForPrompt(self, bufDesired=False):
        buf = self.shell.recv(1024)
        while not buf.endswith(':~# '):
            buf += self.shell.recv(1024)
        if bufDesired :
            try:
                return int(self.retvalRe.search(buf).group('rv'))
            except AttributeError:
                return 0
        
class SysRunner(object):
    """
    This issues the commands directly on the machine this app runs.
    NOTE: this shall be run under root.
    """
    def run(self, command):
        os.system(command)