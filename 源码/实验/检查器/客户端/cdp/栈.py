"""跨 realm 中立的 Runtime 与 Console 事件的浏览器栈解析。

对齐上游 `client/cdp/stack.ts`。公开面仅中文名。
"""
import re#栈行解析

__all__=['捕获客户端控制台栈','客户端错误栈','解析客户端栈']#仅中文公开名

铬规则=re.compile(r'^\s*at\s+(?:(.*?)\s+\()?(.+):(\d+):(\d+)\)?$')#Chrome格式
火狐规则=re.compile(r'^(.*?)@(.+):(\d+):(\d+)$')#Firefox格式

def 解析帧(行,解析脚本):#解析单行帧
    """解析单行帧。"""
    匹配=铬规则.match(行) or 火狐规则.match(行)#匹配
    if 匹配 is None:#不识别
        return None#无
    网址=匹配.group(2)#URL
    行号=int(匹配.group(3))-1#0基行号
    列号=int(匹配.group(4))-1#0基列号
    if 网址 is None:#非法
        return None#无
    脚本键=解析脚本(网址)#脚本键
    帧={'functionName':匹配.group(1) or '','url':网址,'lineNumber':行号,'columnNumber':列号}#帧
    if 脚本键 is not None:#可选键
        帧['scriptKey']=脚本键#脚本键
    return 帧#返回

def 解析客户端栈(栈,解析脚本,跳过帧):#解析Client栈
    """将 V8 与 Firefox 风格文本帧解析为公共栈模型。"""
    if 栈 is None:#无栈
        return None#无
    帧们=[]#帧列表
    for 行 in 栈.split('\n'):#逐行
        帧=解析帧(行,解析脚本)#解析行
        if 帧 is not None:#收集
            帧们.append(帧)#收集
    调用帧=帧们[跳过帧:]#跳过前缀
    return None if len(调用帧)==0 else {'callFrames':调用帧}#有则返回

def 捕获客户端控制台栈(解析脚本):#捕获Console栈
    """捕获被包装的 Client Console 方法的调用方栈。"""
    import traceback#栈文本
    return 解析客户端栈(''.join(traceback.format_stack()),解析脚本,3)#跳过观察器帧

def 客户端错误栈(值,解析脚本=None):#错误栈
    """在可用时解析附着于未捕获 Client 值的栈。"""
    if 解析脚本 is None:#缺省
        解析脚本=lambda _网址:None#空解析
    if not isinstance(值,object) or 值 is None:#非对象
        return None#无
    try:#读取
        栈=getattr(值,'stack',None) or getattr(值,'__traceback__',None)#取stack
    except Exception:#读取失败
        return None#放弃
    if isinstance(栈,str):#字符串栈
        return 解析客户端栈(栈,解析脚本,0)#解析
    return None#无
