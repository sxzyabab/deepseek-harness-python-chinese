'增量会话日志贡献'
import weakref#按会话折叠接受水位与阻塞警告
from ...依赖.schemastery import 字典字段,布尔字段,数字字段#配置
from ...基础设施.通用工具 import 紧凑json编码,utf8字节数#字段字节
from ...内核.会话 import 已知会话事件类型,会话标识#已知事件类型、会话 id 品牌
from .异常 import 会话日志错误#本包异常
from . import (
    类型,
)

包名='@deepseek-ai/dsh-session-log-deepseek'
名称='session-log-deepseek'
依赖=['deepseekLlmApiExtensions','sessions']#依赖常量
配置模式=字典字段(字典结构={
    'enabled':布尔字段(默认值=True),#是否贡献 dsh_session_log
    'maxBytes':数字字段(默认值=8*1024*1024),#单次字段 UTF-8 上限
})#配置模式
__all__=['包名','名称','依赖','应用','默认','已接受至','会话日志错误','线路头','线路事件']

接受折叠表=weakref.WeakKeyDictionary()#Session→{scannedEvents,throughSeq}
阻塞警告表=weakref.WeakKeyDictionary()#Session→上次报告被挡住的事件序号

def 线路头(会话):#线路头
    '把逻辑 Session 元数据译为原始外部请求字段'
    头=会话.header#会话头
    结果={#头对象
        'version':头['version'],#版本
        'id':str(头['id']),#id
        'createdAt':头['createdAt'],#创建
    }#基
    if 'cwd' in 头:#可选cwd
        结果['cwd']=头['cwd']#带上
    if 'parentSession' in 头:#可选父会话
        结果['parentSession']=str(头['parentSession'])#带上
    if 头.get('isSeeded'):#已播种：线协议仍用 seedLength
        继承=getattr(会话,'inheritedEventCount',None)#继承条数
        if 继承 is None:#回退长度
            继承=len(会话.events)#回退
        结果['seedLength']=int(继承)#种子长度
    if 'origin' in 头:#可选来源
        结果['origin']=头['origin']#带上
    if 'delegationDepth' in 头:#可选委托深度
        结果['delegationDepth']=头['delegationDepth']#带上
    if 'agentPreset' in 头:#可选预设
        结果['agentPreset']=头['agentPreset']#带上
    return 结果#返回

def 线路表面操作(操作):#线路表面操作
    '把表面操作译为原始数字请求字段'
    if 操作=='append':#追加
        return 操作#原样
    return {'op':'replace','startSeq':int(操作['startSeq']),'endSeq':int(操作['endSeq'])}#替换

def 线路事件(事件):#线路事件
    '把编译期序号品牌译为原始数字请求字段'
    公共={#公共字段
        'seq':int(事件['seq']),#序号
        'time':事件['time'],#时间
        'data':事件['data'],#数据
    }#common结束
    if 'ignorable' in 事件:#可选可忽略
        公共['ignorable']=事件['ignorable']#带上
    类型=事件['type']#类型
    if 类型 in ('developer/message','system/message','user/message','tool/result'):#表面事件
        结果={**公共,'type':类型,'surfaceOp':线路表面操作(事件['surfaceOp'])}#表面
        if 'sourceEventSeqs' in 事件:#源序号
            结果['sourceEventSeqs']=[int(序号) for 序号 in 事件['sourceEventSeqs']]#映射
        return 结果#返回
    if 类型=='assistant/message':#助手消息
        return {**公共,'type':类型,'surfaceOp':线路表面操作(事件['surfaceOp'])}#助手表面
    if 类型 not in 已知会话事件类型 and 事件.get('ignorable') is True:#未知可忽略
        结果={**公共,'type':类型,'ignorable':True}#不透明事件
        if 'surfaceOp' in 事件:#可选表面
            结果['surfaceOp']=事件['surfaceOp']#带上
        if 'sourceEventSeqs' in 事件:#可选源
            结果['sourceEventSeqs']=事件['sourceEventSeqs']#带上
        return 结果#返回
    return {**公共,'type':类型}#仅日志

def 已接受至(会话):
    '本精确会话格式世代的最高已确认序号'
    if 会话 not in 接受折叠表:
        穿过=-1#水位
        起点=0#扫描起点
    else:
        先前=接受折叠表[会话]#已有折叠
        穿过=先前['throughSeq']#水位
        起点=先前['scannedEvents']#扫描起点
    长度=会话.seq if hasattr(会话,'seq') else len(会话.events)#当前长度
    事件列表=会话.events#日志
    for 索引 in range(起点,长度):
        if 索引>=len(事件列表):#缺失
            raise 会话日志错误(f'session-log-deepseek: missing event {索引} below captured length {长度}')#抛错
        事件=事件列表[索引]#事件
        if 事件['type']!='session-log-deepseek/delivery-accepted':
            continue#跳过
        数据=事件['data'] if 'data' in 事件 else {}#载荷
        接纳版本=数据['sessionFormatVersion'] if 'sessionFormatVersion' in 数据 else 0#接受格式世代
        if (not isinstance(接纳版本,int)) or isinstance(接纳版本,bool) or 接纳版本<0:#非法
            raise 会话日志错误(f'session-log-deepseek: malformed acceptance format version at seq {事件["seq"]}')#抛错
        if 接纳版本!=会话.header['version']:#他世代
            continue#跳过
        会话标识值=数据['sessionId'] if 'sessionId' in 数据 else None#会话 id
        至序号=数据['throughSeq'] if 'throughSeq' in 数据 else None#水位
        if (not isinstance(会话标识值,str)) or len(会话标识值)==0:
            raise 会话日志错误('session-log-deepseek: malformed acceptance watermark at seq '+str(事件['seq']))#畸形
        if (not isinstance(至序号,int)) or isinstance(至序号,bool) or 至序号<0 or 至序号>=事件['seq']:
            raise 会话日志错误('session-log-deepseek: malformed acceptance watermark at seq '+str(事件['seq']))#畸形
        if 会话标识值!=会话.id:
            continue#跳过
        穿过=max(穿过,至序号)#推进
    接受折叠表[会话]={'scannedEvents':长度,'throughSeq':穿过}#缓存
    return 穿过#返回

