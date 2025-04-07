def echo(args):
    sys_write(' '.join(args[1:]))

def main():
    pid = sys_fork()
    if pid != 0:
        sys_sched()
    if pid == 0:
        sys_exec(echo, ['echo', 'this', 'is', 'echo'])
        sys_write('Why would I execute?\n')
    else:
        sys_write("Who's your daddy?\n")
