'把生成的 Typert Remote 描述符装到客户端。方法查找不经过 JavaScript Proxy'
import json,threading#挂载串行与诊断
from ....依赖.cordis.服务 import 服务#服务基类
from ....类型化远程调用.协议 import 远程错误,是否远程上行项,取远程错误#失败与上行项
from ....客户端.连接.rpc import 中止控制器,订进程内事件,取进程内网关#挂载令牌、本进程事件与宿主网关
from ..异常 import 远程流载体错误#载体失败
from ..流协议 import 已中止,若中止则抛,合并信号#取消
from .客户端 import 远程流复用客户端,客户端上行队列#复用套接字与上行队列
from .远程事件 import 客户端远程事件#转发事件
from .远程流 import 远程流 as 远程流类#可重连流。下面再导出模块本身
from . import 日志流,远程事件,快照流,客户端 as 流客户端#同目录模块
from . import 远程流#模块。类名留给 远程流类

依赖=['typert','connection']#Typert 注册表和连接
inject=依赖#框架槽
命名空间保留字段=frozenset(['ctx','empty','invokeRemote','methods','name','namespace'])#不能当方法名

def 拼端点(描述符):
    'namespace/method'
    return 描述符['namespace']+'/'+描述符['method']#端点

def 远程服务键(命名空间):
    'remote. 前缀'
    return 'remote.'+命名空间#服务键

def 内部失败(消息):
    'gateway/internal，细节为空'
    return {'ok':False,'error':远程错误('gateway/internal',消息,{})}#失败

def 已撤回(端点):
    '方法已不再挂载'
    return 内部失败('client api: Remote method '+端点+' is no longer mounted')#失败

def 载体失败(端点,错误):
    '载体抛出折成 gateway/internal'
    消息=错误.message if isinstance(错误,BaseException) and isinstance(getattr(错误,'message',None),str) else str(错误)#说明
    return 内部失败('client api: '+端点+' failed: '+消息)#失败

def 取消失败(端点,原因):
    '调用方中止折成 gateway/cancelled，载体抛出作为 cause'
    因果=原因 if isinstance(原因,BaseException) else None#原因
    return {'ok':False,'error':远程错误('gateway/cancelled','client api: Remote invocation "'+端点+'" was aborted',{},因果)}#失败

def 是远程失败(错误):
    '用远程错误标记判断。其它本地故障应让调用方崩溃'
    return 取远程错误(错误) is not None#是否

def 要求严格编解码(编解码,端点,字段):
    '弱模式不允许出现在客户端生成描述符'
    if not isinstance(编解码,dict) or 编解码.get('mode')!='strict':#不是严格
        raise Exception('client api: generated Remote '+端点+' field '+json.dumps(字段)+' has no strict codec')#拒绝

def 要求严格输入(描述符):
    '参数、上行和 Context 身份都必须是严格编解码'
    端点=拼端点(描述符)#端点
    for 参数 in 描述符['parameters']:#参数
        要求严格编解码(参数['codec'],端点,参数['wire'])#参数
    if 描述符.get('uplink') is not None:#有上行
        要求严格编解码(描述符['uplink']['codec'],端点,'uplink')#上行
    if 描述符['invocation']['kind']=='context':#上下文身份
        要求严格编解码(描述符['invocation']['codec'],端点,描述符['invocation']['wire'])#身份

def 作用域投影(描述符):
    'Context 调用，或 scope 加上唯一的 lookup'
    if 描述符['invocation']['kind']=='context':#上下文
        return {'context':描述符['invocation']['context'],'wire':描述符['invocation']['wire']}#投影
    if 描述符.get('scope') is None:#没有 scope
        return None#不是作用域
    查找=[]#lookup 参数
    for 下标,参数 in enumerate(描述符['parameters']):#带下标
        if 参数.get('source')=='lookup':#查找
            查找.append((参数,下标))#记下
    选中=查找[0] if len(查找)==1 else None#必须恰好一个
    if (选中 is None
            or 选中[0]['wire']!=描述符['scope']['wire']
            or 选中[0].get('lookup')!=描述符['scope']['context']):#对不上
        raise Exception('client api: generated Remote '+拼端点(描述符)+' scope must select its only lookup parameter')#拒绝
    return {'context':描述符['scope']['context'],'wire':描述符['scope']['wire'],'parameterIndex':选中[1]}#投影

