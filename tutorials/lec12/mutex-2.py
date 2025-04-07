N = 2

def Worker():
    heap.note = 1
    sys_sched()
    if heap.tot == 0:
        if heap.note == 0:
            heap.tot += 1
    sys_sched()
    heap.note = 0
    heap.finished += 1

def main():
    heap.finished = 0
    heap.tot = 0
    heap.note = 0
    for _ in range(N):
        sys_spawn(Worker)
    while heap.finished < N:
        sys_sched()
    sys_write(f'Bought {heap.tot} bread.')
