from .原生 import 打开原生浏览器,浏览器输入#SDK
from .工作者rpc import 应答#RPC

__all__=['运行工作者']#仅中文公开名

def 运行工作者(配置,收件箱):#隔离工作者
    """在隔离线程里持有 Stagehand SDK。收件箱是队列。"""
    模式=配置.get('mode')#模式
    if 模式 not in ('launch','attach'):#非法
        raise Exception('Stagehand browser operation')#失败
    if not isinstance(配置.get('headless'),bool):#非法
        raise Exception('Stagehand browser operation')#失败
    if not isinstance(配置.get('operationTimeoutMs'),(int,float)) or 配置['operationTimeoutMs']<=0:#非法
        raise Exception('Stagehand browser operation')#失败
    if not isinstance(配置.get('shutdownGraceMs'),(int,float)) or 配置['shutdownGraceMs']<=0:#非法
        raise Exception('Stagehand browser operation')#失败
    打开=打开原生浏览器({#配置
        **{键:配置[键] for 键 in 配置 if 键 not in ('extensionId','cdpEndpoint','executablePath')},#其余
        **({} if 配置.get('extensionId') is None else {'extensionId':配置['extensionId']}),#扩展
        **({} if 配置.get('cdpEndpoint') is None else {'cdpEndpoint':配置['cdpEndpoint']}),#端点
        **({} if 配置.get('executablePath') is None else {'executablePath':配置['executablePath']}),#可执行
    })#打开
    方法集=frozenset(浏览器输入.keys())#封闭方法
    def 执行(方法,参数):#一次
        """就绪、关闭或一次浏览器操作。"""
        运行时=打开#SDK
        if 方法=='ready':#就绪
            return None#空
        if 方法=='close':#关
            运行时['close']()#关
            return None#空
        if 方法 not in 方法集:#非法
            raise Exception('Stagehand browser operation')#失败
        return 运行时['execute'](方法,参数)#执行
    while True:#循环
        原始=收件箱.get()#取
        if 原始 is None:#终止
            break#停
        try:#应答
            应答(原始,执行)#应答
        except Exception as 错误:#协议失败
            print('Stagehand Worker protocol failed:',错误)#日志
            break#停
