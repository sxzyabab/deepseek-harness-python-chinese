import time,threading,psutil,platform

class 线程:
    @staticmethod
    def 线程数():
        return threading.active_count()
    @staticmethod
    def 总线程数():
        return len(threading.enumerate())
    @staticmethod
    def 线程ID():
        return threading.get_ident()
    @staticmethod
    def 线程名():
        return threading.current_thread().name
    @staticmethod
    def 当前线程状态():
        return threading.current_thread().is_alive()

class 进程:
    @staticmethod
    def 内存占用信息():
        return psutil.Process().memory_info()
    @staticmethod
    def 物理内存占用():
        return psutil.Process().memory_info().rss
    @staticmethod
    def 虚拟内存占用():
        return psutil.Process().memory_info().vms
    @staticmethod
    def 内存占用峰值():
        return psutil.Process().memory_info().peak_wset
    @staticmethod
    def PID():
        return psutil.Process().pid
    @staticmethod
    def 进程名():
        return psutil.Process().name()
    @staticmethod
    def 进程命令行():
        return psutil.Process().cmdline()
    @staticmethod
    def 进程启动时刻():
        return psutil.Process().create_time()
    @staticmethod
    def 进程运行时长():
        return time.time()-psutil.Process().create_time()
    @staticmethod
    def 句柄数():
        return psutil.Process().num_handles()
    @staticmethod
    def 打开文件数():
        return len(psutil.Process().open_files())
    @staticmethod
    def 网络累计发送():
        return psutil.Process().network_io_counters().bytes_sent
    @staticmethod
    def 网络累计接收():
        return psutil.Process().network_io_counters().bytes_recv
    @staticmethod
    def 磁盘累计读取():
        return psutil.Process().io_counters().read_bytes
    @staticmethod
    def 磁盘累计写入():
        return psutil.Process().io_counters().write_bytes

class CPU:
    @staticmethod
    def 逻辑核心数():
        return psutil.cpu_count(logical=True)
    @staticmethod
    def 物理核心数():
        return psutil.cpu_count(logical=False)
    @staticmethod
    def 总和使用率():
        return psutil.cpu_percent()
    @staticmethod
    def 每核使用率():
        return psutil.cpu_percent(percpu=True)
    @staticmethod
    def 当前进程使用率():
        return psutil.Process().cpu_percent()

class 内存:
    @staticmethod
    def 大小():
        return psutil.virtual_memory().total
    @staticmethod
    def 可用():
        return psutil.virtual_memory().available
    @staticmethod
    def 使用率():
        return psutil.virtual_memory().percent

class 网络:
    @staticmethod
    def 发送速度():
        return 网络.累计发送()
    @staticmethod
    def 接收速度():
        return 网络.累计接收()
    @staticmethod
    def 累计发送():
        return psutil.net_io_counters().bytes_sent
    @staticmethod
    def 累计接收():
        return psutil.net_io_counters().bytes_recv
    @staticmethod
    def 网卡信息():
        return psutil.net_if_addrs()
    @staticmethod
    def tcp连接数():
        return len(psutil.net_connections(kind='tcp'))
    @staticmethod
    def udp连接数():
        return len(psutil.net_connections(kind='udp'))
    @staticmethod
    def 所有连接数():
        return len(psutil.net_connections(kind='all'))

class 磁盘:
    @staticmethod
    def 读取速度():
        return 磁盘.累计读取()
    @staticmethod
    def 写入速度():
        return 磁盘.累计写入()
    @staticmethod
    def 累计读取():
        return psutil.disk_io_counters().read_bytes
    @staticmethod
    def 累计写入():
        return psutil.disk_io_counters().write_bytes
    @staticmethod
    def 总容量(路径:str):
        return psutil.disk_usage(路径).total
    @staticmethod
    def 已用(路径:str):
        return psutil.disk_usage(路径).used
    @staticmethod
    def 可用(路径:str):
        return psutil.disk_usage(路径).free
    @staticmethod
    def 使用率(路径:str):
        return psutil.disk_usage(路径).percent

class 系统:
    @staticmethod
    def 开机时刻():
        return psutil.boot_time()
    @staticmethod
    def 运行时长():
        return time.time()-系统.开机时刻()
    @staticmethod
    def 用户名():
        return psutil.Process().username()
    @staticmethod
    def 系统类型():
        return platform.system()
    @staticmethod
    def 系统架构():
        return platform.machine()
    @staticmethod
    def 系统位数():
        return platform.architecture()[0]

def 时间戳():
    return int(time.time()*1000)

