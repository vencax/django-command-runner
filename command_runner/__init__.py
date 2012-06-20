from django.conf import settings


RUN_COMMAND_FACILITY = getattr(settings, 'RUN_COMMAND_FACILITY', 'SudoBasedParamikoRuner')
mod = __import__('command_runner', globals(), locals(), [RUN_COMMAND_FACILITY])
runnerClass = getattr(mod, RUN_COMMAND_FACILITY)
runner = runnerClass()

def runCommand(command):
    """ Runs command on remote machine """
    return runner.run(command)