def json字节(值):
    '请求体编码下的 UTF-8 字节；无法序列化视为超过任何上限'
    try:#序列化
        文本=紧凑json编码(值)#紧凑 JSON
    except (TypeError,ValueError):#无法序列化
        return float('inf')#超过任何上限
    return utf8字节数(文本)#字节

def 启用中(配置值):
    '每次请求读取启用开关'
    值=配置值['enabled'] if 'enabled' in 配置值 else True#默认开
    if hasattr(值,'get') and callable(值.get):#可变配置
        return 值.get() is True#当前值
    return 值 is True#布尔

def 应用(上下文,配置值):
    '注册增量日志字段；每次请求再读启用开关，并只带放得进 maxBytes 的最长前缀'
    最大字节=配置值['maxBytes'] if 'maxBytes' in 配置值 else 8*1024*1024#上限
    if isinstance(最大字节,bool) or not isinstance(最大字节,int) or 最大字节<=0:#非法
        raise 会话日志错误('session-log-deepseek: maxBytes must be a positive integer')#拒绝
    def 准备(请求):
        '为官方 DeepSeek 请求附加放得进上限的增量日志'
        if not 启用中(配置值):#本次关闭
            return None#不贡献
        会话标识值=请求['sessionId'] if 'sessionId' in 请求 else None#会话 id
        if 会话标识值 is None:
            return None#跳过
        会话=上下文.sessions.get(会话标识(会话标识值))#活会话
        if 会话 is None:
            return None#跳过
        之后序号=已接受至(会话)#已确认水位
        待传=会话.snapshotEvents(之后序号+1)#未确认后缀
        信封={#不含事件与 throughSeq 数字的外壳
            'version':1,#版本
            'sessionFormatVersion':会话.header['version'],#格式世代
            'session':线路头(会话),#头
            'afterSeq':之后序号,#起点
        }#信封
        字节=json字节({**信封,'throughSeq':0,'events':[]})-1#去掉占位的一位 throughSeq
        事件列表=[]#放得进的线路事件
        候选字节=0#最近一次考察的字段大小
        for 事件 in 待传:#按前缀增长
            线路=线路事件(事件)#线路事件
            下一段=字节+(0 if len(事件列表)==0 else 1)+json字节(线路)#加上本事件
            候选字节=下一段+len(str(事件['seq']))#补上真实 throughSeq 位数
            if 候选字节>最大字节:#放不下
                break#停在上一个前缀
            字节=下一段#收下
            事件列表.append(线路)#收下
        末事件=None if len(事件列表)==0 else 待传[len(事件列表)-1]#前缀末端
        if 末事件 is None:#一条都放不下
            首条=待传[0] if len(待传)>0 else None#挡住的第一条
            if 首条 is not None and 阻塞警告表.get(会话)!=首条['seq']:#同一条只警告一次
                阻塞警告表[会话]=首条['seq']#记下
                序号文本=str(首条['seq'])#序号
                if 候选字节!=float('inf'):#能算出字节
                    上下文.日志.警告('session-log-deepseek: event '+序号文本+' of session "'+str(会话.id)+'" needs a '+str(候选字节)+'-byte dsh_session_log field, above maxBytes '+str(最大字节)+'; this session\'s upload stays at event '+序号文本+' until maxBytes admits it')#警告
                else:#无法序列化
                    上下文.日志.警告('session-log-deepseek: event '+序号文本+' of session "'+str(会话.id)+'" is too large to serialize into a dsh_session_log field; this session\'s upload stays at event '+序号文本)#警告
            return None#本次不上传
        至序号=末事件['seq']#接受水位
        值={**信封,'throughSeq':至序号,'events':事件列表}#扩展体
        def 接纳():
            '写入 delivery-accepted 水印'
            会话.append('session-log-deepseek/delivery-accepted',{#追加
                'sessionId':会话.id,#会话id
                'sessionFormatVersion':会话.header['version'],#格式世代
                'throughSeq':至序号,#接受至
            })#append结束
        return {'value':值,'accept':接纳}#准备结果
    上下文.deepseekLlmApiExtensions.register('dsh_session_log',{'prepare':准备})#登记

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置模式#框架槽
default=默认#框架槽
