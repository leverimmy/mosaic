# MOSAIC: Operating System Model and Checker

## 简介

这是 [MOSAIC](https://github.com/jiangyy/mosaic) 的修改版，增加了部分 System Call，并增加了 [tutorials](tutorials/) 部分以适配清华大学计算机系《操作系统》课程的讲义。

**文件结构**

- [mosaic.py](mosaic.py) - The Model Checker
- [vis/](vis/) - 可视化脚本
- [examples/](examples/) - 论文中评估的代码示例
- [tutorials/](tutorials/) - 适配《操作系统》课程的教程内容
- [CODE_ANALYSIS.md](CODE_ANALYSIS.md) - 对 [mosaic.py](mosaic.py) 代码框架的详细解释

## 环境配置

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Detailed Introduction

### The Operating System Model

MOSAIC supports simple applications with "system calls". The program entry is `main()`:

```python
def main():
    pid = sys_fork()
    sys_sched()  # non-deterministic context switch
    if pid == 0:
        sys_write('World\n')
    else:
        sys_write('Hello\n')
```

MOSAIC can interpret these system calls, or model-check it:

    python3 mosaic.py --run foo.py
    python3 mosaic.py --check bar.py

A JSON file (state transition graph) will be printed to stdout.
The output (state transition graph) can be piped to another tool, e.g., a
visualization tool:

```bash
# quick and dirty check
python3 mosaic.py --check examples/hello.py | grep stdout | sort | uniq
```

```bash
# interactive state explorer
python3 mosaic.py --check examples/hello.py | python3 -m vis
```

![](vis/demo.png)

### Modeled System Calls

System Call         | Behavior
--------------------|-----------------------------------------------
`sys_fork()`        | create current thread's heap and context clone
`sys_exec(f, xs)`   | create a new process executing `f(xs)`
`sys_spawn(f, xs)`  | spawn a heap-sharing thread executing `f(xs)`
`sys_write(xs)`     | write string `xs` to a shared console
`sys_bread(k)`      | return the value of block id `k`
`sys_bwrite(k, v)`  | write block `k` with value `v`
`sys_sync()`        | persist all outstanding block writes
`sys_sched()`       | perform a non-deterministic context switch
`sys_choose(xs)`    | return a non-deterministic choice in `xs`
`sys_crash()`       | perform a non-deterministic crash

Limitation: system calls are implemented by `yield`. To keep the model checker minimal, one cannot perform system call in a function. (This is not a fundamental limitation and will be addressed in the future.)