def 格式化字节数(字节数:int):
    if 字节数 < 1024:
        return f"{字节数} B"
    elif 字节数 < 1024*1024:
        return f"{字节数/1024:.2f} KB"
    elif 字节数 < 1024*1024*1024:
        return f"{字节数/1024/1024:.2f} MB"
    elif 字节数 < 1024*1024*1024*1024:
        return f"{字节数/1024/1024/1024:.2f} GB"
    else:
        return f"{字节数/1024/1024/1024/1024:.2f} TB"

def 格式化时间秒数(秒数:float):
    if 秒数 < 60:
        return f"{秒数:.2f} 秒"
    elif 秒数 < 60*60:
        return f"{秒数/60:.2f} 分钟"
    elif 秒数 < 60*60*24:
        return f"{秒数/60/60:.2f} 小时"
    elif 秒数 < 60*60*24*30:
        return f"{秒数/60/60/24:.2f} 天"
    elif 秒数 < 60*60*24*365:
        return f"{秒数/60/60/24/30:.2f} 月"
    else:
        return f"{秒数/60/60/24/365:.2f} 年"

if __name__=='__main__':
    print(f"线程数 {线程.线程数()}")
    print(f"总线程数 {线程.总线程数()}")
    print(f"线程ID {线程.线程ID()}")
    print(f"线程名 {线程.线程名()}")
    print(f"当前线程状态 {线程.当前线程状态()}")
    print(f"进程号 {进程.PID()}")
    print(f"进程名 {进程.进程名()}")
    print(f"进程命令行 {进程.进程命令行()}")
    print(f"进程启动时刻 {进程.进程启动时刻()}")
    print(f"进程运行时长 {格式化时间秒数(进程.进程运行时长())}")
    print(f"进程内存信息 {进程.内存占用信息()}")
    print(f"进程物理内存 {格式化字节数(进程.物理内存占用())}")
    print(f"进程虚拟内存 {格式化字节数(进程.虚拟内存占用())}")
    print(f"进程内存峰值 {格式化字节数(进程.内存占用峰值())}")
    print(f"句柄数 {进程.句柄数()}")
    print(f"打开文件数 {进程.打开文件数()}")
    print(f"进程磁盘累计读取 {格式化字节数(进程.磁盘累计读取())}")
    print(f"进程磁盘累计写入 {格式化字节数(进程.磁盘累计写入())}")
    print(f"逻辑核心数 {CPU.逻辑核心数()}")
    print(f"物理核心数 {CPU.物理核心数()}")
    print(f"CPU使用率 {CPU.总和使用率()}")#第一次常常是0
    print(f"CPU每核使用率 {CPU.每核使用率()}")
    print(f"当前进程CPU使用率 {CPU.当前进程使用率()}")#第一次常常是0
    print(f"内存大小 {格式化字节数(内存.大小())}")
    print(f"内存可用 {格式化字节数(内存.可用())}")
    print(f"内存使用率 {内存.使用率()}%")
    print(f"网络发送 {格式化字节数(网络.发送速度())}")
    print(f"网络接收 {格式化字节数(网络.接收速度())}")
    print(f"网络累计发送 {格式化字节数(网络.累计发送())}")
    print(f"网络累计接收 {格式化字节数(网络.累计接收())}")
    print(f"网卡信息 {repr(网络.网卡信息())}")
    print(f"tcp连接数 {网络.tcp连接数()}")
    print(f"udp连接数 {网络.udp连接数()}")
    print(f"所有连接数 {网络.所有连接数()}")
    print(f"磁盘读取速度 {格式化字节数(磁盘.读取速度())}")
    print(f"磁盘写入速度 {格式化字节数(磁盘.写入速度())}")
    print(f"磁盘累计读取 {格式化字节数(磁盘.累计读取())}")
    print(f"磁盘累计写入 {格式化字节数(磁盘.累计写入())}")
    print(f"磁盘总容量 {格式化字节数(磁盘.总容量('.'))}")
    print(f"磁盘已用 {格式化字节数(磁盘.已用('.'))}")
    print(f"磁盘可用 {格式化字节数(磁盘.可用('.'))}")
    print(f"磁盘使用率 {磁盘.使用率('.')}%")
    print(f"开机时刻 {系统.开机时刻()}")
    print(f"运行时长 {格式化时间秒数(系统.运行时长())}")
    print(f"用户名 {系统.用户名()}")
    print(f"系统类型 {系统.系统类型()}")
    print(f"系统架构 {系统.系统架构()}")
    print(f"系统位数 {系统.系统位数()}")
    print(f"时间戳 {时间戳()}")
