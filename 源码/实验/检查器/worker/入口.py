"""实验性检查器的 Worker 引导入口。"""
#对齐上游 worker/entry.ts

from ....内核.智能体循环.辅助 import 解开,在线程跑#可等待则等待|后台跑
from .服务器 import 启动检查器Worker#装配并启动

__all__=['主入口']#仅中文公开名

def 主入口(控制端口,启动数据):#主入口
    """在子进程/线程中校验启动数据并装配 Worker。"""
    if 控制端口 is None:#主线程误载
        raise RuntimeError('experimental inspector: Worker entry loaded on the main thread')#主线程误载则抛错
    if not isinstance(启动数据,dict) or 'hostSourcePort' not in 启动数据:#启动数据无效
        raise RuntimeError('experimental inspector: invalid Worker boot data')#启动数据无效
    启动包={#Worker启动包
        'hostSourcePort':启动数据['hostSourcePort'],#Host源端口
        'config':启动数据['config'],#配置（由上层已解析）
    }#boot结束
    运行时=[None]#运行时盒
    停止中=[None]#停止中的任务盒

    def 停止():#停止Worker
        """惰性单次停止。"""
        if 停止中[0] is not None:#已停
            return 解开(停止中[0])#复用
        def 体():#停止体
            """关闭运行时并通知。"""
            if 运行时[0] is not None:#有运行时
                解开(运行时[0]['close']())#关闭运行时
            控制端口.postMessage({'type':'stopped'})#通知已停
            控制端口.close()#关闭控制口
        停止中[0]=在线程跑(体)#登记
        return 解开(停止中[0])#返回

    def 收控制(消息):#收到Host控制消息
        """解析并停止。"""
        try:#解析并停止
            if not isinstance(消息,dict) or 消息.get('type')!='stop':#非法控制
                raise ValueError('invalid host control')#校验控制帧
            在线程跑(停止)#触发停止
        except Exception as 错误:#控制帧失败
            控制端口.postMessage({'type':'failure','message':str(错误)})#回传失败

    控制端口.on('message',收控制)#消息监听
    def 启动():#启动运行时
        """装配并回传就绪。"""
        try:#启动
            运行时[0]=解开(启动检查器Worker(启动包))#装配并启动
            控制端口.postMessage({'type':'ready',**运行时[0]['endpoint']})#就绪
        except Exception as 错误:#启动失败
            控制端口.postMessage({'type':'failure','message':str(错误)})#回传失败
            停止()#清理退出
    return 启动#返回启动工厂