def 挂载仍在(令牌):
    '令牌还没被拆除'
    return 令牌['active'] is True#还在

def 安装方法(服务,描述符列表):
    '把一组描述符装到命名空间。中途失败则回滚这一组'
    已装=[]#已安装
    try:#回滚
        for 描述符 in 描述符列表:#逐个
            方法={'descriptor':描述符,'token':{'active':True,'abort':中止控制器()},'direct':False,'scoped':False}#记录
            已装.append(方法)#先记下，失败好回滚
            if 描述符['invocation']['kind']=='direct':#直接
                服务.installDirect(描述符,方法['token'])#装
                方法['direct']=True#记下
            投影=作用域投影(描述符)#作用域
            if 投影 is not None:#有
                服务.installScoped(描述符,投影,方法['token'])#装
                方法['scoped']=True#记下
    except Exception:#回滚
        for 方法 in reversed(已装):#逆序
            方法['token']['active']=False#作废
            方法['token']['abort'].abort()#取消进行中的调用
            if 方法['scoped']:#卸作用域
                服务.remove('scoped',方法['descriptor']['method'],方法['token'])#卸
            if 方法['direct']:#卸直接
                服务.remove('direct',方法['descriptor']['method'],方法['token'])#卸
        raise#再抛
    return 已装#记录

class 远程命名空间服务(服务):
    '一个命名空间上的直接调用和作用域调用'
    def __init__(自身,上下文,名,调用远程):
        '以 remote.命名空间 登记'
        super().__init__(上下文,远程服务键(名))#服务键
        自身.namespace=名#命名空间
        自身.invokeRemote=调用远程#真正发出调用
        自身.methods={ }#方法到记录

    @staticmethod
    def 断言方法可用(命名空间,方法):
        '保留字段或原型成员则抛'
        if 方法 in 命名空间保留字段 or 方法 in ('assertMethodAvailable','empty','has','installDirect','installScoped','remove','断言方法可用','安装'):#撞车
            raise Exception('client api: method '+json.dumps(命名空间+'/'+方法)+' conflicts with its namespace service')#拒绝

    def assertMethodAvailable(自身,方法):
        '连实例自有字段一起检查'
        远程命名空间服务.断言方法可用(自身.namespace,方法)#保留字段
        if hasattr(自身,方法) and 方法 not in 自身.methods:#实例上已有别的东西
            raise Exception('client api: method '+json.dumps(自身.namespace+'/'+方法)+' conflicts with its namespace service')#拒绝

    @property
    def empty(自身):
        '表空则为空'
        return len(自身.methods)==0#空

    def has(自身,种类,方法):
        '对应槽非空'
        记录=自身.methods.get(方法)#记录
        if 记录 is None:#没有
            return False#无
        return 记录.get(种类) is not None#有这一种

    def installDirect(自身,描述符,令牌):
        '写入 direct 槽'
        自身._安装(描述符['method'],'direct',{'descriptor':描述符,'token':令牌})#装

    def installScoped(自身,描述符,投影,令牌):
        '写入 scoped 槽'
        自身._安装(描述符['method'],'scoped',{'descriptor':描述符,'projection':投影,'token':令牌})#装

    def _安装(自身,方法,种类,值):
        '首次定义访问器，再写入对应槽'
        自身.assertMethodAvailable(方法)#先检查
        记录=自身.methods.get(方法)#已有
        新建=记录 is None#第一次
        if 记录 is None:#新建
            记录={ }#空记录
        if 新建:#定义方法。每次调用都读当前槽
            def 调用(*参数,方法=方法):
                '读当前的直接槽和作用域槽再发出'
                调用方=自身.ctx#调用纤程
                当前=自身.methods.get(方法)#当前记录
                直接槽=None if 当前 is None else 当前.get('direct')#直接
                作用域槽=None if 当前 is None else 当前.get('scoped')#作用域
                return 自身.invokeRemote(直接槽,作用域槽,调用方,参数)#调用
            setattr(自身,方法,调用)#方法
            自身.methods[方法]=记录#登记
        if 种类=='direct':#直接
            记录['direct']=值#写入
        else:#作用域
            记录['scoped']=值#写入

    def remove(自身,种类,方法,令牌):
        '没有记录或令牌不是自己则不动'
        记录=自身.methods.get(方法)#记录
        当前=None if 记录 is None else 记录.get(种类)#这一槽
        if 记录 is None or 当前 is None or 当前.get('token') is not 令牌:#不是自己
            return#不动
        if 种类=='direct':#卸直接
            记录.pop('direct',None)#卸
        else:#卸作用域
            记录.pop('scoped',None)#卸
        if 记录.get('direct') is not None or 记录.get('scoped') is not None:#还有另一种
            return#留着访问器
        自身.methods.pop(方法,None)#方法没了
        if hasattr(自身,方法):#访问器
            delattr(自身,方法)#摘掉

