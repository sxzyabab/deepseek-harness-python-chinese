"""浏览器半机器可读的 cordis API 目录查询面。

对齐上游 `拓展/cordis-client-runner/src/client/api-catalog.ts`。
SERVICE/EVENT/TYPE/INHERITED_CTX_API 从原版相对路径整表加载。公开面仅中文名。
"""
import os,re#路径与类型名
from ..cordis工具.字面量解析 import 提取导出常量数组,解析数组字面量#复用解析器

__all__=[#公开面
    '服务目录','事件目录','类型目录','继承上下文目录',
    '查询服务目录','查询事件目录','上游接口目录路径',
]#结束

_本目录=os.path.dirname(os.path.abspath(__file__))#本包
上游接口目录路径=os.path.normpath(os.path.join(
    _本目录,'..','..','..','..','..','..','project','dsh分析','源码','拓展','cordis-client-runner','src','client','api-catalog.ts',
))#原版客户端目录

def _加载():#读四表
    """抽出 SERVICE_API / EVENT_API / TYPE_API / INHERITED_CTX_API。"""
    with open(上游接口目录路径,'r',encoding='utf-8') as 文件:#读
        源=文件.read()#全文
    return (#四表
        解析数组字面量(提取导出常量数组(源,'SERVICE_API')),#服务
        解析数组字面量(提取导出常量数组(源,'EVENT_API')),#事件
        解析数组字面量(提取导出常量数组(源,'TYPE_API')),#类型
        解析数组字面量(提取导出常量数组(源,'INHERITED_CTX_API')),#继承 ctx
    )#返回

服务目录,事件目录,类型目录,继承上下文目录=_加载()#导入时物化

def 引用类型闭包(种子们,类型们=None):#签名引用闭包
    """传递闭包。"""
    if 类型们 is None:#缺省
        类型们=类型目录#模块
    已收=set()#已收
    前沿=list(种子们)#本轮
    while len(前沿)>0:#还有
        下一轮=[]#下一轮
        for 条目 in 类型们:#每个
            if 条目['name'] in 已收:#已收
                continue#跳过
            模式=re.compile(r'\b'+re.escape(条目['name'])+r'\b')#词边界
            if not any(模式.search(文本) for 文本 in 前沿):#未点名
                continue#跳过
            已收.add(条目['name'])#收入
            下一轮.append(条目['declaration'])#声明
        前沿=下一轮#换轮
    return [条目 for 条目 in 类型们 if 条目['name'] in 已收]#过滤

def 上下文属性(键):#ctx 访问
    """点或下标。"""
    if re.match(r'^[A-Za-z_$][\w$]*$',键):#标识符
        return 'ctx.'+键#点
    import json#下标
    return 'ctx['+json.dumps(键)+']'#下标

def 查询服务目录(键=None,服务们=None):#查询服务
    """紧凑目录或精确约定。"""
    if 服务们 is None:#缺省
        服务们=服务目录#模块
    if 键 is None:#列
        return {'mode':'catalog','services':[{'key':服务['key'],'description':服务['summary'],'methods':[{'signature':方法['signature']} for 方法 in 服务['methods']]} for 服务 in 服务们]}#目录
    服务=None#找
    for 候选 in 服务们:#查
        if 候选['key']==键:#命中
            服务=候选#记下
            break#结束
    if 服务 is None:#未知
        raise Exception('no catalogued Service named "'+键+'"')#失败
    return {'mode':'service','service':{'key':服务['key'],'description':服务['description'],'access':{'optional':{'expression':'ctx.get('+__import__('json').dumps(服务['key'])+')','requiresUndefinedCheck':True},'hardDependency':{'inject':[服务['key']],'expression':上下文属性(服务['key'])}},'methods':服务['methods']},'referencedTypes':引用类型闭包([方法['signature'] for 方法 in 服务['methods']])}#详细

def 查询事件目录(名=None,事件们=None):#查询事件
    """紧凑目录或精确约定。"""
    if 事件们 is None:#缺省
        事件们=事件目录#模块
    if 名 is None:#列
        return {'mode':'catalog','events':[{'name':事件['name'],'description':事件['summary'],'mode':事件['mode'],'signature':事件['signature']} for 事件 in 事件们]}#目录
    事件=None#找
    for 候选 in 事件们:#查
        if 候选['name']==名:#命中
            事件=候选#记下
            break#结束
    if 事件 is None:#未知
        raise Exception('no catalogued Event named "'+名+'"')#失败
    return {'mode':'event','event':{'name':事件['name'],'description':事件['description'],'mode':事件['mode'],'signature':事件['signature'],'parameters':事件['parameters']},'referencedTypes':引用类型闭包([事件['signature']])}#详细
