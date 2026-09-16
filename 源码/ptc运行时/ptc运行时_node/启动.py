"""在挂载的执行世界里选择源码或构建后的引导资产。"""
import os,sys#路径与冻结探测
from .协议 import 节点ptc错误#本包异常

__all__=['启动配置字段','引导参数']#仅中文公开名

启动配置字段=('nodeExecutable','bootstrapPath')#部署拥有的 Node 可执行与可选预装引导

def 映到进程世界(文件系统,路径):#把宿主路径映到子进程世界
    """把宿主绝对路径映到子进程执行世界。文件系统是对象。"""
    结果=文件系统.宿主路径转进程路径(路径)#后端映射
    if 结果 is None:#执行世界读不到
        raise 节点ptc错误('PTC runtime bootstrap is unavailable in the subprocess execution world: '+路径)#不可用
    return 结果#进程路径

def 引导参数(文件系统,配置,最大消息字节):#选出跟在已解析 Node 可执行后面的参数
    """选出不继承宿主加载器或调试器标志的显式参数。文件系统把宿主引导资产映进进程世界。配置可带预装构建后引导。最大消息字节是已校验的帧与排队写入上限。返回跟在已解析 Node 可执行后面的参数。"""
    if 'bootstrapPath' in 配置 and 配置['bootstrapPath'] is not None:#显式预装
        return [配置['bootstrapPath'],str(最大消息字节)]#预装路径加上限
    if hasattr(sys,'frozen'):#打包可执行
        return [str(最大消息字节)]#只传上限
    入口=os.path.join(os.path.dirname(os.path.abspath(__file__)),'进程入口.py')#本包子进程入口
    return [映到进程世界(文件系统,入口),str(最大消息字节)]#映射后的入口加上限
