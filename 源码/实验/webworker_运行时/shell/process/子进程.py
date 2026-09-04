"""进程 worker 自己的半边：收到 shell 启动帧的新 worker 在此运行
一条命令然后关闭。

它不挂载 VFS 镜像、不启动 Cordis 树、不加载插件——与宿主 worker 共享的
唯一东西是启动它的那个束。其文件系统是宿主的，经消息到达。

对齐上游 `webworker-runtime/src/shell/process/child.ts`。公开面仅中文名。
"""
import threading as 线程#等待文件系统回复
from ..解释 import 运行shell命令,运行shell程序#解释器入口
from ..文件系统访问 import 文件系统错误#FS错误构造

__all__=['运行shell进程']#仅中文公开名

def 运行shell进程(启动,作用域):#运行进程命令
    """将运行一条命令作为本 worker 的全部用途，然后关闭。"""
    待回复={}#待回复调用
    终止={'aborted':False,'_listeners':{}}#终止信号面
    下一调用=[0]#下一调用id
    锁=线程.Lock()#保护待回复

    def 中止(原因=None):#触发取消
        """对齐 AbortController.abort。"""
        终止['aborted']=True#标记
        for 回调 in list(终止.get('_listeners',{}).get('abort',[])):#通知
            回调()#回调
        终止['_listeners']['abort']=[]#清

    def 加监听(类型,回调,选项=None):#挂监听
        """对齐 addEventListener。"""
        终止.setdefault('_listeners',{}).setdefault(类型,[]).append(回调)#登记

    def 卸监听(类型,回调):#卸监听
        """对齐 removeEventListener。"""
        列表=终止.get('_listeners',{}).get(类型,[])#列表
        终止['_listeners'][类型]=[丙 for 丙 in 列表 if 丙 is not 回调]#过滤

    终止['addEventListener']=加监听#挂面
    终止['removeEventListener']=卸监听#挂面
    终止['abort']=中止#挂面

    def 收消息(事件):#监听宿主消息
        """处理宿主帧。"""
        帧=事件['data'] if isinstance(事件,dict) else getattr(事件,'data',事件)#入站帧
        if not isinstance(帧,dict):#非字典
            return#忽略
        if 帧.get('t')=='shell-signal':#终止信号
            中止(Exception('killed by signal'))#触发取消
            return#处理完毕
        if 帧.get('t')!='fs-reply':#非回复忽略
            return#忽略
        with 锁:#取等待者
            等待=待回复.pop(帧['id'],None)#取
        if 等待 is None:#无等待者
            return#忽略
        if 帧.get('failure') is None:#成功结算
            等待['result']=帧.get('value')#结果
            等待['event'].set()#唤醒
        else:#失败结算
            失败=帧['failure']#失败载荷
            等待['error']=文件系统错误(失败.get('code') or 'EIO','fs',失败['message'])#错误
            等待['event'].set()#唤醒

    作用域['addEventListener']('message',收消息)#监听宿主消息

    def 调用(操作,参数):#发FS调用
        """发调用并阻塞等回复。"""
        下一调用[0]+=1#分配id
        标识=下一调用[0]#本次id
        事件=线程.Event()#等待事件
        等待={'event':事件,'result':None,'error':None}#等待者
        with 锁:#挂等待
            待回复[标识]=等待#登记
        作用域['postMessage']({'t':'fs-call','id':标识,'op':操作,'args':参数})#发调用帧
        事件.wait()#等回复
        if 等待['error'] is not None:#失败
            raise 等待['error']#抛错
        return 等待['result']#成功值

    def 远程stat(路径):#远程stat
        """stat。"""
        return 调用('stat',[路径])#调用
    def 远程list(路径):#远程list
        """list。"""
        return 调用('list',[路径])#调用
    def 远程读文本(路径):#远程读文本
        """读文本。"""
        return 调用('readText',[路径])#调用
    def 远程写文本(路径,文本,追加=False):#远程写
        """写文本。"""
        调用('writeText',[路径,文本,追加])#调用
    def 远程mkdir(路径,递归):#远程mkdir
        """mkdir。"""
        调用('mkdir',[路径,递归])#调用
    def 远程remove(路径,选项):#远程remove
        """remove。"""
        调用('remove',[路径,选项])#调用
    def 远程rename(源,目标):#远程rename
        """rename。"""
        调用('rename',[源,目标])#调用

    文件系统={#消息后端FS
        'stat':远程stat,#远程stat
        'list':远程list,#远程list
        'readText':远程读文本,#远程读文本
        'writeText':远程写文本,#远程写
        'mkdir':远程mkdir,#远程mkdir
        'remove':远程remove,#远程remove
        'rename':远程rename,#远程rename
    }#fs结束

    def 输出回调(流,文本):#转发输出
        """写入时即转发。"""
        作用域['postMessage']({'t':'shell-out','stream':流,'text':文本})#转发

    选项={#运行选项
        'cwd':启动['cwd'],#工作目录
        'env':启动['env'],#环境
        'stdin':启动['stdin'],#标准输入
        'signal':终止,#取消信号
        'fs':文件系统,#消息FS
        'onOutput':输出回调,#转发输出
    }#options结束
    try:#选运行路径
        if 启动.get('script') is None:#直接程序
            结果=运行shell程序(启动['argv'],选项)#直接程序
        else:#脚本解释
            结果=运行shell命令(启动['script'],选项)#脚本
        作用域['postMessage']({'t':'shell-exit','code':结果['exitCode']})#报告退出
        作用域['close']()#关闭worker
    except Exception as 错误:#失败
        作用域['postMessage']({'t':'shell-out','stream':'stderr','text':f'bash: {错误}\n'})#写诊断
        作用域['postMessage']({'t':'shell-exit','code':1})#失败退出码
        作用域['close']()#关闭worker
