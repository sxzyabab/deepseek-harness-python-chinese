"""日志驱动会话标题服务、确定性回退与提供方契约（对齐上游 session-title）。"""
import threading,weakref#并发与弱表
from ...依赖 import cordis,schemastery#Cordis 与配置
服务=cordis.服务#服务基类
数字字段=schemastery.数字字段#数字字段
from ...模型后端.llm import 深冻结,是否智能体循环请求#LLM 辅助
from .归一 import 归一化会话标题,回退会话标题#标题归一

class 会话标题无效错误(Exception):#显式重命名失败
    """用户标题归一化后为空。"""
    name='SessionTitleInvalidError'#错误名

def 取字段(对象,键,缺省=None):#读字段
    """读映射或对象字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#键
    return getattr(对象,键,缺省)#属性

def _用户消息(事件):#从事件提取人类消息
    """提取一条合格的人类文本消息。"""
    if 取字段(事件,'type')!='user/message':#非用户消息
        return None#跳过
    数据=取字段(事件,'data')#载荷
    if 取字段(取字段(数据,'source'),'kind')!='user':#非用户来源
        return None#跳过
    内容=取字段(数据,'content') or []#内容块
    文本='\n'.join(块.get('text','') for 块 in 内容 if isinstance(块,dict) and 块.get('type')=='text')#拼文本
    if len(归一化会话标题(文本,2**31-1))==0:#空
        return None#跳过
    return {'seq':取字段(事件,'seq'),'text':文本}#消息

def 折叠会话标题(事件们):#折叠最新标题
    """从日志折叠最新标题快照。"""
    for 事件 in reversed(list(事件们)):#自后向前
        if 取字段(事件,'type')!='session/title':#非标题
            continue#继续
        数据=取字段(事件,'data')#载荷
        return {'title':数据['title'],'messageSeqs':list(数据.get('messageSeqs') or []),'source':数据['source'],'eventSeq':取字段(事件,'seq'),'updatedAt':取字段(事件,'time')}#快照
    return None#无标题

标题投影定义={#title 投影
    'key':'title','stateVersion':1,'stateSchema':None,
    'init':lambda 头:None,
    'apply':lambda 状态,事件:取字段(取字段(事件,'data'),'title') if 取字段(事件,'type')=='session/title' else 状态,
    'wire':{'viewSchema':None,'view':lambda 状态:状态},
}#定义结束

空标题输入={'first':None,'count':0,'lastSeq':None}#titleInput 初始

def _标题输入应用(状态,事件):#titleInput 折叠
    """折叠 titleInput 状态。"""
    消息=_用户消息(事件)#提取
    if 消息 is None:#无关
        return 状态#原样
    return {'first':状态.get('first') or 消息,'count':状态.get('count',0)+1,'lastSeq':消息['seq']}#更新

标题输入投影定义={#titleInput 投影
    'key':'titleInput','stateVersion':3,'stateSchema':None,
    'init':lambda 头:dict(空标题输入),
    'apply':_标题输入应用,
}#无 wire

名称='session-title'#Cordis 插件名
注入=['sessions','sessionProjections']#依赖
配置={#配置模式
    'fallbackMaxWords':数字字段(默认值=8),#回退词数
    'fallbackMaxBytes':数字字段(默认值=80),#回退字节
    'maxTitleBytes':数字字段(默认值=200),#标题字节上限
}#配置结束
__all__=['会话标题服务','会话标题无效错误','折叠会话标题','标题投影定义','名称','注入','配置','应用','默认']#公开面

class 会话标题服务(服务):#会话标题服务
    """日志驱动标题与可选异步提供方。"""
    inject=['sessions','sessionProjections']#Cordis 注入
    Config=配置#Cordis 配置

    def __init__(自身,上下文,配置值):#构造服务
        """安装 ctx.sessionTitle。"""
        super().__init__(上下文,'sessionTitle')#服务名
        for 键 in ('fallbackMaxWords','fallbackMaxBytes','maxTitleBytes'):#校验正整数
            值=配置值[键]#读配置
            if not isinstance(值,int) or 值<=0:#非法
                raise Exception('session-title: '+键+' must be a positive integer')#拒绝
        if 配置值['fallbackMaxBytes']>配置值['maxTitleBytes']:#回退超上限
            raise Exception('session-title: fallbackMaxBytes must not exceed maxTitleBytes')#拒绝
        自身._配置=深冻结(dict(配置值))#冻结配置
        自身._提供方=None#唯一提供方
        自身._工作=weakref.WeakKeyDictionary()#每会话工作状态
        自身._生命周期=threading.Event()#拆除旗（简化）
        上下文.sessionProjections.register(标题投影定义)#title 单元
        上下文.sessionProjections.register(标题输入投影定义)#titleInput 单元
        def 收到用户消息(会话,事件):#user/message
            """调度回退与自动标题。"""
            自身._处理用户消息(会话,事件)#处理
        上下文.on('session/event',lambda 会话,事件: 自身._路由事件(会话,事件))#事件路由
        def 拆除():#服务拆除
            """中止在途工作。"""
            自身._生命周期.set()#标记拆除
            自身._提供方=None#清提供方
            自身._工作=weakref.WeakKeyDictionary()#清工作表
        上下文.effect(lambda:拆除,'sessionTitle lifecycle')#生命周期

    def _路由事件(自身,会话,事件):#事件分发
        """按类型分发。"""
        if 自身._生命周期.is_set():#已拆除
            return#忽略
        类型=取字段(事件,'type')#类型
        if 类型=='user/message':#用户消息
            自身._处理用户消息(会话,事件)#处理
        elif 类型=='request/header':#请求头
            自身._处理请求头(会话,事件)#处理

    def 获取(自身,会话):#读最新标题
        """读折叠标题。"""
        return 折叠会话标题(取字段(会话,'events'))#折叠

    get=获取#Cordis 槽

    def 重命名(自身,会话,标题):#用户重命名
        """接受显式用户标题。"""
        if 自身._生命周期.is_set():#已拆除
            raise Exception('session-title service disposed')#拒绝
        if 自身.ctx.sessions.get(取字段(会话,'id')) is not 会话:#非活会话
            raise Exception('session "'+str(取字段(会话,'id'))+'" is not live in this store')#拒绝
        归一=归一化会话标题(标题,自身._配置['maxTitleBytes'])#归一
        if len(归一)==0:#空
            raise 会话标题无效错误('session title must contain visible characters')#拒绝
        会话.append('session/title',{'title':归一,'messageSeqs':[],'source':{'kind':'user'}})#追加
        结果=自身.获取(会话)#再读
        if 结果 is None:#不应发生
            raise Exception('renamed title failed to fold')#失败
        return 结果#快照

    rename=重命名#Cordis 槽

    def 登记提供方(自身,提供方):#登记提供方
        """登记唯一可选提供方。"""
        if 自身._提供方 is not None:#已占用
            raise Exception('session-title provider "'+str(取字段(提供方,'id'))+'" is already registered')#拒绝
        def 效果():#effect 登记
            """登记并在拆除时清提供方。"""
            自身._提供方=提供方#写入
            def 拆除():#拆除
                自身._提供方=None#清空
            return 拆除#拆除器
        return 自身.ctx.effect(效果,'sessionTitle.register()')#挂 effect

    register=登记提供方#Cordis 槽

    def _处理用户消息(自身,会话,事件):#用户消息路径
        """确保回退并调度自动标题。"""
        if _用户消息(事件) is None:#不合格
            return#跳过
        当前=自身.获取(会话)#当前标题
        if 当前 is not None and 取字段(当前.get('source'),'kind')=='user':#用户钉住
            return#不自动
        自身._确保回退(会话)#回退

    def _确保回退(自身,会话):#写回退标题
        """若无标题则写确定性回退。"""
        if 自身.获取(会话) is not None:#已有
            return#跳过
        输入=自身.ctx.sessionProjections.stateOf(会话,'titleInput') or 空标题输入#输入状态
        首=输入.get('first')#首消息
        if 首 is None:#无输入
            return#跳过
        标题=回退会话标题(首['text'],自身._配置['fallbackMaxWords'],自身._配置['fallbackMaxBytes'])#回退
        if len(标题)==0:#不可派生
            return#跳过
        会话.append('session/title',{'title':标题,'messageSeqs':[首['seq']],'source':{'kind':'fallback'}})#追加

    def _处理请求头(自身,会话,事件):#请求头路径
        """自动标题在请求头后启动（简化：仅确保回退）。"""
        自身._确保回退(会话)#回退

def 应用(上下文,配置值):#加载插件
    """注册会话标题服务。"""
    会话标题服务(上下文,配置值)#构造即登记

apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
默认=应用#中文默认导出
