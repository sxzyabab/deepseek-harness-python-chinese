"""从宿主 worker 启动并监督 shell 进程。

进程是从这个同一束启动的 Web Worker，由其第一帧告知成为 shell 进程而非
宿主。这就是在浏览器中买到真进程语义的方式：命令在宿主线程外运行，
`terminate()` 即使中途循环也能停下它——协作式线程内解释器永远做不到的事。

在不存在 `Worker` 构造器处（Node 测试宿主），同一命令在本线程内联运行。
除抢占外一切行为相同，差异被点名而非隐藏：`destroy`
只能请求内联命令停止。

对齐上游 `webworker-runtime/src/shell/process/host.ts`。公开面仅中文名。
"""
from ..解释 import 运行shell命令,运行shell程序#解释器入口
from ..文件系统访问 import 宿主文件系统#宿主FS
from .子进程 import 运行shell进程#进程入口

__all__=['启动进程','运行shell进程']#仅中文公开名

def 可派worker():#是否可派Worker
    """本线程能否启动真进程 worker。"""
    # 对齐上游：typeof Worker === 'function' && self.location.href 为字符串
    Worker构造=globals().get('Worker')#浏览器Worker
    self对象=globals().get('self')#worker全局
    if not callable(Worker构造) or self对象 is None:#环境不具备
        return False#不可派
    位置=getattr(self对象,'location',None)#location
    href=getattr(位置,'href',None) if 位置 is not None else None#href
    return isinstance(href,str)#具备

def 服务文件系统调用(文件系统,操作,参数们):#服务FS调用
    """为进程 worker 服务一次文件系统调用。"""
    if 操作=='stat':#stat
        return 文件系统['stat'](参数们[0])#stat
    if 操作=='list':#list
        return 文件系统['list'](参数们[0])#list
    if 操作=='readText':#读文本
        return 文件系统['readText'](参数们[0])#读
    if 操作=='writeText':#写文本
        文件系统['writeText'](参数们[0],参数们[1],参数们[2] if len(参数们)>2 else False)#写
        return None#无返回值
    if 操作=='mkdir':#建目录
        文件系统['mkdir'](参数们[0],参数们[1])#mkdir
        return None#无返回值
    if 操作=='remove':#移除
        文件系统['remove'](参数们[0],参数们[1])#remove
        return None#无返回值
    if 操作=='rename':#重命名
        文件系统['rename'](参数们[0],参数们[1])#rename
        return None#无返回值
    raise Exception(f'webworker shell: unknown filesystem op {操作}')#拒绝未知

def 启动worker进程(选项):#Worker进程
    """worker 支撑的进程：本束的第二份拷贝，运行一条命令。"""
    文件系统=选项.get('fs') or 宿主文件系统()#选用FS
    Worker构造=globals()['Worker']#Worker
    self对象=globals()['self']#self
    worker=Worker构造(self对象.location.href,{'type':'module'})#同束新Worker
    已落定=[False]#是否已落定
    def 落定(码):#落定一次
        """落定一次。"""
        if 已落定[0]:#已落定则忽略
            return#忽略
        已落定[0]=True#标记落定
        worker.terminate()#终止Worker
        选项['onExit'](码)#报告退出
    def 收消息(事件):#收进程帧
        """处理出站帧。"""
        帧=事件['data'] if isinstance(事件,dict) else getattr(事件,'data',None)#出站帧
        if not isinstance(帧,dict):#非字典
            return#忽略
        if 帧.get('t')=='shell-out':#输出
            选项['onOutput'](帧['stream'],帧['text'])#转发
            return#处理完毕
        if 帧.get('t')=='shell-exit':#退出
            落定(帧['code'])#落定
            return#处理完毕
        try:#服务FS
            值=服务文件系统调用(文件系统,帧['op'],帧['args'])#服务
            worker.postMessage({'t':'fs-reply','id':帧['id'],'value':值})#成功回复
        except Exception as 错误:#失败
            失败={'code':getattr(错误,'code',None),'message':str(错误)}#失败载荷
            worker.postMessage({'t':'fs-reply','id':帧['id'],'failure':失败})#失败回复
    def 收错误(事件):#Worker错误
        """写诊断并失败落定。"""
        消息=getattr(事件,'message',str(事件))#消息
        选项['onOutput']('stderr',f'bash: process worker failed: {消息}\n')#写诊断
        落定(1)#失败落定
    worker.addEventListener('message',收消息)#收进程帧
    worker.addEventListener('error',收错误)#错误监听
    启动={#启动帧
        't':'shell-start',#类型
        'script':选项.get('script'),#脚本
        'argv':选项['argv'],#参数
        'cwd':选项['cwd'],#目录
        'env':选项['env'],#环境
        'stdin':选项['stdin'],#标准输入
    }#start结束
    worker.postMessage(启动)#发出启动
    def 软中断():#软中断
        """请求停止。"""
        if not 已落定[0]:#未落定
            worker.postMessage({'t':'shell-signal'})#发信号
    def 强制杀():#强制杀
        """立刻停止。"""
        落定(130)#强制杀
    return {'interrupt':软中断,'destroy':强制杀}#返回句柄

def 启动内联进程(选项):#内联进程
    """内联进程：本线程上的同一命令，只能通过请求停止。"""
    中止={'aborted':False}#取消标志
    def 加监听(类型,回调,选项面=None):#挂监听
        """对齐 addEventListener。"""
        中止.setdefault('_listeners',{}).setdefault(类型,[]).append(回调)#登记
    def 卸监听(类型,回调):#卸监听
        """对齐 removeEventListener。"""
        列表=中止.get('_listeners',{}).get(类型,[])#列表
        中止['_listeners'][类型]=[丙 for 丙 in 列表 if 丙 is not 回调]#过滤
    中止['addEventListener']=加监听#挂面
    中止['removeEventListener']=卸监听#挂面
    运行选项={#运行选项
        'cwd':选项['cwd'],#目录
        'env':选项['env'],#环境
        'stdin':选项['stdin'],#标准输入
        'signal':中止,#信号
        'fs':选项.get('fs') or 宿主文件系统(),#FS
        'onOutput':选项['onOutput'],#输出
    }#runOptions结束
    try:#执行
        if 选项.get('script') is None:#直接程序
            结果=运行shell程序(选项['argv'],运行选项)#直接
        else:#脚本
            结果=运行shell命令(选项['script'],运行选项)#脚本
        选项['onExit'](结果['exitCode'])#成功退出
    except Exception as 错误:#失败
        选项['onOutput']('stderr',f'bash: {错误}\n')#诊断
        选项['onExit'](1)#失败码
    def 停止():#请求停止
        """请求停止。"""
        中止['aborted']=True#中止
        for 回调 in list(中止.get('_listeners',{}).get('abort',[])):#通知
            回调()#回调
    return {'interrupt':停止,'destroy':停止}#两者同为请求

def 启动进程(选项):#启动进程
    """启动一条命令。"""
    return 启动worker进程(选项) if 可派worker() else 启动内联进程(选项)#选路径
