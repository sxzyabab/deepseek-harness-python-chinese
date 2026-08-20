"""Cordis 工具的纯函数、可回放渲染意图。

对齐上游 `拓展/tool-cordis/src/present.ts`。公开面仅中文名。
"""

__all__=[#仅中文公开名
    '呈现运行时巡检调用','呈现巡检列表调用','呈现巡检查询调用','呈现自检调用',
    '呈现包巡检调用','呈现定义调用','呈现移除调用','呈现运行调用','呈现停止调用',
]#公开面结束

def 呈现运行时巡检调用(参数=None):#渲染一次运行时巡检调用
    """可回放的通用调用展示。"""
    if 参数 is None:#无参
        参数={}#空
    if 参数.get('name') is None:#未指定成员名
        目标=参数.get('what')#仅类别
    else:#有成员名
        目标=(参数.get('what') or '')+': '+参数['name']#类别: 名
    if 目标 is None:#无目标
        return {'card':'generic','kind':'read','title':'Inspect Cordis runtime'}#总览
    return {'card':'generic','kind':'read','title':'Inspect Cordis runtime: '+目标}#带目标

def 呈现巡检列表调用(*_位置参数,**_关键字参数):#渲染提供方列表
    """可回放的通用调用展示。"""
    return {'card':'generic','kind':'read','title':'List Cordis Inspect Providers'}#通用只读卡片

def 呈现巡检查询调用(参数):#渲染提供方查询
    """可回放的通用调用展示。"""
    return {'card':'generic','kind':'read','title':'Query Cordis '+参数['platform']+' '+参数['provider']+'.'+参数['method']}#通用只读卡片

def 呈现自检调用(参数):#渲染自检
    """可回放的通用调用展示。"""
    if 参数.get('pluginId') is None:#未指定插件
        目标='dynamic Cordis Plugins'#总览
    elif 参数.get('packageId') is None:#只插件
        目标=参数['pluginId']#插件 id
    else:#两 id
        目标=参数['pluginId']+'/'+参数['packageId']#插件/包
    return {'card':'generic','kind':'read','title':'Inspect '+目标}#通用只读卡片

def 呈现包巡检调用(参数):#渲染不可变包源码巡检
    """可回放的通用调用展示。"""
    return {'card':'generic','kind':'read','title':'Inspect Cordis Package '+参数['pluginId']+'/'+参数['packageId']}#通用只读卡片

def 呈现定义调用(参数):#渲染定义调用
    """可回放的通用调用展示，源码放在 raw input。"""
    目标=('new '+参数['plugin']['idPrefix']+'-*') if 参数['plugin']['kind']=='new' else 参数['plugin']['pluginId']#新建用前缀
    return {'card':'generic','kind':'execute','title':'Register Cordis Plugin "'+参数['name']+'" for '+目标+': '+参数['purpose'],'rawInput':参数['code']}#展示

def 呈现移除调用(参数):#渲染移除
    """可回放的通用调用展示。"""
    return {'card':'generic','kind':'delete','title':'Remove Cordis Plugin '+参数['pluginId']}#通用删除卡片

def 呈现运行调用(参数):#渲染运行/更新
    """可回放的通用调用展示。"""
    动词='Update' if 参数['mode']=='update' else 'Run'#按模式
    return {'card':'generic','kind':'execute','title':动词+' Cordis Plugin '+参数['pluginId']+' · '+参数['packageId']}#标题

def 呈现停止调用(参数):#渲染停止
    """可回放的通用调用展示。"""
    return {'card':'generic','kind':'execute','title':'Stop Cordis Plugin '+参数['pluginId']}#通用执行卡片
