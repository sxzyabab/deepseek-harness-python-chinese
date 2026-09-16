import re,uuid#路径与标识
from ...依赖.工具 import 二进制#base64
__all__=[#仅中文公开名
    'ssh错误','进程标识','文本流标识','进程标识模式','文本流标识模式','远端路径',
    '目标模式','信息模式','路径信息模式','政策模式','目录项模式','意图模式','编辑模式',
    '写结果模式','编辑结果模式','环境模式','启动模式','握手模式','流端点模式','已准备模式',
    '结局模式','输出快照模式','输出快照帧上限','完成模式','前台模式','信息可空模式','路径信息可空模式',
]#公开面结束

uuid形态=re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\Z',re.ASCII)#UUID
哈希形态=re.compile(r'^[0-9a-f]{64}\Z')#SHA-256 十六进制
base64形态=re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?\Z',re.ASCII)#规范 base64

class ssh错误(Exception):#本包异常基类
    """SSH 辅助协议失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 进程标识(原始):#品牌化进程 id
    """承认辅助协议进程身份。"""
    return 原始#原样

def 文本流标识(原始):#品牌化流 id
    """承认辅助协议文本迭代器身份。"""
    return 原始#原样

def 认uuid(值,工厂):#校验 UUID
    """UUID 文本。"""
    if not isinstance(值,str) or uuid形态.match(值) is None:#非法
        raise ssh错误('expected a UUID')#失败
    uuid.UUID(值)#再核
    return 工厂(值)#品牌

def 进程标识模式(值):#解析进程 id
    """承认进程身份。"""
    return 认uuid(值,进程标识)#品牌

def 文本流标识模式(值):#解析流 id
    """承认文本迭代器身份。"""
    return 认uuid(值,文本流标识)#品牌

def 远端路径(值):#绝对 POSIX 路径
    """非空、以 / 起、不含空字节。"""
    if not isinstance(值,str) or len(值)==0 or not 值.startswith('/') or '\0' in 值:#非法
        raise ssh错误('expected an absolute POSIX path')#失败
    return 值#路径

def 严格对象(值,键集):#无额外键
    """值须为 dict 且键恰好属于允许集。"""
    if not isinstance(值,dict):#非对象
        raise ssh错误('expected an object')#失败
    for 键 in 值:#未知键
        if 键 not in 键集:#额外
            raise ssh错误('unexpected field '+键)#失败
    return 值#对象

def 目标模式(值):#文件系统目标
    """targetKey 与 displayPath。"""
    严格对象(值,('targetKey','displayPath'))#键
    if 'targetKey' not in 值 or 'displayPath' not in 值:#缺
        raise ssh错误('expected targetKey and displayPath')#失败
    远端路径(值['targetKey'])#键路径
    if not isinstance(值['displayPath'],str):#展示
        raise ssh错误('expected displayPath string')#失败
    return 值#目标

def 信息模式(值):#stat 元数据
    """version/type/可选 size。"""
    严格对象(值,('version','type','size'))#键
    if 'version' not in 值 or 'type' not in 值:#缺
        raise ssh错误('expected version and type')#失败
    if not isinstance(值['version'],str):#版本
        raise ssh错误('expected version string')#失败
    if 值['type'] not in ('file','directory','other'):#类型
        raise ssh错误('expected file, directory or other')#失败
    if 'size' in 值 and (not isinstance(值['size'],(int,float)) or 值['size']<0):#大小
        raise ssh错误('expected nonnegative size')#失败
    return 值#信息

def 路径信息模式(值):#lstat
    """含 symlink。"""
    严格对象(值,('version','type','size'))#键
    if 'version' not in 值 or 'type' not in 值:#缺
        raise ssh错误('expected version and type')#失败
    if not isinstance(值['version'],str):#版本
        raise ssh错误('expected version string')#失败
    if 值['type'] not in ('file','directory','symlink','other'):#类型
        raise ssh错误('expected path info type')#失败
    if 'size' in 值 and (not isinstance(值['size'],(int,float)) or 值['size']<0):#大小
        raise ssh错误('expected nonnegative size')#失败
    return 值#路径信息

def 可空信息(模式):#nullable schema
    """None 或模式。"""
    def 解析(值):#解析
        """空则空。"""
        if 值 is None:#空
            return None#空
        return 模式(值)#解析
    return 解析#包装

def 政策模式(值):#文件效果政策
    """mode/workspaceRoot/可选 sessionId。"""
    严格对象(值,('mode','workspaceRoot','sessionId'))#键
    if 'mode' not in 值 or 'workspaceRoot' not in 值:#缺
        raise ssh错误('expected mode and workspaceRoot')#失败
    if 值['mode'] not in ('read-only','workspace-write','danger-full-access'):#模式
        raise ssh错误('expected sandbox mode')#失败
    远端路径(值['workspaceRoot'])#根
    if 'sessionId' in 值 and not isinstance(值['sessionId'],str):#会话
        raise ssh错误('expected sessionId string')#失败
    return 值#政策

def 目录项模式(值):#列举
    """目录子项数组。"""
    if not isinstance(值,list):#非数组
        raise ssh错误('expected directory entries')#失败
    结果=[]#项
    for 项 in 值:#逐项
        严格对象(项,('name','type','target','version','size'))#键
        if 'name' not in 项 or 'type' not in 项 or 'target' not in 项:#缺
            raise ssh错误('expected name, type and target')#失败
        if not isinstance(项['name'],str):#名
            raise ssh错误('expected entry name')#失败
        if 项['type'] not in ('file','directory','other'):#类型
            raise ssh错误('expected entry type')#失败
        目标模式(项['target'])#子目标
        结果.append(项)#收下
    return 结果#数组

def 写结果模式(值):#写观察
    """operation/version/before/after。"""
    严格对象(值,('operation','version','before','after'))#键
    if 值.get('operation') not in ('create','update'):#操作
        raise ssh错误('expected write operation')#失败
    if not isinstance(值.get('version'),str) or not isinstance(值.get('after'),str):#字段
        raise ssh错误('expected write result strings')#失败
    if 值.get('before') is not None and not isinstance(值['before'],str):#before
        raise ssh错误('expected before string or null')#失败
    return 值#结果

def 编辑结果模式(值):#编辑观察
    """version/before/after。"""
    严格对象(值,('version','before','after'))#键
    for 键 in ('version','before','after'):#字符串
        if not isinstance(值.get(键),str):#缺
            raise ssh错误('expected edit result strings')#失败
    return 值#结果

def 意图模式(值):#写意图
    """createIfAbsent 或 replaceIfVersion。"""
    if not isinstance(值,dict) or 'kind' not in 值:#缺
        raise ssh错误('expected write intent')#失败
    if 值['kind']=='createIfAbsent':#创建
        严格对象(值,('kind',))#键
        return 值#意图
    if 值['kind']=='replaceIfVersion':#替换
        严格对象(值,('kind','version'))#键
        if not isinstance(值.get('version'),str):#版本
            raise ssh错误('expected version')#失败
        return 值#意图
    raise ssh错误('expected write intent kind')#失败

def 编辑模式(值):#字面量编辑
    """oldString/newString/replaceAll。"""
    严格对象(值,('oldString','newString','replaceAll'))#键
    if not isinstance(值.get('oldString'),str) or not isinstance(值.get('newString'),str):#串
        raise ssh错误('expected edit strings')#失败
    if not isinstance(值.get('replaceAll'),bool):#布尔
        raise ssh错误('expected replaceAll boolean')#失败
    return 值#编辑

def 环境模式(值):#子进程环境
    """字符串到字符串或空。"""
    if not isinstance(值,dict):#非对象
        raise ssh错误('expected environment record')#失败
    for 键,项 in 值.items():#逐项
        if not isinstance(键,str) or (项 is not None and not isinstance(项,str)):#非法
            raise ssh错误('expected environment string or null')#失败
    return 值#环境

def 启动模式(值):#普通或终端启动
    """stdio 与 terminal 互斥。"""
    严格对象(值,('argv','cwd','env','graceMs','stdio','terminal'))#键
    return 值#规格

def 握手模式(值):#hello
    """连接握手。"""
    严格对象(值,('protocol','hash','platform','nodeVersion','node','root','workspace','bootstrapHash'))#键
    if 值.get('protocol')!=1:#版本
        raise ssh错误('expected protocol 1')#失败
    if not isinstance(值.get('hash'),str) or 哈希形态.match(值['hash']) is None:#摘要
        raise ssh错误('expected helper hash')#失败
    if 值.get('platform') not in ('linux','darwin'):#平台
        raise ssh错误('expected linux or darwin')#失败
    远端路径(值.get('node'))#node
    远端路径(值.get('root'))#root
    远端路径(值.get('workspace'))#workspace
    return 值#握手

def 流端点模式(值):#流坐标
    """path 与 capability。"""
    严格对象(值,('path','capability'))#键
    远端路径(值.get('path'))#路径
    if not isinstance(值.get('capability'),str) or 哈希形态.match(值['capability']) is None:#能力
        raise ssh错误('expected stream capability')#失败
    return 值#端点

def 已准备模式(值):#prepared
    """id 与 streams。"""
    严格对象(值,('id','streams'))#键
    进程标识模式(值.get('id'))#id
    if not isinstance(值.get('streams'),dict):#流表
        raise ssh错误('expected streams')#失败
    return 值#已准备

def 结局模式(值):#退出事实
    """exitCode 与 signal。"""
    严格对象(值,('exitCode','signal'))#键
    return 值#结局

def 输出快照模式(值):#收集尾
    """tail base64 与 totalBytes。"""
    严格对象(值,('tail','totalBytes'))#键
    if not isinstance(值.get('tail'),str) or base64形态.match(值['tail']) is None:#尾
        raise ssh错误('expected base64 tail')#失败
    二进制.从base64(值['tail'])#可解码
    if not isinstance(值.get('totalBytes'),int) or 值['totalBytes']<0:#字节
        raise ssh错误('expected nonnegative totalBytes')#失败
    return 值#快照

def 输出快照帧上限(最大字节):#帧上限
    """按收集预算封顶。"""
    return min(64*1024*1024,最大字节*2+1024)#上限

def 完成模式(值):#process.done
    """outcome/spills/collected。"""
    严格对象(值,('outcome','spills','collected'))#键
    结局模式(值.get('outcome'))#结局
    return 值#完成

def 前台模式(值):#terminal.inspect
    """可空前台组。"""
    if 值 is None:#空
        return None#空
    严格对象(值,('processGroupId','inputWaiting'))#键
    return 值#前台

信息可空模式=可空信息(信息模式)#stat 可空
路径信息可空模式=可空信息(路径信息模式)#lstat 可空
