N = 2

def aqcuire():
    while heap.lock != 0:
        sys_sched()
    heap.lock = 1

def release():
    heap.lock = 0

def Worker():
    aqcuire()
    sys_sched()
    if heap.tot == 0:
        heap.tot += 1
    sys_sched()
    release()
    heap.finished += 1

def main():
    heap.finished = 0
    heap.tot = 0
    heap.lock = 0
    for i in range(N):
        sys_spawn(Worker)
    while heap.finished < N:
        sys_sched()
    sys_write(f'Bought {heap.tot} bread.')