class 客户端流句柄:
    '生成的流方法返回的一代逻辑流'
    def __init__(自身,端点,下行,上行,代际,令牌):
        '先拉一次，让 open 帧在 send 之前出去'
        自身._端点=端点#端点
        自身._上行=上行#上行队列
        自身._代际=代际#这一代取消
        自身._令牌=令牌#挂载令牌
        自身._下行=iter(下行)#下行迭代
        自身._预取=None#第一项
        自身._已消费=False#只有一个读者
        自身._已拆除=False#dispose
        try:#预取可能失败，失败等到读者
            自身._预取={'值':next(自身._下行),'结束':False}#第一项
        except StopIteration:#空
            自身._预取={'结束':True}#结束
        except Exception as 错误:#失败
            自身._预取={'错误':错误}#等读者
            自身._上行.close()#之后 send 抛

    def send(自身,项):
        '送一条上行。必须是无损 JSON 或顶层空'
        if not 是否远程上行项(项):#不合法
            raise Exception('client api: '+自身._端点+' uplink item is not a lossless JSON value')#拒绝
        自身._上行.push(项)#入队

    def end(自身):
        '半关上行'
        自身._上行.end()#半关

    def dispose(自身):
        '中止这一代并交还载体迭代器'
        if 自身._已拆除:#已经
            return#停
        自身._已拆除=True#占住
        自身._上行.close()#关闭队列
        自身._代际.abort(Exception('client api: '+自身._端点+' stream disposed'))#取消
        关闭=getattr(自身._下行,'close',None)#生成器
        if callable(关闭):#有
            try:#不把关闭失败抛给调用方
                关闭()#交还
            except Exception:#忽略
                pass#忽略

    def __iter__(自身):
        '单消费者'
        if 自身._已消费:#第二个
            raise Exception('client api: '+自身._端点+' stream has one consumer')#拒绝
        自身._已消费=True#占住
        return 自身._迭代()#生成器

    def _迭代(自身):
        '读预取，然后读下行'
        try:#结束即拆除
            while True:#直到结束
                if 自身._预取 is not None:#用掉预取
                    下一项=自身._预取#预取
                    自身._预取=None#只用一次
                else:#继续
                    try:#读
                        下一项={'值':next(自身._下行),'结束':False}#项
                    except StopIteration:#结束
                        下一项={'结束':True}#结束
                if 自身._已拆除 or 下一项.get('结束'):#拆了或结束
                    return#停
                if '错误' in 下一项:#预取失败
                    raise 下一项['错误']#抛
                if not 挂载仍在(自身._令牌):#方法被卸了
                    raise Exception(已撤回(自身._端点)['error'].message)#撤回
                yield 下一项['值']#一项
        except Exception:#失败
            if 自身._已拆除:#拆除导致的
                return#静默
            raise#原样
        finally:#结束即拆除
            自身.dispose()#拆除
            关闭=getattr(自身._下行,'close',None)#再交还一次
            if callable(关闭):#有
                try:#可能已经关了
                    关闭()#交还
                except Exception:#忽略
                    pass#忽略

