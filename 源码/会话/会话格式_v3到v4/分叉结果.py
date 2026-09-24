"""原生 V4 分叉结果身份与未启动错误校验。"""
import re#十进制后缀
from ..会话格式 import 会话格式错误,是否会话格式json对象#从会话格式导入

十进制序号=re.compile(r'0|[1-9]\d*',re.ASCII)#十进制安全整数字符串
安全整数上限=9007199254740991#外来JSON安全整数上限

def 断言v4分叉结果(行):#断言v4分叉结果
    """校验分叉生成的未启动结果，不改其身份或文本。"""
    if not 是否会话格式json对象(行) or 行.get('type')!='tool/result':#非工具结果
        return#返回
    数据=行.get('data')#载荷
    if not 是否会话格式json对象(数据):#非对象
        return#返回
    错误=数据.get('error')#错误
    消息=数据.get('message')#消息
    if (not 是否会话格式json对象(错误) or 错误.get('code')!='TOOL_NOT_STARTED'
        or not 是否会话格式json对象(消息) or not isinstance(消息.get('id'),str)
        or not 消息['id'].startswith('forked-tool-result-')):#非分叉未启动
        return#返回
    来源=消息.get('source')#来源
    调用标识=来源.get('callId') if 是否会话格式json对象(来源) else None#调用标识
    前缀='forked-tool-result-'+str(调用标识)+'-'#前缀
    后缀=消息['id'][len(前缀):]#后缀
    操作=行.get('surfaceOp')#表面操作
    替换=是否会话格式json对象(操作) and 操作.get('op')=='replace'#是否替换
    匹配=十进制序号.fullmatch(后缀)#十进制
    序号=int(后缀) if 匹配 is not None else None#数值
    内容=消息.get('content')#内容
    文本=内容[0] if isinstance(内容,list) and len(内容)==1 else None#唯一块
    溯源=行.get('sourceEventSeqs') if 'sourceEventSeqs' in 行 else None#溯源
    if (not isinstance(调用标识,str) or not 消息['id'].startswith(前缀)
        or 匹配 is None or 序号 is None or abs(序号)>安全整数上限
        or (替换 and (not isinstance(行.get('seq'),(int,float)) or isinstance(行.get('seq'),bool) or 序号>=行['seq']))
        or ((not 替换) and 序号!=行.get('seq'))
        or 错误.get('name')!='ToolNotStartedError'
        or ((not 替换) and (溯源 is not None or 操作!='append'))
        or (替换 and (not isinstance(溯源,list) or len(溯源)!=1 or 溯源[0]!=序号))
        or 消息.get('role')!='tool' or 消息.get('isError') is not True or 消息.get('toolCallId')!=调用标识
        or not 是否会话格式json对象(来源) or 来源.get('kind')!='tool'
        or not 是否会话格式json对象(文本) or 文本.get('type')!='text' or not isinstance(文本.get('text'),str)):#非法
        raise 会话格式错误('invalid V4 not-started fork result')#错误
