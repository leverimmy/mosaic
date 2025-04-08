# Code Analysis for MOSAIC

本文档对提供的 MOSAIC 操作系统模拟器和状态检查器代码进行详细解析。代码的注释已经非常详尽，本文基于注释的内容，进一步详细分析其实现细节、设计意图和功能。

## 代码概述

该代码实现了一个模拟的操作系统模型 `OperatingSystem` 和一个状态空间检查器 `Mosaic`。主要功能包括：

1. 操作系统建模：
   - 模拟多线程操作系统的行为，包括进程创建、线程切换、系统调用等。
   - 提供简单的虚拟设备模拟，包括字符设备（如 `sys_write`）和块存储设备（如 `sys_bread` 和 `sys_bwrite`）。
2. 系统调用和状态转移：
   - 通过 Python 的生成器机制实现系统调用（使用 `yield` 模拟操作系统与用户程序的交互）。
   - 系统调用返回可能的非确定性选择，支持模拟操作系统的非确定性行为（如线程调度）。
3. 状态空间探索：
   - 提供两种状态空间探索方式：
     - `run`：随机探索路径，模拟一次执行。
     - `check`：穷尽所有可能的状态转移，构建完整的状态转移图。
4. 输入源代码的自动转换：
   - 自动将用户的 Python 源代码中的系统调用（如 `sys_write`）转化为生成器表达式（如 `yield ('sys_write', args)`）。

代码分为以下几个部分：

1. 系统调用定义（1. Mosaic system calls）
2. 操作系统建模（2. Mosaic operating system emulator）
   - 数据结构（2.1 Data structures）
   - 操作系统类 `OperatingSystem` 的实现（2.2, 2.3, 2.4）
3. 状态检查器（3. Mosaic runtime）
   - `Mosaic` 类与解析逻辑（3.1）
4. 命令行工具（4. Utilities）

## 1. 系统调用定义

系统调用是操作系统提供给用户进程的接口，用于访问底层资源或完成操作系统控制的任务。代码定义了以下系统调用（通过 `@syscall` 装饰器注册）：

### 1.1 进程、线程和上下文切换

- `sys_exec`：清空当前线程列表并启动一个新进程。
- `sys_spawn`：创建一个共享堆的新线程。
- `sys_fork`：通过深拷贝创建当前线程的克隆。
- `sys_sched`：非确定性地切换到其他可运行的线程。

这些调用模拟了多线程操作系统的基本行为，如进程创建（`exec`）、线程并发（`spawn`）、线程克隆（`fork`）和调度（`sched`）。

### 1.2 虚拟字符设备

- `sys_choose`：非确定性地从一个选项集合中选择一个值。
- `sys_write`：将字符串写入模拟的标准输出。

这部分提供了字符设备的基本功能，尤其 `sys_choose` 支持非确定性选择，为随机性和模型检查提供支持。

### 1.3 虚拟块存储设备

- `sys_bread`：从块存储设备中读取键对应的值。
- `sys_bwrite`：将键值对写入存储设备的缓冲区。
- `sys_sync`：将缓冲区中的数据持久化到存储设备。
- `sys_crash`：模拟系统崩溃，允许缓冲区中的数据部分持久化。

这部分模拟了简单的键值存储设备，支持缓存、不确定性崩溃等行为，适合测试存储系统的崩溃一致性。

### 1.4 系统调用辅助函数

- `SYSCALLS`：维护所有系统调用的列表。
- `syscall(func)`：一个装饰器，用于标记系统调用函数并将其名称加入 `SYSCALLS`。

## 2. 操作系统建模

`OperatingSystem` 类是代码的核心部分，模拟了一个简单的操作系统。以下是对其实现的解析。

### 2.1 数据结构

- `Heap`：
  - 模拟线程的堆内存，使用 `__dict__` 储存数据。
  - 不直接定义成员变量，允许动态扩展。
- `Thread`：
  - 表示线程结构，包含两个部分：
    1. `context`：线程上下文，用生成器表示。
    2. `heap`：线程的堆内存。
