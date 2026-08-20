"""最终 LLM 适配器边界所抛值的归一化。

对齐上游 `llm/src/adapter-failure.ts`。公开面仅中文名；无英文别名。
"""
import math#有限数判定
from .错误 import 装备错误#导入装备错误基类
from .调用配置 import 深冻结#导入深冻结

__all__=('归一化语言模型失败',)#仅中文公开名

def 归一化语言模型失败(值):#从适配器抛出拆下失败事实
    """从适配器抛出的值上拆下可序列化的提供方事实。"""
    if isinstance(值,Exception):#已是异常
        错误=值#原样使用
    else:#非 Error
        错误=装备错误(抛出消息(值),'UNKNOWN',{'cause':值})#非 Error 则包一层
    携带=自有失败快照(错误)#尝试取出自有 failure 快照
    if 携带 is not None and 携带['code']==自有错误码(错误):#code 一致
        return 携带#code 一致才采用
    事实={'message':错误消息(错误),'code':装备错误码(错误)}#从 Error 自身拼一份
    return 深冻结(事实)#冻结事实

def 抛出消息(值):#渲染非 Error 抛出
    """渲染非 Error 抛出，不让敌对强制转换逃出归一化。"""
    try:#强制转字符串
        消息=str(值)#强制转字符串
        if len(消息)>0:#非空串
            return 消息#非空串
        return 'LLM adapter failed'#空串则用默认文案
    except Exception:#敌对强制转换
        return 'LLM adapter failed'#吞掉敌对强制转换

def 自有错误码(错误):#读取外来 Error 的自有数据型 code
    """读取外来 Error 的自有数据型 code，不调用访问器。"""
    try:#只看实例字典
        字典=getattr(错误,'__dict__',None)#只看实例字典
        if 字典 is None or 'code' not in 字典:#没有数据值
            return None#没有数据值
        return 字典['code']#有数据值才返回
    except Exception:#属性陷阱
        return None#吞掉属性陷阱

def 自有失败快照(错误):#快照自有 failure 属性
    """快照一个自有数据属性，不调用 SDK 定义的访问器。"""
    try:#只看实例字典
        字典=getattr(错误,'__dict__',None)#只看实例字典
        if 字典 is None or 'failure' not in 字典:#没有数据值
            return None#没有数据值
        return 失败快照(字典['failure'])#校验并拆离载荷
    except Exception:#属性陷阱
        return None#吞掉属性陷阱

def 失败快照(值):#校验并拆离可序列化失败载荷
    """校验并拆离任意可序列化失败载荷。"""
    if not isinstance(值,dict):#必须是对象
        return None#必须是对象
    try:#校验字段
        消息=值.get('message')#消息字段
        码=值.get('code')#代码字段
        if not isinstance(消息,str) or len(消息)==0:#消息非法
            return None#消息必须是非空字符串
        if not isinstance(码,str) or len(码)==0:#code 非法
            return None#code 必须是非空字符串
        事实={'message':消息,'code':码}#基础字段
        if 'status' in 值:#有 HTTP 状态
            状态=值['status']#可选 HTTP 状态
            是整数=isinstance(状态,(int,float)) and not isinstance(状态,bool) and math.isfinite(状态) and 状态==int(状态)#合法整数
            if not 是整数 or 状态<100 or 状态>599:#状态越界
                return None#状态必须是合法 HTTP 码
            事实['status']=状态#有状态才带上
        if 'providerRetryAfterMs' in 值:#有建议等待
            建议等待=值['providerRetryAfterMs']#可选建议等待
            if not (isinstance(建议等待,(int,float)) and not isinstance(建议等待,bool) and math.isfinite(建议等待) and 建议等待>0):#等待非法
                return None#提供方等待必须是正有限数
            事实['providerRetryAfterMs']=建议等待#有等待才带上
        if 'requestId' in 值:#有请求 id
            请求标识=值['requestId']#可选请求 id
            if not isinstance(请求标识,str) or len(请求标识)==0:#requestId 非法
                return None#requestId 必须是非空字符串
            事实['requestId']=请求标识#有请求 id 才带上
        return 深冻结(事实)#字段合法则冻结拆离
    except Exception:#读失败
        return None#读失败则放弃载荷

def 错误消息(错误):#读取 SDK 错误消息
    """读取 SDK 错误消息，不让访问器替换主失败。"""
    try:#取出消息
        消息=错误.message#取出消息
        if isinstance(消息,str) and len(消息)>0:#非空字符串
            return 消息#非空字符串才用
    except Exception:#SDK message getter
        pass#吞掉 SDK message getter
    return 'LLM adapter failed'#读不到则用默认文案

def 装备错误码(错误):#只信任装备自有 code
    """只信任装备自有 code；第三方 SDK 的 code 不是我们的分类。"""
    if isinstance(错误,装备错误):#装备错误
        return 错误.code#装备分类码
    return 'UNKNOWN'#非装备则 UNKNOWN
