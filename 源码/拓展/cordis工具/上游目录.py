"""定位并解析 api-catalog 的 SERVICE_API / EVENT_API。

优先读本包内嵌单文件或分片；本包有内容时优先用本包。
只解析真实条目，禁止占位。
"""
import os#路径
from .字面量解析 import 提取导出常量数组,解析数组字面量#解析

__all__=['上游目录路径','本包片段路径','本包分片前缀','加载导出数组']#公开面

_本目录=os.path.dirname(os.path.abspath(__file__))#本包
# tool_cordis→拓展→源码→dsh-python-chinese→pydsh→lib→py
上游目录路径=os.path.normpath(os.path.join(
    _本目录,'..','..','..','..','..','..','project','dsh分析','源码','拓展','tool-cordis','src','api-catalog.ts',
))#双工作区原版

本包片段路径={#导出名 → 本包内嵌单文件
    'SERVICE_API':os.path.join(_本目录,'服务目录.上游.ts'),#服务全表
    'EVENT_API':os.path.join(_本目录,'事件目录.上游.ts'),#事件全表
}#片段表

本包分片前缀={#导出名 → 分片文件名前缀（如 服务目录_01.上游.ts）
    'SERVICE_API':'服务目录_',#服务分片
    'EVENT_API':'事件目录_',#事件分片
}#分片前缀

_期望条数={'SERVICE_API':55,'EVENT_API':55}#上游全量表长

_缓存={}#按导出名缓存

def _列本包源(导出名):#本包优先：单文件或有序分片
    """返回本包可读源路径列表；无本包则空列表。"""
    单=本包片段路径.get(导出名)#单文件候选
    if 单 and os.path.isfile(单) and os.path.getsize(单)>64:#单文件有效
        return [单]#只用单文件
    前缀=本包分片前缀.get(导出名)#分片前缀
    if not 前缀:#无配置
        return []#空
    片们=[]#收集
    for 名 in sorted(os.listdir(_本目录)):#字典序=编号序
        if not (名.startswith(前缀) and 名.endswith('.上游.ts')):#非本导出分片
            continue#跳过
        路径=os.path.join(_本目录,名)#绝对
        if os.path.isfile(路径) and os.path.getsize(路径)>64:#有效
            片们.append(路径)#收入
    return 片们#可能空

def _解析一源(路径,导出名):#读并解析一个源文件
    """从一个含 export const 的源抽出条目列表。"""
    with open(路径,'r',encoding='utf-8') as 文件:#读全文
        源=文件.read()#文本
    if '<<<' in 源:#禁止占位
        raise Exception('api-catalog 源含占位标记：'+路径)#失败
    return 解析数组字面量(提取导出常量数组(源,导出名))#真表

def _条目键(导出名,条目):#去重键
    """SERVICE 用 key，EVENT 用 name。"""
    if 导出名=='SERVICE_API':#服务
        return 条目.get('key')#服务键
    return 条目.get('name')#事件名

def 加载导出数组(导出名):#抽出并解析
    """返回 SERVICE_API / EVENT_API 之一（真实条目列表）。"""
    if 导出名 in _缓存:#已解析
        return _缓存[导出名]#复用
    源们=_列本包源(导出名)#本包
    表=[]#合并
    已见=set()#去重
    for 路径 in 源们:#逐本包源
        for 条目 in _解析一源(路径,导出名):#逐条
            键=_条目键(导出名,条目)#去重键
            if 键 in 已见:#已有
                continue#跳过
            已见.add(键)#记下
            表.append(条目)#收入
    期望=_期望条数.get(导出名)#目标条数
    if (not 表 or (期望 is not None and len(表)<期望)) and os.path.isfile(上游目录路径):#本包不足则补原版
        for 条目 in _解析一源(上游目录路径,导出名):#原版全表
            键=_条目键(导出名,条目)#去重键
            if 键 in 已见:#本包已有
                continue#跳过
            已见.add(键)#记下
            表.append(条目)#补入
    if not 表:#皆无
        raise Exception('找不到 '+导出名+' 源：本包片段与原版均缺失')#失败
    _缓存[导出名]=表#记下
    return 表#返回
