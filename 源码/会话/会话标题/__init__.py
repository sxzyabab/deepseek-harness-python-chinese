"""日志驱动会话标题服务、确定性回退与提供方契约（对齐上游 session-title）。"""
import threading,weakref#并发与弱表
from ...依赖 import cordis#Cordis
from ...依赖.schemastery import 字典字段,数字字段#配置
服务=cordis.服务#服务基类
from ...模型后端.llm import 深冻结#冻结配置
from .归一 import 归一化会话标题,回退会话标题,会话标题错误,会话标题无效错误#标题归一与异常

def _用户消息(事件):
    """提取一条合格的人类文本消息。"""
    if 事件['type']!='user/message':
        return None#跳过
    数据=事件['data']#载荷
    来源=数据['source'] if 'source' in 数据 else None#来源
    if 来源 is None or 来源['kind']!='user':
        return None#跳过
    内容=数据['content'] if 'content' in 数据 and 数据['content'] is not None else []#内容块
    文本块=[]#文本
    for 块 in 内容:
        if isinstance(块,dict) and 块['type']=='text':
            文本块.append(块['text'] if 'text' in 块 else '')#拼文本
    文本='\n'.join(文本块)#拼文本
    if len(归一化会话标题(文本,2**31-1))==0:
        return None#跳过
    return {'seq':事件['seq'],'text':文本}#消息

def 折叠会话标题(事件列表):
    """从日志折叠最新标题快照。"""
    for 事件 in reversed(list(事件列表)):
        if 事件['type']!='session/title':
            continue#继续
        数据=事件['data']#载荷
        序列=数据['messageSeqs'] if 'messageSeqs' in 数据 and 数据['messageSeqs'] is not None else []#序列
        return {'title':数据['title'],'messageSeqs':list(序列),'source':数据['source'],'eventSeq':事件['seq'],'updatedAt':事件['time']}#快照
    return None#无标题

def 标题初始(头):
    """title 投影初值。"""
    return None#无标题

def 标题应用(状态,事件):
    """title 投影折叠。"""
    if 事件['type']=='session/title':
        return 事件['data']['title']#新标题
    return 状态#原样

def 标题视图(状态):
    """title 投影视图。"""
    return 状态#原样

标题投影定义={
    'key':'title','stateVersion':1,'stateSchema':None,
    'init':标题初始,
    'apply':标题应用,
    'wire':{'viewSchema':None,'view':标题视图},
}#title 投影

空标题输入={'first':None,'count':0,'lastSeq':None}#titleInput 初始

def _标题输入应用(状态,事件):
    """折叠 titleInput 状态。"""
    消息=_用户消息(事件)#提取
    if 消息 is None:
        return 状态#原样
    首条=状态['first'] if 'first' in 状态 and 状态['first'] is not None else 消息#首消息
    次数=状态['count'] if 'count' in 状态 else 0#计数
    return {'first':首条,'count':次数+1,'lastSeq':消息['seq']}#更新

def 标题输入初始(头):
    """titleInput 投影初值。"""
    return dict(空标题输入)#拷贝初值

标题输入投影定义={
    'key':'titleInput','stateVersion':3,'stateSchema':None,
    'init':标题输入初始,
    'apply':_标题输入应用,
}#无 wire

名称='session-title'#配套插件名常量
注入=['sessions','sessionProjections']#依赖常量
配置模式=字典字段({
    'fallbackMaxWords':数字字段(默认值=8),#回退词数
    'fallbackMaxBytes':数字字段(默认值=80),#回退字节
    'maxTitleBytes':数字字段(默认值=200),#标题字节上限
})#配置结束
__all__=['会话标题服务','会话标题错误','会话标题无效错误','折叠会话标题','标题投影定义','名称','注入','应用']#公开面

