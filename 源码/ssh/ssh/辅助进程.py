import hashlib,os,sys,threading,uuid#摘要、路径、平台、租期与流 id
import tempfile,shutil#临时根与删除
from ...依赖 import cordis#上下文
from ...依赖.工具 import 二进制#base64
from ...文件系统.文件系统 import 文件系统错误#整文超限
from ...文件系统.文件系统沙盒 import 沙箱文件系统#沙箱 fs
from ...子进程.子进程 import 可执行未找到错误#查找失败
from ...子进程.本地子进程 import 本地子进程运行时#本地进程
from ...沙盒.本地沙盒 import 本地沙箱提供方#本地沙箱
from ...沙盒.沙盒策略 import 沙箱政策服务#政策
from ...会话.会话投影 import 会话投影注册表#投影
from ...工具.超时 import 中止控制器,若已中止则抛出,已中止,合成信号#中止
from .协议 import ssh请求对等,远程操作错误,ssh进程句柄上限,ssh文本流上限,ssh协议版本#对等
from .远端进程 import 远端进程#进程表
from .模式 import (
    编辑模式,#编辑
    环境模式,#环境
    意图模式,#写意图
    政策模式,#政策
    进程标识模式,#进程 id
    远端路径,#路径
    目标模式,#目标
    文本流标识模式,#流 id
    ssh错误,#基类
)#模式结束

__all__=['运行ssh辅助']#仅中文公开名

最大帧字节=64*1024*1024#帧上限
最大文本字节=8*1024*1024#整文上限

def 空对象(值):#z.object({}).strict()
    """空对象。"""
    if not isinstance(值,dict) or len(值)>0:#非空
        raise ssh错误('expected empty object')#失败
    return 值#空

def 进程标识请求(值):#{id}
    """只含 id。"""
    if not isinstance(值,dict) or 'id' not in 值:#缺
        raise ssh错误('expected process id')#失败
    return {'id':进程标识模式(值['id'])}#id

def 文本流标识请求(值):#{id}
    """只含流 id。"""
    if not isinstance(值,dict) or 'id' not in 值:#缺
        raise ssh错误('expected text stream id')#失败
    return {'id':文本流标识模式(值['id'])}#id

def 装服务():#本地提供方
    """挂投影、政策、沙箱 fs、本地进程与本地沙箱。"""
    上下文=cordis.上下文()#根
    纤程表=[]#拆除序
    def 挂(插件,配置=None):#启动并等待
        """启动插件并记下纤程。"""
        纤程=上下文.启动插件(插件,配置)#启动
        纤程.等待()#启动失败则抛
        纤程表.append(纤程)#记下
    挂(会话投影注册表)#投影
    挂(沙箱政策服务,{'mode':'read-only','workspaceRoot':os.getcwd()})#政策
    挂(沙箱文件系统,{'cwd':os.getcwd()})#fs
    挂(本地子进程运行时)#进程
    挂(本地沙箱提供方)#沙箱
    def 关闭():#逆序拆除
        """逆序拆除纤程。"""
        for 纤程 in reversed(纤程表):#逆序
            if 纤程.拆除 is not None:#有拆除器
                纤程.拆除()#拆
    return {'ctx':上下文,'close':关闭}#运行时

