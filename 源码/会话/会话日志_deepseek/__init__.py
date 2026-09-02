"""增量会话日志贡献（对齐 upstream session-log-deepseek）。"""
import weakref#按会话折叠接受水位
from ...依赖.schemastery import 字典字段,布尔字段#配置
from ...模型后端.llm import 品牌字符串#会话 id 品牌
from ...内核.智能体循环.辅助 import 取 as 取字段#字段读取
名称='session-log-deepseek'#Cordis 插件名
注入=['deepseekLlmApiExtensions','sessions']#依赖
配置=字典字段({'enabled':布尔字段(默认值=False)})#配置模式
__all__=['名称','注入','配置','已接受至','应用','默认']#公开面

接受折叠表=weakref.WeakKeyDictionary()#Session→{scannedEvents,throughSeq}

def 已接受至(会话):#最高已确认 seq
    """折叠 session-log-deepseek/delivery-accepted 事件。"""
    先前=接受折叠表.get(会话)#已有折叠
    穿过=取字段(先前,'throughSeq',-1) if 先前 is not None else -1#水位
    事件们=取字段(会话,'events',[])#日志
    起点=取字段(先前,'scannedEvents',0) if 先前 is not None else 0#扫描起点
    for 索引 in range(起点,len(事件们)):#增量扫描
        事件=事件们[索引]#事件
        if 取字段(事件,'type')!='session-log-deepseek/delivery-accepted':#非接受
            continue#跳过
        数据=取字段(事件,'data',{})#载荷
        会话标识=取字段(数据,'sessionId')#会话 id
        至序号=取字段(数据,'throughSeq')#水位
        if (not isinstance(会话标识,str)) or len(会话标识)==0:#非法 id
            raise Exception('session-log-deepseek: malformed acceptance watermark at seq '+str(取字段(事件,'seq')))#畸形
        if (not isinstance(至序号,int)) or 至序号<0 or 至序号>=取字段(事件,'seq'):#非法 seq
            raise Exception('session-log-deepseek: malformed acceptance watermark at seq '+str(取字段(事件,'seq')))#畸形
        if 会话标识!=取字段(会话,'id'):#别会话
            continue#跳过
        穿过=max(穿过,至序号)#推进
    接受折叠表[会话]={'scannedEvents':len(事件们),'throughSeq':穿过}#缓存
    return 穿过#返回

def 应用(上下文,配置值):#注册请求贡献
    """enabled 时注册 dsh_session_log 字段。"""
    if 配置值.get('enabled') is not True:#未启用
        return#不挂
    def 准备(请求):#提供方 prepare
        """为官方 DeepSeek 请求附加增量日志。"""
        会话标识=取字段(请求,'sessionId')#会话 id
        if 会话标识 is None:#无会话
            return None#跳过
        会话=上下文.sessions.get(品牌字符串(会话标识))#活会话
        if 会话 is None:#无活会话
            return None#跳过
        之后序号=已接受至(会话)#已确认水位
        快照=取字段(会话,'events',[])#完整日志
        至序号=len(快照)-1#当前末端
        if 至序号<0:#空日志
            return None#跳过
        后缀=快照[之后序号+1:]#未确认后缀
        值={'version':1,'session':取字段(会话,'header'),'afterSeq':之后序号,'throughSeq':至序号,'events':后缀}#扩展体
        def 接纳():#accept 回调
            """写入 delivery-accepted 水印。"""
            会话.append('session-log-deepseek/delivery-accepted',{'sessionId':取字段(会话,'id'),'throughSeq':至序号})#追加
        return {'value':值,'accept':接纳}#准备结果
    上下文.deepseekLlmApiExtensions.register('dsh_session_log',{'prepare':准备})#登记

apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
默认=应用#中文默认导出