class 会话标题服务(服务):
    """日志驱动标题与可选异步提供方。"""
    def __init__(自身,上下文,配置值):
        """安装 ctx.sessionTitle。"""
        super().__init__(上下文,'sessionTitle')#服务名
        for 键 in ('fallbackMaxWords','fallbackMaxBytes','maxTitleBytes'):
            值=配置值[键]#读配置
            if not isinstance(值,int) or isinstance(值,bool) or 值<=0:
                raise 会话标题错误('session-title: '+键+' must be a positive integer')#拒绝
        if 配置值['fallbackMaxBytes']>配置值['maxTitleBytes']:
            raise 会话标题错误('session-title: fallbackMaxBytes must not exceed maxTitleBytes')#拒绝
        自身._配置=深冻结(dict(配置值))#冻结配置
        自身._提供方=None#唯一提供方
        自身._工作=weakref.WeakKeyDictionary()#每会话工作状态
        自身._生命周期=threading.Event()#拆除旗
        上下文.sessionProjections.登记(标题投影定义)#title 单元
        上下文.sessionProjections.登记(标题输入投影定义)#titleInput 单元
        上下文.监听('session/event',自身._路由事件)#事件路由
        def 拆除效果():
            """服务拆除。"""
            def 拆除():
                """中止在途工作。"""
                自身._生命周期.set()#标记拆除
                自身._提供方=None#清提供方
                自身._工作=weakref.WeakKeyDictionary()#清工作表
            return 拆除#拆除器
        上下文.副作用(拆除效果,'sessionTitle lifecycle')#生命周期

    def _路由事件(自身,会话,事件):
        """按类型分发。"""
        if 自身._生命周期.is_set():
            return#忽略
        类型=事件['type']#类型
        if 类型=='user/message':
            自身._处理用户消息(会话,事件)#处理
        elif 类型=='request/header':
            自身._处理请求头(会话,事件)#处理

    def 获取(自身,会话):
        """读折叠标题。"""
        return 折叠会话标题(会话.events)#折叠

    def 重命名(自身,会话,标题):
        """接受显式用户标题。"""
        if 自身._生命周期.is_set():
            raise 会话标题错误('session-title service disposed')#拒绝
        if 自身.ctx.sessions.get(会话.id) is not 会话:
            raise 会话标题错误('session "'+str(会话.id)+'" is not live in this store')#拒绝
        归一=归一化会话标题(标题,自身._配置['maxTitleBytes'])#归一
        if len(归一)==0:
            raise 会话标题无效错误('session title must contain visible characters')#拒绝
        会话.append('session/title',{'title':归一,'messageSeqs':[],'source':{'kind':'user'}})#追加
        结果=自身.获取(会话)#再读
        if 结果 is None:
            raise 会话标题错误('renamed title failed to fold')#失败
        return 结果#快照

    def 登记提供方(自身,提供方):
        """登记唯一可选提供方。"""
        if 自身._提供方 is not None:
            提供方号=提供方['id'] if isinstance(提供方,dict) else 提供方.id#提供方身份
            raise 会话标题错误('session-title provider "'+str(提供方号)+'" is already registered')#拒绝
        def 效果():
            """登记并在拆除时清提供方。"""
            自身._提供方=提供方#写入
            def 拆除():
                """清提供方。"""
                自身._提供方=None#清空
            return 拆除#拆除器
        return 自身.ctx.副作用(效果,'sessionTitle.register()')#挂 effect

    def _处理用户消息(自身,会话,事件):
        """确保回退并调度自动标题。"""
        if _用户消息(事件) is None:
            return#跳过
        当前=自身.获取(会话)#当前标题
        if 当前 is not None:
            来源=当前['source'] if 'source' in 当前 else None#来源
            if 来源 is not None and 来源['kind']=='user':
                return#用户钉住不自动
        自身._确保回退(会话)#回退

    def _确保回退(自身,会话):
        """若无标题则写确定性回退。"""
        if 自身.获取(会话) is not None:
            return#跳过
        输入=自身.ctx.sessionProjections.状态(会话,'titleInput')#输入状态
        if 输入 is None:
            输入=空标题输入#缺省
        首=输入['first'] if 'first' in 输入 else None#首消息
        if 首 is None:
            return#跳过
        标题=回退会话标题(首['text'],自身._配置['fallbackMaxWords'],自身._配置['fallbackMaxBytes'])#回退
        if len(标题)==0:
            return#跳过
        会话.append('session/title',{'title':标题,'messageSeqs':[首['seq']],'source':{'kind':'fallback'}})#追加

    def _处理请求头(自身,会话,事件):
        """自动标题在请求头后启动（简化：仅确保回退）。"""
        自身._确保回退(会话)#回退

def 应用(上下文,配置值):
    """注册会话标题服务。"""
    会话标题服务(上下文,配置值)#构造即登记

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
应用.Config=配置模式#Cordis Config 槽
default=应用#Cordis 默认导出槽