def 运行ssh辅助(传输):#跑到通道关闭或租期到期
    """传输含 input/output/entryPath/signal。"""
    平台=sys.platform#平台
    if 平台!='linux' and not 平台.startswith('linux') and 平台!='darwin':#非 POSIX
        raise ssh错误('SSH helper requires a POSIX host')#拒绝
    若已中止则抛出(传输['signal'])#已中止
    运行时=装服务()#服务
    上下文=运行时['ctx']#上下文
    根=tempfile.mkdtemp(prefix='dsh-ssh-',dir='/tmp')#套接字根
    进程表=远端进程(上下文,根,ssh进程句柄上限,30000)#进程
    寿命=中止控制器()#寿命
    迭代器表={}#流 id → 记录
    租期定时=None#租期
    租期毫秒=30000#默认
    已握手=False#hello
    工作区=os.getcwd()#默认 cwd
    清理任务={'值':None}#只跑一次

    def 关闭():#关闭辅助
        """停租期、中止迭代器、关进程、拆服务、删根。"""
        if 清理任务['值'] is not None:#已开始
            清理任务['值'].wait()#等
            return#结束
        完成=threading.Event()#完成
        清理任务['值']=完成#记下
        def 跑():#线程
            """一次清理。"""
            nonlocal 租期定时#改
            try:#清理
                if 租期定时 is not None:#有定时
                    租期定时.cancel()#清
                寿命.中止(ssh错误('SSH helper is closing'))#中止
                for 记录 in 迭代器表.values():#流
                    记录['controller'].中止(寿命.信号)#中止
                    迭代器=记录['iterator']#迭代器
                    if hasattr(迭代器,'close'):#生成器
                        try:#关
                            迭代器.close()#关
                        except BaseException:#忽略
                            pass#吞
                迭代器表.clear()#清空
                try:#进程
                    进程表.关闭()#关
                finally:#服务与根
                    try:#服务
                        运行时['close']()#拆
                    finally:#根
                        shutil.rmtree(根,ignore_errors=True)#删
            finally:#广播
                完成.set()#完
        threading.Thread(target=跑).start()#清理
        完成.wait()#等

    def 续租():#重置租期
        """到期则关闭对等。"""
        nonlocal 租期定时#改
        if 租期定时 is not None:#旧
            租期定时.cancel()#清
        def 到期():#租期到
            """关闭对等。"""
            对等.关闭(ssh错误('SSH helper client lease expired'))#关
        租期定时=threading.Timer(租期毫秒/1000.0,到期)#定时
        租期定时.daemon=True#守护
        租期定时.start()#武装

    def 解析政策(原始,信号):#政策
        """规范化 workspaceRoot。"""
        已解析=政策模式(原始)#校验
        目标=上下文.fs.解析(已解析['workspaceRoot'],{'signal':信号})#解析
        结果=dict(已解析)#拷
        结果['workspaceRoot']=上下文.fs.进程路径(目标)#进程路径
        return 结果#政策

    def 作目标(原始):#目标
        """校验目标。"""
        return 目标模式(原始)#目标

    def 处理(方法,原始,请求信号):#入站
        """hello 之后的私有操作。"""
        信号=合成信号(请求信号,寿命.信号)#融合
        if 方法=='hello':#握手
            if 已握手:#重复
                raise ssh错误('SSH helper handshake already completed')#拒绝
            if not isinstance(原始,dict):#非对象
                raise ssh错误('expected hello object')#失败
            if 原始.get('protocol')!=ssh协议版本:#版本
                raise ssh错误('expected protocol 1')#失败
            工作区路径=远端路径(原始.get('workspace'))#工作区
            租=原始.get('leaseMs')#租期
            if isinstance(租,bool) or not isinstance(租,int) or 租<3000 or 租>600000:#范围
                raise ssh错误('expected leaseMs')#失败
            引导=原始.get('bootstrapPath')#可选引导
            if 引导 is not None:#有
                远端路径(引导)#路径
            nonlocal 工作区,租期毫秒,已握手#改
            工作区=上下文.fs.进程路径(上下文.fs.解析(工作区路径,{'signal':信号}))#规范化
            租期毫秒=租#记下
            已握手=True#完成
            续租()#开租
            入口字节=open(传输['entryPath'],'rb').read()#入口
            结果={
                'protocol':ssh协议版本,#版本
                'hash':hashlib.sha256(入口字节).hexdigest(),#摘要
                'platform':'linux' if 平台=='linux' or 平台.startswith('linux') else 'darwin',#平台
                'nodeVersion':sys.version.split()[0],#解释器版本
                'node':sys.executable.replace('\\','/') if not sys.executable.startswith('/') else sys.executable,#可执行
                'root':根,#套接字根
                'workspace':工作区,#工作区
            }#握手
            if 引导 is not None:#有引导
                结果['bootstrapHash']=hashlib.sha256(open(引导,'rb').read()).hexdigest()#引导摘要
            return 结果#hello
        if (not 已握手) or 清理任务['值'] is not None:#未握手或关闭中
            raise ssh错误('SSH helper is not accepting operations')#拒绝
        if 方法=='heartbeat':#心跳
            空对象(原始)#空
            续租()#续
            return None#空
        if 方法=='close':#关闭
            空对象(原始)#空
            关闭()#关
            return None#空
        if 方法=='process.prepare':#准备
            return 进程表.准备(原始)#预留
        if 方法=='process.start':#启动
            return 进程表.启动(进程标识请求(原始)['id'],信号)#启动
        if 方法=='process.done':#完成
            return 进程表.完成(进程标识请求(原始)['id'])#完成
        if 方法=='process.wait':#等待
            return 进程表.等待(进程标识请求(原始)['id'],信号)#观察
        if 方法=='process.terminate':#终止
            进程表.终止(进程标识请求(原始)['id'])#终止
            return None#空
        if 方法=='terminal.environment':#终端环境
            空对象(原始)#空
            return 上下文.subprocess.终端环境(信号)#环境
        if 方法=='terminal.resize':#尺寸
            if not isinstance(原始,dict):#非对象
                raise ssh错误('expected resize object')#失败
            进程表.调整终端尺寸(进程标识模式(原始.get('id')),原始['cols'],原始['rows'])#调
            return None#空
        if 方法=='terminal.write' or 方法=='terminal.inspect' or 方法=='terminal.activity' or 方法=='terminal.signal':#终端操作
            if not isinstance(原始,dict):#非对象
                raise ssh错误('expected terminal object')#失败
            if 方法=='terminal.write':#写
                操作='write'#写
            elif 方法=='terminal.inspect':#前台
                操作='inspect'#检查
            elif 方法=='terminal.activity':#活动
                操作='activity'#活动
            else:#信号
                操作='signal'#信号
            return 进程表.终端操作(进程标识模式(原始.get('id')),操作,原始.get('value'))#操作
        if 方法=='executable':#可执行
            if not isinstance(原始,dict) or 'command' not in 原始:#缺
                raise ssh错误('expected command')#失败
            环境=None if 原始.get('env') is None else {键:值 for 键,值 in 环境模式(原始['env']).items() if 值 is not None}#去掉墓碑
            try:#解析
                return 上下文.subprocess.解析可执行文件(原始['command'],环境,信号)#路径
            except 可执行未找到错误 as 错误:#未找到
                raise 远程操作错误(str(错误),'SUBPROCESS_EXECUTABLE_NOT_FOUND')#提升
        if 方法=='sandbox':#沙箱包装
            if not isinstance(原始,dict):#非对象
                raise ssh错误('expected sandbox object')#失败
            已解析=解析政策(原始['policy'],信号)#政策
            if 已解析['mode']=='danger-full-access':#无须包装
                raise ssh错误('Unconfined argv does not need a sandbox wrapper')#拒绝
            return 上下文.sandbox.隔离(原始['argv'],已解析)#隔离
        if 方法=='fs.resolve' or 方法=='fs.lstat':#路径
            if not isinstance(原始,dict):#非对象
                raise ssh错误('expected path object')#失败
            选项={'cwd':原始['cwd'] if 原始.get('cwd') is not None else 工作区,'signal':信号}#选项
            if 方法=='fs.resolve':#解析
                return 上下文.fs.解析(原始['path'],选项)#目标
            信息=上下文.fs.链接状态(原始['path'],选项,信号)#lstat
            return 信息#可空
        if 方法=='fs.stat' or 方法=='fs.list' or 方法=='fs.readText' or 方法=='fs.stream':#目标操作
            目标=作目标(原始['target'] if isinstance(原始,dict) and 'target' in 原始 else 原始)#目标
            if 方法=='fs.stat':#stat
                return 上下文.fs.状态(目标,信号)#信息
            if 方法=='fs.list':#列举
                return 上下文.fs.列目录(目标,信号)#项
            if 方法=='fs.stream':#开流
                if len(迭代器表)>=ssh文本流上限:#满
                    raise ssh错误('SSH text stream limit reached')#满
                控制器=中止控制器()#流寿命
                融合=合成信号(信号,控制器.信号)#融合
                流=上下文.fs.流文本(目标,融合)#生成器
                迭代器=iter(流)#迭代器
                try:#登记
                    若已中止则抛出(信号)#中止
                    if len(迭代器表)>=ssh文本流上限:#满
                        raise ssh错误('SSH text stream limit reached')#满
                    标识=str(uuid.uuid4())#流 id
                    迭代器表[标识]={'iterator':迭代器,'controller':控制器}#登记
                    return 标识#id
                except BaseException as 错误:#失败
                    控制器.中止(错误 if isinstance(错误,BaseException) else ssh错误(str(错误)))#中止
                    if hasattr(迭代器,'close'):#关
                        迭代器.close()#关
                    raise 错误#原样
            流=上下文.fs.流文本(目标,信号)#整文
            文本=''#累积
            字节=0#字节
            for 块 in 流:#逐块
                字节+=len(块.encode('utf-8'))#UTF-8
                if 字节>最大文本字节:#超
                    raise 文件系统错误('SSH whole-text transfer exceeds its bounded frame budget; use streaming','FS_TOO_LARGE')#超限
                文本+=块#追加
            return 文本#整文
        if 方法=='fs.next' or 方法=='fs.streamClose':#流拉取
            标识=文本流标识请求(原始)['id']#id
            记录=迭代器表.get(标识)#记录
            if 记录 is None:#未知
                raise ssh错误('Unknown SSH text stream')#拒绝
            if 方法=='fs.streamClose':#关
                del 迭代器表[标识]#摘
                记录['controller'].中止(ssh错误('SSH text stream closed'))#中止
                if hasattr(记录['iterator'],'close'):#关
                    记录['iterator'].close()#关
                return None#空
            若已中止则抛出(信号)#中止
            try:#下一
                值=next(记录['iterator'])#下一块
                return {'done':False,'value':值}#未结束
            except StopIteration:#结束
                del 迭代器表[标识]#摘
                return {'done':True,'value':''}#结束
            except BaseException as 错误:#失败
                if 标识 in 迭代器表:#仍在
                    del 迭代器表[标识]#摘
                记录['controller'].中止(错误 if isinstance(错误,BaseException) else ssh错误(str(错误)))#中止
                if hasattr(记录['iterator'],'close'):#关
                    记录['iterator'].close()#关
                raise 错误#原样
        if 方法=='fs.readBytes' or 方法=='fs.readRange':#字节
            if not isinstance(原始,dict):#非对象
                raise ssh错误('expected byte request')#失败
            目标=作目标(原始['target'])#目标
            if 方法=='fs.readBytes':#整文件有界
                上限=原始.get('maxBytes')#上限
                if isinstance(上限,bool) or not isinstance(上限,int) or 上限<0:#非法
                    raise ssh错误('expected nonnegative maxBytes')#失败
                字节=上下文.fs.读字节(目标,信号,min(上限,最大文本字节))#读
            else:#窗口
                偏移=原始.get('offset')#偏移
                长度=原始.get('length')#长度
                if isinstance(偏移,bool) or not isinstance(偏移,int) or 偏移<0:#非法
                    raise ssh错误('expected nonnegative offset')#失败
                if isinstance(长度,bool) or not isinstance(长度,int) or 长度<0 or 长度>最大文本字节:#非法
                    raise ssh错误('expected length')#失败
                字节=上下文.fs.读字节范围(目标,{'offset':偏移,'length':长度},信号)#窗口
            return 二进制.转base64(字节 if isinstance(字节,bytes) else bytes(字节))#base64
        if 方法=='fs.write' or 方法=='fs.edit':#变更
            if not isinstance(原始,dict):#非对象
                raise ssh错误('expected mutation')#失败
            目标=作目标(原始['target'])#目标
            已解析=解析政策(原始['policy'],信号)#政策
            if 方法=='fs.write':#写
                内容=原始.get('content')#内容
                if not isinstance(内容,str):#须字符串
                    raise ssh错误('expected content string')#失败
                期望=None if 原始.get('expected') is None else 意图模式(原始['expected'])#意图
                return 上下文.fs.写文本(目标,内容,期望,信号,已解析)#写
            编辑=编辑模式(原始.get('edit'))#编辑
            期望=None#版本
            if 原始.get('expected') is not None:#有
                期望=原始['expected']#原样
            return 上下文.fs.编辑文本(目标,编辑,期望,信号,已解析)#编辑
        raise ssh错误('Unknown SSH helper operation: '+方法)#未知

    对等=ssh请求对等(传输['input'],传输['output'],最大帧字节,128,处理)#对等
    已关闭=threading.Event()#通道关闭
    def 对等已关(错误=None):#closed
        """启动清理。"""
        threading.Thread(target=关闭).start()#清理
        已关闭.set()#广播
    对等.关闭回调.append(对等已关)#监听
    def 传输中止():#transport abort
        """关对等。"""
        对等.关闭(ssh错误('SSH helper transport was terminated'))#关
    信号=传输['signal']#寿命
    if 已中止(信号):#已中止
        传输中止()#立刻
    else:#监视
        def 监视():#等
            """置位后关。"""
            if hasattr(信号,'wait'):#Event
                信号.wait()#等
            传输中止()#关
        threading.Thread(target=监视,daemon=True).start()#监视
        续租()#开租
    已关闭.wait()#等通道
    关闭()#再确保清理
