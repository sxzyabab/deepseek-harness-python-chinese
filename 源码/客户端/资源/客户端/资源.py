'按地址登记资源提供方，并保住每条地址的活快照'
from json import dumps as 转json#效果标签里的协议名
from threading import Event as 事件#流的中止旗
from types import SimpleNamespace as 简单命名空间#一条记录和它的源
from urllib.parse import urlparse as 解析网址#地址里的协议名
from ....基础设施.通用工具 import 启动守护线程#消费流不挡住登记
from ...存储 import 创建快照存储#按地址的快照

__all__=['资源方案','取协议','资源注册表']#本文件公开名

资源方案='dsh-resource'#资源地址的方案，不带冒号


def 取协议(地址):
    'dsh-resource 地址的 host，小写。解析失败或其它方案都没有协议'
    try:#地址解析器拒绝的字符串不是资源地址
        解析=解析网址(地址)#按网址读
    except ValueError:#没有方案或括号不配
        return None#不是资源地址
    if 解析.scheme!=资源方案:#不是 dsh-resource
        return None#导航地址或普通文件地址
    主机=解析.hostname#host。空主机是 None
    if 主机 is None or 主机=='':#没有 host
        return None#不是资源地址
    return 主机.lower()#收成小写


def 空闲(状态):
    '没有值和失败的快照'
    return {'status':状态,'value':None,'failure':None}#三个字段都在


class 流信号(事件):
    '交给 open 的中止旗。aborted 对齐 AbortSignal，等待和置位沿用 Event'
    def abort(自身):
        '中止这条流。再调一次没有事'
        自身.set()#置位

    @property
    def aborted(自身):
        '已经中止'
        return 自身.is_set()#是否置位


