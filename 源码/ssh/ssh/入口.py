import sys,signal as 信号模块#参数与终止信号
from ...工具.超时 import 中止控制器#进程寿命
from .模式 import ssh错误#本包基类
from .辅助进程 import 运行ssh辅助#辅助运行
from .流安全 import 套接字流#标准流入面

__all__=['主入口']#仅中文公开名

def 包装标准流(缓冲):#给请求对等用
    """把二进制缓冲包成套接字流面；标准流用文件对象读写。"""
    class 文件流(套接字流):#文件对象面
        """覆盖读写到文件缓冲。"""
        def __init__(自身,文件):#记下
            """不持有真实套接字。"""
            自身._文件=文件#缓冲
            自身._监听={'error':[],'close':[],'connect':[],'data':[],'drain':[],'secureConnect':[]}#事件
            自身.closed=False#是否已关
        def write(自身,字节):#写
            """写入缓冲。"""
            自身._文件.write(字节)#写
            自身._文件.flush()#立刻送出
            return True#已接受
        def read(自身,大小):#读
            """读缓冲。"""
            return 自身._文件.read(大小)#读
        def destroy(自身,错误=None):#关
            """标记关闭。"""
            if 自身.closed:#已关
                return#忽略
            自身.closed=True#记下
            if 错误 is not None:#有因
                for 回调 in list(自身._监听['error']):#错误
                    回调(错误)#通知
            for 回调 in list(自身._监听['close']):#关闭
                回调()#通知
    return 文件流(缓冲)#面

def 主入口():#OpenSSH 进程入口
    """辅助模块拥有请求与清理；本入口只接线与信号。"""
    控制器=中止控制器()#寿命
    def 停止(信号号,帧):#终止信号
        """中止辅助运行。"""
        控制器.中止(ssh错误('SSH helper process terminated'))#中止
    for 名 in ('SIGTERM','SIGHUP','SIGINT'):#终止信号
        信号模块.signal(getattr(信号模块,名),停止)#一次登记
    try:#运行
        if len(sys.argv)!=1:#除脚本名外还有参数
            raise ssh错误('SSH helper accepts no command arguments')#拒绝
        运行ssh辅助({
            'input':包装标准流(sys.stdin.buffer),#OpenSSH exec 标准入
            'output':包装标准流(sys.stdout.buffer),#只走 exec 标准出
            'entryPath':__file__,#入口路径供摘要
            'signal':控制器.信号,#寿命
        })#运行直到通道关闭
    except BaseException as 错误:#失败
        消息=错误.args[0] if isinstance(错误,BaseException) and len(错误.args)>0 else str(错误)#消息
        sys.stderr.write('dsh-ssh-sandbox: '+str(消息)+'\n')#诊断
        sys.exit(127)#约定退出
    finally:#摘信号
        for 名 in ('SIGTERM','SIGHUP','SIGINT'):#信号
            信号模块.signal(getattr(信号模块,名),信号模块.SIG_DFL)#恢复

if __name__=='__main__':#进程入口
    主入口()#启动
