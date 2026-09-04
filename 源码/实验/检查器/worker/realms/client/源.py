"""有界浏览器源目录传输上的 Client SourceBackend。"""
#对齐上游 worker/realms/client/sources.ts

import base64#分块解码
from ......内核.智能体循环.辅助 import 解开#可等待则等待

__all__=['Client源后端']#仅中文公开名

class Client源后端:#Client源后端
    """经公共只读源模型呈现一个 Client 包目录。"""
    def __init__(自身,目标,会话id,路由,脚本身份):#构造
        """保存依赖。"""
        自身.目标=目标#目标
        自身.会话id=会话id#会话
        自身.路由=路由#路由
        自身.脚本身份=脚本身份#脚本身份
        自身._脚本={}#脚本表
        自身._目录=None#目录缓存
        自身._已关闭=False#是否已关闭

    def 列脚本(自身):#列脚本
        """确保目录已加载。"""
        if 自身._已关闭:#已关闭
            raise RuntimeError('Client source session is closed')#抛错
        if 自身._目录 is None:#惰性加载
            自身._目录=自身._加载目录()#加载
        return 自身._目录#目录

    def 取脚本来源(自身,脚本键):#取脚本来源
        """读 source 分块。"""
        路由=自身._路由(脚本键)#路由
        源=自身._读(路由['localKey'],'source')#读源
        if 源 is None:#不可用
            raise RuntimeError('Client script source is unavailable')#抛错
        return 源#返回

    def 取源映射(自身,脚本键):#取源映射
        """读 source-map 分块。"""
        路由=自身._路由(脚本键)#路由
        return 自身._读(路由['localKey'],'source-map')#读映射

    def 订阅(自身,_监听):#订阅
        """无动态发现。"""
        return lambda:None#无动态发现

    def 关闭(自身):#关闭
        """拒绝本 DevTools 连接拥有的待决读取。"""
        if 自身._已关闭:#幂等
            return#返回
        自身._已关闭=True#置位
        自身.路由.关闭会话(自身.目标['source'],自身.会话id)#关会话
        自身._脚本.clear()#清脚本

    def _加载目录(自身):#加载目录
        """请求 list-scripts。"""
        结果=自身._期望(解开(自身.路由.请求(自身.目标['source'],自身.会话id,{'op':'list-scripts'})),'list-scripts')#请求列表
        return [自身._登记(脚本) for 脚本 in 结果['scripts']]#登记映射

    def _登记(自身,脚本):#登记脚本
        """登记公开键。"""
        脚本键=自身.脚本身份.转Runtime(脚本['scriptKey'])#公开键
        描述={**脚本,'scriptKey':脚本键,'executionContextId':自身.目标['contextId']}#描述
        自身._脚本[脚本键]={'localKey':脚本['scriptKey']}#路由
        return 描述#返回

    def _路由(自身,脚本键):#解析路由
        """确保目录后取路由。"""
        自身.列脚本()#确保目录
        路由=自身._脚本.get(脚本键)#取路由
        if 路由 is None:#不可用
            raise RuntimeError('Client script is no longer available')#抛错
        return 路由#返回

    def _读(自身,脚本键,内容):#读内容分块
        """循环分块直至 eof。"""
        块们=[]#块
        偏移=0#偏移
        while True:#循环分块
            结果=自身._期望(解开(自身.路由.请求(自身.目标['source'],自身.会话id,{#请求块
                'op':'get-content-chunk','scriptKey':脚本键,'content':内容,#种类
                'offset':偏移,'maxBytes':自身.路由.分块字节,#上限
            })),'get-content-chunk')#expect结束
            if not 结果.get('available'):#不可用
                return None#无
            字节=base64.b64decode(结果['data'])#解码
            if len(字节)>自身.路由.分块字节 or 结果['nextOffset']!=偏移+len(字节) or (not 结果.get('eof') and 结果['nextOffset']==偏移) or 结果['nextOffset']>自身.路由.最大内容字节:#无效块
                raise RuntimeError('Client source returned an invalid content chunk')#无效块
            块们.append(字节)#收集
            偏移=结果['nextOffset']#推进
            if 结果.get('eof'):#结束
                break#停止
        return b''.join(块们).decode('utf-8')#解码文本

    def _期望(自身,结果,操作):#期望结果
        """窄化结果操作。"""
        结果=解开(结果)#可等待则等待
        if 结果.get('op')!=操作:#不符
            raise RuntimeError(f"Client source returned {结果.get('op')} for {操作}")#抛错
        return 结果#返回
