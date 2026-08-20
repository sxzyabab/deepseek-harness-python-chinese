"""机器可读的 cordis API 目录查询面。

对齐上游 `拓展/tool-cordis/src/api-catalog.ts`。
SERVICE/EVENT/TYPE 分别来自服务目录表、事件目录表、类型目录表。
"""
import re#类型名词边界
from .服务目录表 import 服务目录#服务
from .事件目录表 import 事件目录#事件
from .类型目录表 import 类型目录#类型

__all__=[#仅中文公开名
    '服务目录','事件目录','类型目录','继承上下文目录',
    '查询服务目录','查询事件目录',
]#公开面结束

继承上下文目录=[#继承 ctx 目录（上游完整）
    {'name':'ctx.on / ctx.once','summary':'Register an event listener (disposable).'},#监听
    {'name':'ctx.emit / ctx.parallel / ctx.serial / ctx.bail / ctx.waterfall','summary':'Dispatch an event (sync / awaited / first-bail / short-circuit chain).'},#分发
    {'name':'ctx.plugin / ctx.inject','summary':'Load a plugin / declare required services.'},#加载/声明
    {'name':'ctx.effect','summary':'Register a disposable side effect tied to the fiber.'},#副作用
    {'name':'ctx.get / ctx.set / ctx.provide / ctx.accessor / ctx.mixin','summary':'Low-level service-store access and binding.'},#服务仓
    {'name':'ctx.extend / ctx.isolate / ctx.intercept','summary':'Derive a child context (scoped services / isolation / interception).'},#派生子上下文
    {'name':'ctx.root / ctx.scope / ctx.fiber / ctx.registry / ctx.reflect / ctx.events / ctx.logger','summary':'Ambient handles onto the running context graph.'},#环境句柄
    {'name':'ctx.timer (+ interval / timeout / throttle / debounce)','summary':'Disposable timer helpers. The `timer` key is provided at runtime; the four supported helpers are mixed onto ctx directly (declared via Pick).'},#定时器
    {'name':'ctx.loader','summary':'The config Loader that booted the app (present under the loader).'},#Loader
    {'name':'ctx.hmr','summary':'The hot-module-reload watcher (present under the hmr plugin).'},#热更新
]#结束继承

def 引用类型闭包(种子们,类型们=None):#签名引用的类型闭包
    """种子文本引用到的已编目类型形态的传递闭包。"""
    if 类型们 is None:#缺省
        类型们=类型目录#用模块目录
    已收=set()#已收入的类型名
    前沿=list(种子们)#本轮要搜的文本
    while len(前沿)>0:#还有未展开的
        下一轮=[]#下一轮文本
        for 条目 in 类型们:#每个类型
            if 条目['name'] in 已收:#已收入
                continue#跳过
            模式=re.compile(r'\b'+re.escape(条目['name'])+r'\b')#按名匹配
            if not any(模式.search(文本) for 文本 in 前沿):#本轮文本没点名
                continue#跳过
            已收.add(条目['name'])#收入
            下一轮.append(条目['declaration'])#其声明进入下一轮
        前沿=下一轮#换一轮
    return [条目 for 条目 in 类型们 if 条目['name'] in 已收]#按目录顺序过滤

def 上下文属性(键):#ctx 访问表达式
    """合法标识符用点，否则用下标。"""
    if re.match(r'^[A-Za-z_$][\w$]*$',键):#合法标识符
        return 'ctx.'+键#点访问
    import json#下标
    return 'ctx['+json.dumps(键)+']'#下标访问

def 查询服务目录(键=None,服务们=None):#查询服务
    """把服务目录投影成紧凑目录，或一份精确编码约定。"""
    if 服务们 is None:#缺省
        服务们=服务目录#模块目录
    if 键 is None:#列目录
        return {#目录模式
            'mode':'catalog',#模式
            'services':[{#每条服务
                'key':服务['key'],#键
                'description':服务['summary'],#摘要
                'methods':[{'signature':方法['signature']} for 方法 in 服务['methods']],#只留签名
            } for 服务 in 服务们],#map
        }#目录
    服务=None#按键找
    for 候选 in 服务们:#查找
        if 候选['key']==键:#命中
            服务=候选#记下
            break#结束
    if 服务 is None:#未知服务
        raise Exception('no catalogued Service named "'+键+'"')#未知
    return {#服务模式
        'mode':'service',#模式
        'service':{#详细服务
            'key':服务['key'],#键
            'description':服务['description'],#完整说明
            'access':{#访问方式
                'optional':{'expression':'ctx.get('+__import__('json').dumps(服务['key'])+')','requiresUndefinedCheck':True},#可选查找
                'hardDependency':{'inject':[服务['key']],'expression':上下文属性(服务['key'])},#硬依赖
            },#access
            'methods':服务['methods'],#方法约定
        },#service
        'referencedTypes':引用类型闭包([方法['signature'] for 方法 in 服务['methods']]),#引用类型
    }#服务模式

def 查询事件目录(名=None,事件们=None):#查询事件
    """把事件目录投影成紧凑目录，或一份精确监听器约定。"""
    if 事件们 is None:#缺省
        事件们=事件目录#模块目录
    if 名 is None:#列目录
        return {#目录模式
            'mode':'catalog',#模式
            'events':[{#每条事件
                'name':事件['name'],#名
                'description':事件['summary'],#摘要
                'mode':事件['mode'],#分发模式
                'signature':事件['signature'],#签名
            } for 事件 in 事件们],#map
        }#目录
    事件=None#按名找
    for 候选 in 事件们:#查找
        if 候选['name']==名:#命中
            事件=候选#记下
            break#结束
    if 事件 is None:#未知事件
        raise Exception('no catalogued Event named "'+名+'"')#未知
    return {#事件模式
        'mode':'event',#模式
        'event':{#详细事件
            'name':事件['name'],#名
            'description':事件['description'],#完整说明
            'mode':事件['mode'],#分发模式
            'signature':事件['signature'],#签名
            'parameters':事件['parameters'],#参数
        },#event
        'referencedTypes':引用类型闭包([事件['signature']]),#引用类型
    }#事件模式
