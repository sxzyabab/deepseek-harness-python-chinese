"""增量会话日志贡献（对齐 upstream session-log-deepseek）。"""
import weakref#按会话折叠接受水位
from ...依赖.schemastery import 字典字段,布尔字段#配置
from ...模型后端.llm import 品牌字符串#会话 id 品牌

class 会话日志错误(Exception):
    """会话日志 deepseek 包的异常基类。"""

名称='session-log-deepseek'#配套插件名常量
注入=['deepseekLlmApiExtensions','sessions']#依赖常量
配置模式=字典字段({'enabled':布尔字段(默认值=False)})#配置模式
__all__=['名称','注入','已接受至','应用','会话日志错误']#公开面

接受折叠表=weakref.WeakKeyDictionary()#Session→{scannedEvents,throughSeq}

def 已接受至(会话):
    """折叠 session-log-deepseek/delivery-accepted 事件。"""
    先前=接受折叠表.get(会话)#已有折叠
    if 先前 is None:
        穿过=-1#水位
        起点=0#扫描起点
    else:
        穿过=先前['throughSeq']#水位
        起点=先前['scannedEvents']#扫描起点
    事件列表=会话.events#日志
    for 索引 in range(起点,len(事件列表)):
        事件=事件列表[索引]#事件
        if 事件['type']!='session-log-deepseek/delivery-accepted':
            continue#跳过
        数据=事件['data'] if 'data' in 事件 else {}#载荷
        会话标识=数据['sessionId'] if 'sessionId' in 数据 else None#会话 id
        至序号=数据['throughSeq'] if 'throughSeq' in 数据 else None#水位
        if (not isinstance(会话标识,str)) or len(会话标识)==0:
            raise 会话日志错误('session-log-deepseek: malformed acceptance watermark at seq '+str(事件['seq']))#畸形
        if (not isinstance(至序号,int)) or isinstance(至序号,bool) or 至序号<0 or 至序号>=事件['seq']:
            raise 会话日志错误('session-log-deepseek: malformed acceptance watermark at seq '+str(事件['seq']))#畸形
        if 会话标识!=会话.id:
            continue#跳过
        穿过=max(穿过,至序号)#推进
    接受折叠表[会话]={'scannedEvents':len(事件列表),'throughSeq':穿过}#缓存
    return 穿过#返回

def 应用(上下文,配置值):
    """enabled 时注册 dsh_session_log 字段。"""
    if 'enabled' not in 配置值 or 配置值['enabled'] is not True:
        return#不挂
    def 准备(请求):
        """为官方 DeepSeek 请求附加增量日志。"""
        会话标识=请求['sessionId'] if 'sessionId' in 请求 else None#会话 id
        if 会话标识 is None:
            return None#跳过
        会话=上下文.sessions.get(品牌字符串(会话标识))#活会话
        if 会话 is None:
            return None#跳过
        之后序号=已接受至(会话)#已确认水位
        快照=会话.events#完整日志
        至序号=len(快照)-1#当前末端
        if 至序号<0:
            return None#跳过
        后缀=快照[之后序号+1:]#未确认后缀
        值={'version':1,'session':会话.header,'afterSeq':之后序号,'throughSeq':至序号,'events':后缀}#扩展体
        def 接纳():
            """写入 delivery-accepted 水印。"""
            会话.append('session-log-deepseek/delivery-accepted',{'sessionId':会话.id,'throughSeq':至序号})#追加
        return {'value':值,'accept':接纳}#准备结果
    上下文.deepseekLlmApiExtensions.register('dsh_session_log',{'prepare':准备})#登记

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
应用.Config=配置模式#Cordis Config 槽
default=应用#Cordis 默认导出槽
