'经已有会话写入、与提供方无关的耐久翻译'
import math
import re
import threading
from ...基础设施.通用工具 import 当前毫秒,紧凑json编码
from ...内核 import 会话 as 会话模块
from ...内核.会话 import 快照json值,冻结树
from ...内核.会话.异常 import 会话错误
from ...会话.会话持久化.异常 import 会话持久化未找到错误
from ...工具.值 import 深冻结,深相等json
from ...模型后端.llm.调用配置 import 结构化克隆
from .异常 import 翻译错误
from .类型 import 若已中止则抛出

__all__=['翻译存储','插件记录之']

插件记录文法=re.compile(r'^plugin:[a-z0-9][a-z0-9._-]*(?:/[a-z0-9][a-z0-9._-]*)*$')
最大安全整数=9007199254740991
请求类型='plugin:translator/request'
结果类型='plugin:translator/result'

def 需要会话():
    '没有可复用的耐久会话'
    return 翻译错误('TRANSLATION_SESSION_REQUIRED','翻译需要一份已有的耐久会话')

def 无效():
    '已存记录读不回来或对不上'
    return 翻译错误('TRANSLATION_STORAGE_ERROR','已存翻译记录无效或不可用')

def 失败(错误,信号):
    '中止原样抛出；未找到会话改成需要会话；其余存储失败收成无效'
    若已中止则抛出(信号)
    if isinstance(错误,会话持久化未找到错误):
        raise 需要会话()
    if isinstance(错误,翻译错误):
        raise 错误
    raise 无效()

def 是对象(值):
    '普通记录，数组不算'
    return isinstance(值,dict)

def 是安全序号(值):
    '非负安全整数，拒绝布尔和负零'
    if isinstance(值,bool) or not isinstance(值,(int,float)):
        return False
    if isinstance(值,float):
        if not 值.is_integer():
            return False
        if 值==0.0 and math.copysign(1.0,值)<0:
            return False
    return 0<=值<=最大安全整数

def 请求数据(值):
    '校验一条翻译请求记录的必填字符串'
    if not 是对象(值):
        raise 无效()
    for 键 in ('provider','text','sourceLanguage','targetLanguage','recipe'):
        if not isinstance(值.get(键),str):
            raise 无效()
    if 'metadata' in 值 and not 是对象(值['metadata']):
        raise 无效()
    记录={
        'provider':值['provider'],
        'text':值['text'],
        'sourceLanguage':值['sourceLanguage'],
        'targetLanguage':值['targetLanguage'],
        'recipe':值['recipe'],
    }
    if 'metadata' in 值:
        记录['metadata']=值['metadata']
    return 记录

def 身份键(身份):
    '提供方、原文、语言和配方合成的缓存键'
    return 紧凑json编码([身份['provider'],身份['text'],身份['sourceLanguage'],身份['targetLanguage'],身份['recipe']])

def 是插件记录类型(类型):
    'plugin: 加小写斜杠分段'
    return isinstance(类型,str) and 插件记录文法.fullmatch(类型) is not None

def 插件记录之(事件):
    '只认 ignorable 且类型符合插件记录文法的事件'
    if not 是对象(事件):
        return None
    类型=事件.get('type')
    if 事件.get('ignorable') is not True or not 是插件记录类型(类型):
        return None
    return {'type':类型,'seq':事件['seq'],'time':事件['time'],'data':事件['data']}

def 追加插件记录(会话,类型,数据):
    '在观察者跑起来之前写上 ignorable；公开追加不会带这个标记'
    if not 是插件记录类型(类型):
        raise 会话错误('插件记录类型 "'+str(类型)+'" 必须是 plugin: 加小写斜杠分段')
    数据快照=快照json值(数据)
    if 数据快照 is None:
        raise 会话错误('插件记录 "'+str(类型)+'" 携带了无法 JSON 序列化的 data')
    条目=会话模块.附着表.get(会话)
    if 条目 is not None and 条目['appending']:
        raise 会话错误('另一条追加正在发表时，会话追加不得重入')
    事件=冻结树({
        'type':类型,
        'seq':len(会话.日志),
        'time':当前毫秒(),
        'data':数据快照,
        'ignorable':True,
    })
    会话.表面视图.校验下一条(事件)
    if 条目 is not None:
        条目['appending']=True
    try:
        回调列表=None
        回调参数=[会话,事件]
        if 条目 is not None:
            回调列表=会话模块.收集会话回调(条目['emitCtx'],[条目['carrier'],'session/event']+回调参数)
        会话.日志.append(事件)
        会话._事件快照=None
        if 回调列表 is not None and 条目 is not None:
            会话模块.收住会话观察者(条目['emitCtx'],'session/event',条目['id'],回调参数,回调列表)
        return 事件['seq']
    finally:
        if 条目 is not None:
            条目['appending']=False
            if 条目['detachRequested'] and (not 条目['announcing']):
                条目['detach']()

