def echo(args):
    sys_write(' '.join(args[1:]))

def main():
    argv = ['echo', 'this', 'is', 'echo']
    heap.buf = '0x5f3759df'
    sys_exec(echo, argv)
    sys_write('exec() failed\n')