class 客户端远程服务(服务):
    '安装带类型的客户端远程服务'
    def __init__(自身,上下文):
        '以 remote 登记。应答客户端才挂事件'
        super().__init__(上下文,'remote')#服务键
        自身.ownerCtx=上下文#根
        连接=上下文.获取服务('connection') if hasattr(上下文,'获取服务') else 上下文.connection#连接
        自身._连接=连接#连接
        自身.namespaces={ }#命名空间句柄
        自身._宿主事实=None#上次的 $host
        交互=getattr(连接,'interactions',None)#应答或被动
        def 打开套接字(路径):
            '连接提供的已认证套接字'
            return 连接.openWebSocket(路径)#打开
        自身._流=远程流复用客户端(打开套接字,交互=='answer')#复用
        自身._事件=None#转发事件
        自身._进程内=getattr(连接.rpc,'进程内',False) is True#宿主在本进程，不走浏览器流
        if 交互=='answer' and not 自身._进程内:#应答客户端，事件流在浏览器或壳上
            def 打开事件流(端点,载荷,信号):
                '事件流走和普通流一样的打开器'
                return 自身._打开远程流(端点,载荷,信号)#打开
            自身._事件=客户端远程事件(上下文,连接,打开事件流)#事件
        打开=None#进程内打开器
        rpc=getattr(连接,'rpc',None)#rpc
        if isinstance(rpc,dict):#字典
            打开=rpc.get('open')#可能没有
        else:#对象
            打开=getattr(rpc,'open',None)#可能没有
        if 打开 is None and 交互!='none':#没有进程内流，而且这条连接要去找宿主
            自身._流.start()#自己连
        已拆除={'v':False}#卸载
        循环={'v':None}#连接循环
        def 启动():
            '加载器就绪后启动。none 不启动。本进程的事件不靠这条循环'
            if 已拆除['v'] or getattr(连接,'interactions',None)=='none' or 自身._进程内:#不该开浏览器循环
                return#停
            if 打开 is None:#没有进程内
                自身._流.start()#保证有尝试
            def 已连接():
                '连接重置'
                自身.ownerCtx.广播('connection/reset')#事件
            def 要求重连():
                '没有进程内流时重连套接字'
                if 打开 is None:#需要套接字
                    自身._流.reconnect()#重连
            循环['v']=连接.start({'onConnected':已连接,'onReconnectRequested':要求重连})#循环
        加载器=上下文.反射.获取服务('loader')#加载器
        if 加载器 is None:#没有
            启动()#马上
        else:#等加载器
            等待=getattr(加载器,'await',None)#可能是协程
            if callable(等待):#有
                try:#同步等
                    等待()#等
                    启动()#然后启动
                except Exception:#加载失败也别挡住卸载
                    pass#上游 then 的失败分支是空
            else:#没有 await
                启动()#马上
        def 效应():
            '卸载时停循环、事件和套接字'
            def 拆除():
                '停'
                已拆除['v']=True#标记
                if 循环['v'] is not None and hasattr(循环['v'],'stop'):#有循环
                    循环['v'].stop()#停
                if 自身._事件 is not None:#有事件
                    自身._事件.拆除()#等静默
                自身._流.close()#关套接字
            return 拆除#拆除器
        上下文.副作用(效应,'api-gateway.client.transport')#生命周期
        自身._变更锁=threading.Lock()#挂载串行

    def 打开逻辑流(自身,选项):
        '创建一条可独立取消、可重连的逻辑流。被动客户端用生成的流方法'
        if getattr(自身._连接,'interactions',None)=='none':#被动
            raise Exception('client api: $stream requires interactions=answer; use a generated stream method')#拒绝
        return 远程流类(自身._连接,选项)#流

    @property
    def 宿主事实(自身):
        '宿主事实。home 在第一帧就绪前是 None。同一事实复用同一个对象'
        快照=自身._连接.generation.getSnapshot()#当前代际
        家=None#就绪前没有
        if isinstance(快照,dict):#字典快照
            宿主=快照.get('host')#宿主
            if isinstance(宿主,dict):#有 home
                家=宿主.get('home')#家目录
        elif 快照 is not None:#对象快照
            宿主=getattr(快照,'host',None)#宿主
            家=getattr(宿主,'home',None)#家目录
        if 自身._宿主事实 is None or 自身._宿主事实['home']!=家:#变了才换对象
            自身._宿主事实={'home':家,'isLoopback':自身._连接.isLoopback}#新对象
        return 自身._宿主事实#稳定引用

    def 挂载远程(自身,贡献):
        '把挂载纳入调用方效果'
        调用方=自身.ctx#调用纤程
        def 效应():
            '进入时安装，离开时卸载'
            def 安装():
                '串行安装这一份贡献'
                return 自身._挂载贡献(调用方,贡献)#安装
            拆除=自身._入队(安装)#串行安装
            def 卸载():
                '串行卸载'
                自身._入队(拆除)#串行
            return 卸载#拆除器
        return 调用方.副作用(效应,'api-gateway.client.$mount('+json.dumps(贡献.get('package'))+')')#效果

    def 订阅事件(自身,事件,监听器):
        '转发事件。本进程直接订宿主。被动客户端没有'
        if 自身._进程内:#宿主在本进程
            return 订进程内事件(事件,监听器)#不走浏览器
        if 自身._事件 is None:#没有
            raise Exception('client api: forwarded events require interactions=answer')#拒绝
        return 自身._事件.订阅(自身.ctx,事件,监听器)#登记

    def _打开远程流(自身,端点,载荷,信号,上行=None):
        '进程内流优先。没有则走复用套接字'
        连接=自身.ownerCtx.反射.获取服务('connection')#当前连接
        if 连接 is None:#没有
            raise Exception('client api: '+端点+' has no active Connection')#拒绝
        rpc=连接.rpc if not isinstance(连接,dict) else 连接['rpc']#rpc
        打开=None#进程内
        if isinstance(rpc,dict):#字典
            打开=rpc.get('open')#打开器
        else:#对象
            打开=getattr(rpc,'open',None)#打开器
        if callable(打开):#有进程内
            本地=打开('/api',端点,载荷,信号,上行)#本地流
            if 本地 is not None:#用它
                return 自身._归一连接流(本地)#还原错误类
        return 自身._流.open(端点,载荷,信号,上行)#套接字

    def _归一连接流(自身,源):
        '工作线程传来的结构失败还原成远程错误或载体错误'
        try:#原样产出
            for 值 in 源:#逐项
                yield 值#项
        except Exception as 错误:#可能带标记
            标记=getattr(错误,'dshRemoteStreamFailure',None)#标记
            if isinstance(标记,dict) and 标记.get('kind')=='remote':#远程失败
                raise 远程错误(标记['code'],str(错误),标记.get('details') or {})#还原
            if isinstance(标记,dict) and 标记.get('kind')=='carrier':#载体
                raise 远程流载体错误(str(错误),错误)#还原
            raise#原样

    def _入队(自身,操作):
        '挂载和卸载串行。操作是函数'
        with 自身._变更锁:#串行
            return 操作()#执行

    def _挂载贡献(自身,调用方,贡献):
        '先校验，再按命名空间安装。中途失败回滚'
        自身._校验贡献(贡献)#校验
        卸远程=调用方.typert.remotes.register(贡献)#登记描述符
        分组={ }#命名空间到描述符
        for 描述符 in 贡献['descriptors']:#分组
            组=分组.get(描述符['namespace'])#已有
            if 组 is None:#新建
                分组[描述符['namespace']]=[描述符]#一组
            else:#追加
                组.append(描述符)#追加
        已装=[]#卸载器
        try:#回滚
            for 命名空间,描述符列表 in 分组.items():#逐组
                已装.append(自身._安装命名空间(命名空间,描述符列表))#安装
        except Exception as 错误:#回滚
            for 拆除 in reversed(已装):#逆序
                拆除()#卸
            if callable(卸远程):#卸注册
                卸远程()#卸
            raise 错误#再抛
        def 拆除():
            '卸这一组和远程登记'
            for 卸 in reversed(已装):#逆序
                卸()#卸
            if callable(卸远程):#卸注册
                卸远程()#卸
        return 拆除#拆除器

    def _校验贡献(自身,贡献):
        '本贡献内以及和已挂载的命名空间不冲突'
        直接={ }#命名空间到方法集合
        作用域={ }#命名空间到方法集合
        def 添加(表,描述符,种类):
            '重复则抛'
            方法集=表.get(描述符['namespace'])#已有
            if 方法集 is None:#新建
                方法集=set()#空
                表[描述符['namespace']]=方法集#记下
            if 描述符['method'] in 方法集:#重复
                raise Exception('client api: contribution repeats '+种类+' method '+拼端点(描述符))#拒绝
            方法集.add(描述符['method'])#记下
            已有=自身.namespaces.get(描述符['namespace'])#已挂载
            服务=None if 已有 is None else 已有['service']#服务
            if 服务 is not None and 服务.has(种类,描述符['method']):#已经装了
                raise Exception('client api: '+种类+' method '+拼端点(描述符)+' is already mounted')#拒绝
        for 描述符 in 贡献['descriptors']:#逐个
            要求严格输入(描述符)#严格编解码
            if 描述符['invocation']['kind']=='direct':#直接
                添加(直接,描述符,'direct')#记
            if 作用域投影(描述符) is not None:#作用域
                添加(作用域,描述符,'scoped')#记
        名字=set(直接)|set(作用域)#全部命名空间
        for 命名空间 in 名字:#逐个
            已有=自身.namespaces.get(命名空间)#已挂载
            服务=None if 已有 is None else 已有['service']#服务
            if 服务 is None:#新建命名空间
                if hasattr(自身,命名空间):#撞上 remote 服务自己的字段
                    raise Exception('client api: namespace '+json.dumps(命名空间)+' conflicts with the Remote service')#拒绝
                键=远程服务键(命名空间)#服务键
                属性=自身.ownerCtx.反射.属性表.get(键)#已有属性
                if (属性 is not None and 属性.get('类型')=='访问器') or 自身.ownerCtx.反射.获取服务(键) is not None:#撞车
                    raise Exception('client api: namespace '+json.dumps(命名空间)+' conflicts with an existing Remote namespace')#拒绝
            方法集=set()#这一命名空间的方法
            方法集.update(直接.get(命名空间) or ())#直接
            方法集.update(作用域.get(命名空间) or ())#作用域
            for 方法 in 方法集:#逐个
                if 服务 is None:#还没服务
                    远程命名空间服务.断言方法可用(命名空间,方法)#保留字段
                else:#已有服务
                    服务.assertMethodAvailable(方法)#实例字段

    def _安装命名空间(自身,名,描述符列表):
        '新命名空间在插件 apply 里同步装完一整组'
        已有=自身.namespaces.get(名)#已有
        if 已有 is None:#新建
            盒={ }#服务和已装
            def 应用(上下文,配置=None):
                '同一同步窗口里创建服务并安装方法'
                服务对象=远程命名空间服务(上下文,名,自身._调用方法)#服务
                盒['service']=服务对象#记下
                盒['installed']=安装方法(服务对象,描述符列表)#安装
            纤程=自身.ownerCtx.启动插件({'name':远程服务键(名),'apply':应用})#插件
            if hasattr(纤程,'等待'):#等激活
                纤程.等待()#等
            if 'service' not in 盒 or 'installed' not in 盒:#没起来
                if hasattr(纤程,'拆除'):#卸
                    纤程.拆除()#卸
                raise Exception('client api: namespace '+json.dumps(名)+' did not start')#拒绝
            def 空拆除():
                '插件没有拆除方法时的空操作'
                return None
            拆除插件=纤程.拆除 if hasattr(纤程,'拆除') else 空拆除#拆除
            句柄={'service':盒['service'],'dispose':拆除插件}#句柄
            自身.namespaces[名]=句柄#登记
            已装=盒['installed']#记录
        else:#追加到已有命名空间
            句柄=已有#句柄
            已装=安装方法(句柄['service'],描述符列表)#安装
        def 拆除(句柄=句柄,已装=已装,名=名):
            '逆序卸方法，空了再卸命名空间'
            for 方法 in reversed(已装):#逆序
                if not 方法['token']['active']:#已经卸过
                    continue#跳
                方法['token']['active']=False#作废
                方法['token']['abort'].abort()#取消
                if 方法['scoped']:#作用域
                    句柄['service'].remove('scoped',方法['descriptor']['method'],方法['token'])#卸
                if 方法['direct']:#直接
                    句柄['service'].remove('direct',方法['descriptor']['method'],方法['token'])#卸
            自身._卸命名空间(名,句柄)#空了才卸服务
        return 拆除#拆除器

    def _卸命名空间(自身,名,句柄):
        '命名空间已空且仍是当前句柄时拆除'
        if not 句柄['service'].empty or 自身.namespaces.get(名) is not 句柄:#还有方法或已换
            return#留着
        自身.namespaces.pop(名,None)#摘
        拆除=句柄.get('dispose')#插件拆除
        if callable(拆除):#有
            拆除()#卸

    def _调用方法(自身,直接,作用域,调用方,值列表):
        '有身份则走作用域。否则直接。只有作用域则仍走作用域'
        if 作用域 is not None:#有作用域
            适配器=自身.ownerCtx.typert.contexts.getClient(作用域['projection']['context'])#适配器
            身份=None#身份
            if 适配器 is not None:#有
                身份=适配器['identity'](调用方) if isinstance(适配器,dict) else 适配器.identity(调用方)#取身份
            if 身份 is not None:#当前上下文能提供身份
                return 自身._调用选中(作用域['descriptor'],作用域['projection'],作用域['token'],调用方,值列表,{'value':身份})#作用域
        if 直接 is not None:#直接
            return 自身._调用选中(直接['descriptor'],None,直接['token'],调用方,值列表)#直接
        if 作用域 is not None:#只有作用域
            return 自身._调用选中(作用域['descriptor'],作用域['projection'],作用域['token'],调用方,值列表)#仍走作用域
        raise Exception('client api: Remote method is no longer mounted')#卸了

    def _是流(自身,描述符):
        '流可以标在描述符上，也可以标在调用标记上'
        if 描述符.get('mode')=='stream':#描述符
            return True#流
        调用标记=描述符.get('invocation')#调用标记
        return isinstance(调用标记,dict) and 调用标记.get('mode')=='stream'#流

    def _进程内对象(自身,描述符,投影,令牌,调用方,值列表,已绑身份=None):
        '直接调用宿主方法。流把生成器交回去，一元把返回值放进信封'
        端点=拼端点(描述符)#端点
        if not 令牌['active']:#已卸
            if 自身._是流(描述符):#流
                raise Exception(已撤回(端点)['error'].message)#撤回
            return 已撤回(端点)#一元失败
        准备=自身._准备调用(描述符,投影,令牌,调用方,值列表,已绑身份)#参数
        网关=取进程内网关()#宿主
        if 网关 is None:#还没起来。启动期不能把插件带倒
            if 自身._是流(描述符):#没有帧
                def 空流():
                    '宿主网关还没起来'
                    if False:#空生成器
                        yield None#不会执行
                return 空流()#调用方迭代完就结束
            return {'ok':False,'error':{'code':'gateway/unavailable','message':'connection: 本进程没有宿主网关','details':{}}}#一元失败信封
        对象=网关.直接执行(端点,{'args':准备['args']},准备['signal'])#宿主对象
        if 自身._是流(描述符):#调用方按帧迭代
            return 对象#生成器
        return {'ok':True,'value':对象}#一元仍是信封，值是对象本身

    def _调用选中(自身,描述符,投影,令牌,调用方,值列表,已绑身份=None):
        '流方法返回句柄。一元方法返回结果。本进程直接交宿主对象'
        if 自身._进程内:#不走远程载体
            return 自身._进程内对象(描述符,投影,令牌,调用方,值列表,已绑身份)#对象
        if 描述符.get('mode') is not None:#流
            return 自身._调用流(描述符,投影,令牌,调用方,值列表,已绑身份)#流
        return 自身._调用(描述符,投影,令牌,调用方,值列表,已绑身份)#一元

    def _调用(自身,描述符,投影,令牌,调用方,值列表,已绑身份=None):
        '一元 RPC'
        端点=拼端点(描述符)#端点
        if not 令牌['active']:#已卸
            return 已撤回(端点)#失败结果
        准备=自身._准备调用(描述符,投影,令牌,调用方,值列表,已绑身份)#参数
        连接=自身.ownerCtx.反射.获取服务('connection')#连接
        if 连接 is None:#没有
            raise Exception('client api: '+端点+' has no active Connection')#拒绝
        try:#调用
            结果=连接.rpc.call('/api',端点,{'args':准备['args']},准备['signal'])#RPC
            if not 挂载仍在(令牌):#中途卸了
                return 已撤回(端点)#撤回
            若中止则抛(准备['signal'])#取消
            if not 结果['ok']:#失败
                错误=结果['error']#线路错误
                return {'ok':False,'error':远程错误(错误['code'],错误['message'],错误.get('details') or {})}#还原成异常
            值=结果.get('value')#值
            if 描述符['result'].get('mode')=='strict' and callable(描述符['result'].get('decode')):#严格解码
                值=描述符['result']['decode'](值)#解码
            return {'ok':True,'value':值}#成功
        except Exception as 错误:#载体抛出
            if 已中止(准备['signal']):#调用方取消
                return 取消失败(端点,错误)#取消
            return 载体失败(端点,错误)#载体

    def _调用流(自身,描述符,投影,令牌,调用方,值列表,已绑身份=None):
        '现在打开逻辑流，send 在第一次读之前会排在 open 后面'
        端点=拼端点(描述符)#端点
        if not 令牌['active']:#已卸
            raise Exception(已撤回(端点)['error'].message)#撤回
        准备=自身._准备调用(描述符,投影,令牌,调用方,值列表,已绑身份)#参数
        代际=中止控制器()#这一代
        上行=客户端上行队列(端点)#上行
        下行=自身._打开远程流(端点,{'args':准备['args']},合并信号(准备['signal'],代际.signal),上行)#下行
        return 客户端流句柄(端点,下行,上行,代际,令牌)#句柄

    def _准备调用(自身,描述符,投影,令牌,调用方,值列表,已绑身份=None):
        '组线路参数，并合并挂载取消和调用方信号'
        端点=拼端点(描述符)#端点
        期望=len(描述符['parameters'])-(0 if 投影 is None or 投影.get('parameterIndex') is None else 1)#业务参数个数
        有调用方信号=描述符.get('cancellation') is not None and len(值列表)==期望+1#多带了一个信号
        if len(值列表)!=期望 and not 有调用方信号:#个数不对
            if 描述符.get('cancellation') is None:#不能带信号
                合同=str(期望)+' argument(s)'#个数
            else:#可以带信号
                合同=str(期望)+' business argument(s) plus an optional AbortSignal'#个数
            raise Exception('client api: '+端点+' expected '+合同+', got '+str(len(值列表)))#拒绝
        参数={ }#线路参数
        if 投影 is not None:#要身份
            适配器=None#适配器
            if 已绑身份 is None:#还没绑
                适配器=自身.ownerCtx.typert.contexts.getClient(投影['context'])#适配器
            if 已绑身份 is None and 适配器 is None:#没有适配器
                raise Exception('client api: '+端点+' has no Client Context adapter for '+json.dumps(投影['context']))#拒绝
            if 已绑身份 is None:#从调用方取
                身份=适配器['identity'](调用方) if isinstance(适配器,dict) else 适配器.identity(调用方)#身份
            else:#已经绑了
                身份=已绑身份['value']#值
            if 身份 is None:#没有上下文
                raise Exception('client api: '+端点+' requires a '+json.dumps(投影['context'])+' Context')#拒绝
            参数[投影['wire']]=身份#写入
        值下标=0#业务参数下标
        for 参数下标,参数描述 in enumerate(描述符['parameters']):#逐个
            if 投影 is not None and 参数下标==投影.get('parameterIndex'):#身份占了这个参数
                continue#跳
            值=值列表[值下标]#对应值
            if 值 is not None:#空不写，省略字段
                参数[参数描述['wire']]=值#写入
            值下标+=1#前进
        调用方信号=值列表[期望] if 有调用方信号 else None#可选信号
        if 调用方信号 is None:#只用挂载取消
            信号=令牌['abort'].signal#挂载
        else:#合并
            信号=合并信号(令牌['abort'].signal,调用方信号)#两路
        return {'endpoint':端点,'args':参数,'signal':信号}#准备结果

setattr(客户端远程服务,'$stream',客户端远程服务.打开逻辑流)#协议名
setattr(客户端远程服务,'$host',客户端远程服务.宿主事实)#协议名
setattr(客户端远程服务,'$mount',客户端远程服务.挂载远程)#协议名
setattr(客户端远程服务,'$on',客户端远程服务.订阅事件)#协议名

def 应用(上下文,配置=None):
    '在客户端根上挂载 Remote 服务'
    客户端远程服务(上下文)#安装

apply=应用#框架槽
__all__=[#公开名
    '依赖','应用','apply','客户端远程服务','远程命名空间服务',
    '载体失败','取消失败','是远程失败','远程流载体错误',
    '日志流','远程事件','远程流','快照流','流客户端',
]#公开面结束
