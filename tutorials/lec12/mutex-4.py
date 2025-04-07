N = 2

def Worker(name):
    if name == 1:
        heap.note_1 = 1
        sys_sched()
        while (heap.note_2 != 0):
            sys_sched()
        if heap.tot == 0:
            heap.tot += 1
        sys_sched()
        heap.note_1 = 0
        heap.finished += 1
    if name == 2:
        heap.note_2 = 1
        sys_sched()
        if (heap.note_1 == 0):
            if heap.tot == 0:
                heap.tot += 1
        sys_sched()
        heap.note_2 = 0
        heap.finished += 1

def main():
    heap.finished = 0
    heap.tot = 0
    heap.note_1 = 0
    heap.note_2 = 0
    for i in range(1, N + 1):
        sys_spawn(Worker, i)
    while heap.finished < N:
        sys_sched()
    sys_write(f'Bought {heap.tot} bread.')