class 翻译存储:
    '命中缓存不需要活动会话；未命中才走当前写入者'
    def __init__(自身,上下文):
        '同一身份的并发尝试串成一队，卸载时等其他线程写完'
        自身.上下文=上下文
        自身.翻译表={}
        自身.表锁=threading.Lock()

        def 登记():
            '交出卸载时等待在途翻译的拆除器'
            def 拆():
                '不等待调用拆除的那条线程，避免死锁'
                本线程=threading.get_ident()
                with 自身.表锁:
                    待等=list(自身.翻译表.values())
                for 门,线程 in 待等:
                    if 线程!=本线程:
                        门.wait()
            return 拆

        上下文.副作用(登记)

    def 运行(自身,标识,身份,信号,操作):
        '先读缓存；未命中要求活动会话，写完并读回对上才返回'
        持久化=自身.上下文.获取服务('sessionPersistence')
        键=紧凑json编码([标识,身份键(身份)])
        完成=threading.Event()
        线程=threading.get_ident()
        with 自身.表锁:
            先前=自身.翻译表.get(键)
            自身.翻译表[键]=(完成,线程)
        写入=[]
        try:
            if 先前 is not None and 先前[1]!=线程:
                先前[0].wait()
            若已中止则抛出(信号)
            if 持久化 is None:
                raise 需要会话()

            def 当前():
                '持久化实例被换掉就不再使用旧身份'
                若已中止则抛出(信号)
                现在=自身.上下文.获取服务('sessionPersistence')
                if 现在 is None or getattr(现在,'identity',None) is not 持久化.identity:
                    raise 需要会话()

            try:
                当前()
                if 持久化.观察(标识,{'signal':信号}) is None:
                    raise 需要会话()
                当前()
                缓存=自身.查找(标识,身份,持久化,信号,当前)
                当前()
                if 缓存 is not None:
                    return 缓存
                会话们=自身.上下文.获取服务('sessions')
                会话=None if 会话们 is None else 会话们.获取(标识)
                if 会话们 is None or 会话 is None:
                    raise 翻译错误('TRANSLATION_SESSION_INACTIVE','未命中缓存的翻译需要一份活动会话')

                def 活着():
                    '活动会话对象被换掉则停止写入'
                    当前()
                    现在会话们=自身.上下文.获取服务('sessions')
                    if 现在会话们 is None or 现在会话们.获取(标识) is not 会话:
                        raise 需要会话()

                def 追加(类型,数据):
                    '写入、冲洗、再读回一条，对不上就当存储无效'
                    门=threading.Event()
                    写入.append(门)
                    try:
                        活着()
                        快照=深冻结(结构化克隆(数据))
                        序号=追加插件记录(会话,类型,快照)
                        会话们.冲洗(会话)
                        活着()
                        已存=自身.读取(标识,持久化,信号,活着,序号,1)
                        活着()
                        记录=None if len(已存)==0 else 插件记录之(已存[0])
                        if len(已存)==0 or 记录 is None or 记录['type']!=类型 or not 深相等json(已存[0]['data'],快照):
                            raise 无效()
                        return 序号
                    except Exception as 错误:
                        失败(错误,信号)
                    finally:
                        门.set()

                def 请求(数据):
                    '分派前记下请求'
                    return 追加(请求类型,数据)

                def 结果(请求序号,文本):
                    '返回调用方之前记下译文'
                    追加(结果类型,{'requestSeq':请求序号,'text':文本})

                return 操作({'请求':请求,'结果':结果})
            except Exception as 错误:
                失败(错误,信号)
        finally:
            for 门 in 写入:
                门.wait()
            with 自身.表锁:
                当前项=自身.翻译表.get(键)
                if 当前项 is not None and 当前项[0] is 完成:
                    del 自身.翻译表[键]
            完成.set()

    def 读取(自身,标识,持久化,信号,当前,起点=0,条数=None):
        '打开只读句柄，读完即关'
        当前()
        句柄=持久化.打开(标识,'read',{'signal':信号})
        try:
            当前()
            已存=句柄.读(起点,条数,{'signal':信号})
            当前()
            return 已存['events']
        finally:
            句柄.关闭()

    def 查找(自身,标识,身份,持久化,信号,当前):
        '同一身份保留最后一条成功译文'
        请求表={}
        结果表={}
        for 事件 in 自身.读取(标识,持久化,信号,当前):
            记录=插件记录之(事件)
            if 记录 is not None and 记录['type']==请求类型:
                请求表[记录['seq']]=请求数据(记录['data'])
            if 记录 is None or 记录['type']!=结果类型:
                continue
            数据=记录['data']
            if (not 是对象(数据) or not 是安全序号(数据.get('requestSeq'))
                or 数据.get('requestSeq')<0 or not isinstance(数据.get('text'),str)):
                raise 无效()
            请求=请求表.get(数据['requestSeq'])
            if 请求 is None:
                raise 无效()
            结果表[身份键(请求)]=数据['text']
        return 结果表.get(身份键(身份))
