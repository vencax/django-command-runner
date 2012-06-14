'''
Created on Mar 9, 2012

@author: vencax 
'''
import os
from django.conf import settings

class ParamikoRuner(object):
    """
    Base class for paramiko based runners.
    """
    known_hosts = '~/.ssh/known_hosts'
    def __init__(self):
        import paramiko
        self._server = getattr(settings, 'COMMAND_TARGET_SERVER', '127.0.0.1')
        self._serverUser = getattr(settings, 'COMMAND_TARGET_USER', 'root')
        self._client = paramiko.SSHClient()
        if os.path.exists(os.path.expanduser(self.known_hosts)):
            self._client.load_host_keys(os.path.expanduser(self.known_hosts))
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        from lockfile import FileLock
        self._lock = FileLock('%s/__lock' % settings.PROJECT_ROOT)

    def run(self, command):
        if not hasattr(self, 'shell'):
            self._client.connect(self._server, username=self._serverUser)
            self.shell = self._client.invoke_shell()
        with self._lock:
            self.runCommand(command)
      
class SudoBasedParamikoRuner(ParamikoRuner):
    """
    This is a bit problematic since there is many ways how to login as root.
    That's why this class.
    """
    def __init__(self):
        super(SudoBasedParamikoRuner, self).__init__()
        self._passwd = open('%s/admin.pwd' % settings.PROJECT_ROOT).read()
        
    def runCommand(self, command):
        self.shell.send('sudo -i\n')
        self._waitForPrompt()
        self.shell.send('%s\n' % command)
        self._waitForPrompt()
        
    def _waitForPrompt(self):
        buf = self.shell.recv(9999)
        while not buf.endswith('~# '):
            if buf.endswith(': '):
                self.shell.send('%s\n' % self._passwd)
            buf += self.shell.recv(9999)            
        if settings.DEBUG:
            print buf
        
        
class SysRunner(object):
    """
    This issues the commands directly on the machine this app runs.
    NOTE: this shall be run under root.
    """
    def run(self, command):
        os.system(command)