class 资源注册表:
    'resources 服务。记录一旦建成就留下，最后一次释放只丢掉状态'
    def __init__(自身,上下文):
        '记下登记效应所属的上下文'
        自身.上下文=上下文#本插件的上下文
        自身.提供方={}#协议到提供方
        自身.记录={}#地址到记录

    def 登记(自身,提供方):
        '为一个协议登记提供方。已经有提供方就抛出。返回的拆除器可以重复调用'
        协议=提供方['protocol']#协议键
        if 协议 in 自身.提供方:#已经有
            raise RuntimeError('resources: protocol "'+str(协议)+'" already has a provider')#拒绝第二个

        def 寿命():
            '挂上提供方。已持有的地址开流，空闲的改成加载中'
            自身.提供方[协议]=提供方#登记
            for 记录 in 自身.协议下记录(协议):#已有地址
                自身.挂上(记录)#持有则开流

            def 拆除():
                '卸下提供方，停掉它的流，状态改成无'
                del 自身.提供方[协议]#摘掉
                for 记录 in 自身.协议下记录(协议):#同一协议
                    自身.卸下(记录)#停流
            return 拆除#拆除器

        拆除登记=自身.上下文.副作用(寿命,'resources.register('+转json(协议)+')')#挂到本纤程

        def 对外拆除():
            '拆除这次登记'
            拆除登记()#幂等
        return 对外拆除#交给调用方

    def 钉住(自身,地址,信号):
        '信号中止前保持打开。已经中止的信号钉不住'
        if 信号.aborted:#已经中止
            return#钉不住
        记录=自身.取记录(地址)#建或取出
        自身.持有(记录)#算一个持有者

        def 松开():
            '中止后释放这一钉'
            自身.释放(记录)#最后一个则停流
        信号.addEventListener('abort',松开,{'once':True})#中止时松开

    def 取源(自身,地址):
        '这一地址的活源。记录还在，源就还是同一个'
        return 自身.取记录(地址).源#可观察源

    def 取记录(自身,地址):
        '页面存续期内保留记录'
        记录=自身.记录.get(地址)#已有或没有
        if 记录 is None:#第一次
            记录=自身.创建(地址)#建一条
            自身.记录[地址]=记录#留下
        return 记录#同一条

    def 创建(自身,地址):
        '建一条永不删除的记录。同一地址以后都返回这条的源'
        协议=取协议(地址)#协议或没有
        if 自身.取提供方(协议) is None:#没有提供方
            初态='none'#无
        else:#已经有提供方
            初态='loading'#等第一帧
        存储=创建快照存储(空闲(初态))#初始快照
        记录=简单命名空间(地址=地址,协议=协议,存储=存储,源=None,持有者数=0,控制器=None)#地址运行态

        def 取快照():
            '读当前快照，不因此持有这条资源'
            return 存储.getSnapshot()#当前

        def 订阅(监听器):
            '订阅变更并持有。退订只生效一次'
            退订=存储.subscribe(监听器)#存储上的退订
            自身.持有(记录)#第一个订阅者打开流
            活跃=[True]#门闩

            def 取消():
                '退订并释放。再调一次没有事'
                if 活跃[0] is not True:#已经退过
                    return#空操作
                活跃[0]=False#关上
                退订()#摘掉监听
                自身.释放(记录)#最后一个则停流
            return 取消#退订器

        记录.源=简单命名空间(getSnapshot=取快照,subscribe=订阅)#可观察源
        return 记录#留下

    def 取提供方(自身,协议):
        '没有协议就没有提供方'
        if 协议 is None:#不是资源地址
            return None#没有
        return 自身.提供方.get(协议)#未登记则是 None

    def 协议下记录(自身,协议):
        '这个协议下已经建过的记录'
        for 记录 in 自身.记录.values():#全部地址
            if 记录.协议==协议:#同一协议
                yield 记录#交给调用方

    def 持有(自身,记录):
        '增加持有者。从零到一的时候打开流'
        记录.持有者数=记录.持有者数+1#加上这次
        if 记录.持有者数==1:#第一个
            自身.启动(记录)#打开

    def 释放(自身,记录):
        '减少持有者。最后一个离开时停流，并把快照收成空闲'
        记录.持有者数=记录.持有者数-1#去掉这次
        if 记录.持有者数>0:#还有人
            return#流继续
        自身.停止(记录)#中止流
        if 自身.取提供方(记录.协议) is None:#没有提供方
            状态='none'#无
        else:#提供方还在
            状态='loading'#等下一次打开
        记录.存储.set(空闲(状态))#丢掉值和失败

    def 挂上(自身,记录):
        '提供方到了。有人持有就开流，否则只把空闲改成加载中'
        if 记录.持有者数>0:#有人持有
            自身.启动(记录)#开流
            return#不再改空闲
        记录.存储.set(空闲('loading'))#还没人订，只改状态

    def 卸下(自身,记录):
        '提供方走了。停流并报无'
        自身.停止(记录)#中止
        记录.存储.set(空闲('none'))#无提供方

    def 启动(自身,记录):
        '有提供方才打开流。没有提供方就留在当前状态'
        方=自身.取提供方(记录.协议)#当前提供方
        if 方 is None:#还没有
            return#不开
        控制器=流信号()#这条流的中止旗
        记录.控制器=控制器#记下，停止时中止它
        if 记录.存储.getSnapshot()['status']!='loading':#还不是加载中
            记录.存储.set(空闲('loading'))#先进入加载中
        启动守护线程(自身.消费,记录,方,控制器)#不等待整条流

    def 停止(自身,记录):
        '中止正在跑的流，并摘掉控制器'
        if 记录.控制器 is not None:#有流
            记录.控制器.abort()#中止
            记录.控制器=None#摘掉

    def 消费(自身,记录,提供方,信号):
        '逐帧写入。中止之后的帧丢掉。流里抛出的错误不接住'
        流=提供方['open'](记录.地址,{'signal':信号})#打开
        for 帧 in 流:#逐帧
            if 信号.aborted:#已经释放
                break#丢掉这一帧并结束迭代
            if 帧['ok']:#成功帧
                记录.存储.set({#换成最新值
                    'status':'live',#活
                    'value':帧['value'],#这一帧的值
                    'failure':None,#清掉失败
                })#写入
            else:#失败帧
                记录.存储.set({#保留上一份值
                    'status':'failed',#失败
                    'value':记录.存储.getSnapshot()['value'],#上一份
                    'failure':帧['error'],#这一帧的失败
                })#写入


资源注册表.register=资源注册表.登记#调用方按 register 登记
资源注册表.pin=资源注册表.钉住#调用方按 pin 钉住
资源注册表.source=资源注册表.取源#调用方按 source 取源