- `Storage`：
  - 模拟块存储设备，包含两个字段：
    1. `persist`：持久化存储。
    2. `buf`：缓冲区，表示未持久化的写操作。

### 2.2 操作系统类

#### 初始化：  

```python
def __init__(self, init: Callable):
```

- 创建一个操作系统实例并初始化：
  - 一个包含初始线程的线程列表。
  - 当前运行的线程索引设置为 `0`。
  - 虚拟字符设备的输出 `stdout` 初始化为空字符串。
  - 虚拟存储设备的状态初始化为空。

#### 系统调用实现

系统调用的实现以**返回所有可能的非确定性选择**为核心设计理念。例如：

- `sys_sched`：
  - 返回所有可运行线程的切换选项。
  - 非确定性选择由字典表示，键是选项，值是对应的操作。
    ```python
    @syscall
    def sys_sched(self):
        return {
            f't{i+1}': (lambda i=i: self._switch_to(i))
            for i, th in enumerate(self._threads)
            if th.context.gi_frame is not None  # thread still alive?
        }
    ```
- `sys_crash`：
  - 模拟崩溃时的持久化子集选择。
  - 利用 `itertools.product` 枚举所有可能的持久化子集。

#### 状态转移

- `_step(self, choice)`：执行一次状态转移：
  1. 切换到当前线程。
  2. 根据选择执行对应操作。
  3. 运行当前线程的下一步，处理生成器的返回值。
- `state_dump(self)`：创建当前操作系统状态的快照，包含：
  - 当前运行的线程。
  - 所有线程上下文。
  - 标准输出。
  - 存储设备的状态。
  - 当前可用的选择列表。

## 3. 状态检查器

`Mosaic` 类实现了状态空间的探索。其主要功能包括：

### 3.1 模型解释器

- `run(self)`：
  - 随机选择路径，模拟一次执行。
  - 通过 `OperatingSystem` 的 `replay` 方法，对选择序列进行重放，生成状态转移序列。
- `check(self)`：
  - 穷尽所有可能的状态转移，构建完整的状态转移图。
  - 使用广度优先搜索（BFS）探索所有路径，避免重复访问相同状态。

### 3.2 源码解析和转换

`Mosaic` 类通过 `ast.NodeTransformer` 自动将用户代码中的系统调用转换为生成器表达式。例如：

- 用户代码：`sys_write('Hello')`
- 转换后：`yield ('sys_write', ('Hello',))`

```python
class Transformer(ast.NodeTransformer):
    def visit_Call(self, node):
        if (isinstance(node.func, ast.Name) and node.func.id in SYSCALLS):
            return ast.Yield(ast.Tuple(
                elts=[
                    ast.Constant(value=node.func.id),
                    ast.Tuple(elts=node.args),
                ]
            ))
```

## 4. 命令行工具

支持通过命令行运行模拟器：

- `--run`：随机执行一次用户代码。
  ```bash
  # quick and dirty check
  python3 mosaic.py --check examples/hello.py | grep stdout | sort | uniq
  ```
- `--check`：穷尽所有可能状态，生成状态转移图。
  ```bash
  # interactive state explorer
  python3 mosaic.py --check examples/hello.py | python3 -m vis > examples/hello.html
  ```

## 总结

MOSAIC 通过精简的实现，成功模拟了一个多线程的操作系统模型和状态检查器。其设计思想如下：

1. 生成器与系统调用：利用生成器保存线程上下文，实现系统调用的挂起与恢复。
2. 非确定性选择：通过显式返回可能的选择，支持随机执行和状态空间穷举。
3. 状态快照：通过序列化操作系统的状态，支持状态转移图的构建和重放。
4. 代码转换：自动将用户代码中的系统调用转换为生成器表达式，简化用户交互。

该模型可以用于测试多线程程序的正确性（如竞争、死锁等）以及存储系统的崩溃一致性，非常适合分布式系统的研究和教学场景。
