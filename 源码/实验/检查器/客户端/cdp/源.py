"""Inspector Client 包及其 source map 的浏览器侧目录。

对齐上游 `client/cdp/sources.ts`。公开面仅中文名。
"""
import base64#分片编码
from ...共享.身份 import 检查器id#品牌化

__all__=[#仅中文公开名
    '源桥能力','客户端源资产','客户端源目录错误','客户端源目录','发现检查器客户端源目录',
]#公开面结束

包标识='@deepseek-ai/dsh-experimental-inspector'#包id
客户端脚本键=检查器id('client-bundle','scriptKey')#Client脚本键

def 源桥能力(可用):#Sources桥能力
    """描述浏览器侧源访问。"""
    return {'type':'client-sources'} if 可用 else None#有则通告

class 客户端源目录错误(Exception):#Client源目录错误
    """Client 源传输序列化的有意错误。"""
    def __init__(自身,code,message):#绑定错误码
        """保存码与信息。"""
        super().__init__(message)#基类
        自身.code=code#错误码
        自身.message=message#信息

class 客户端源目录:#Client源目录
    """对 Client 脚本资产执行有界只读操作。"""
    def __init__(自身,资产们):#构造
        """登记资产。"""
        自身.资产={}#资产表
        for 资产 in 资产们:#逐项
            键=资产['scriptKey'] if isinstance(资产,dict) else 资产.scriptKey#键
            if 键 in 自身.资产:#重复
                raise Exception(f'inspector: duplicate Client script key {键}')#拒绝
            自身.资产[键]={'asset':资产}#登记

    def 按网址取脚本键(自身,网址):#按URL取脚本键
        """将栈帧 URL 解析为本目录的本地脚本键。"""
        规范=规范化网址(网址)#规范化
        for 项 in 自身.资产.values():#逐资产
            资产=项['asset']#资产
            资产网址=资产['url'] if isinstance(资产,dict) else 资产.url#URL
            if 规范化网址(资产网址)==规范:#命中
                return 资产['scriptKey'] if isinstance(资产,dict) else 资产.scriptKey#键
        return None#无

    def 执行(自身,命令,最大内容字节):#执行源操作
        """执行一个已校验的源操作。"""
        操作=命令.get('op')#操作
        if 操作=='list-scripts':#列脚本
            脚本们=[]#列表
            for 项 in 自身.资产.values():#逐资产
                资产=项['asset']#资产
                描述={'scriptKey':资产['scriptKey'] if isinstance(资产,dict) else 资产.scriptKey,'url':资产['url'] if isinstance(资产,dict) else 资产.url,'hash':资产['hash'] if isinstance(资产,dict) else 资产.hash,'startLine':0,'startColumn':0,'endLine':0,'endColumn':0}#描述
                脚本们.append(描述)#入列
            return {'op':'list-scripts','scripts':脚本们}#列表结果
        if 操作=='get-content-chunk':#取分片
            键=命令['scriptKey']#脚本键
            项=自身.资产.get(键)#资产
            if 项 is None:#未找到
                raise 客户端源目录错误('script-not-found','Client script was not found')#未找到
            return {'op':'get-content-chunk','scriptKey':键,'content':命令['content'],'available':False}#不可用占位
        raise 客户端源目录错误('invalid-request',f'unknown Client source command {操作!r}')#未知

def 规范化网址(网址):#规范化
    """规范化网址。"""
    return 网址.split('#')[0]#去片段

def 发现检查器客户端源目录():#发现目录
    """发现 Inspector Client 包源目录；无发现时返回 None。"""
    return None#无发现
