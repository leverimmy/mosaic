def main():
    pid = sys_fork()
    if pid != 0:
        sys_sched()
    sys_write(f'fork() returned {pid}\n')

    if pid == 0:
        sys_write('child\n')
    else:
        sys_write('parent\n')
