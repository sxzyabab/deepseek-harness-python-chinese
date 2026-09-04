"""每个 CDP 连接上，各 realm Runtime 对象的路由与投影。

对齐上游 `worker/cdp/domains/runtime/object-table.ts`。公开面仅中文名。
"""
from ...标识 import cdp字符串id#CDP对象id

__all__=['Runtime对象表']#仅中文公开名

class Runtime对象表:#Runtime对象表
    """将各 realm 的后端句柄映射到限定于一个 CDP 连接的对象 id。"""
    def __init__(自身,connectionId):#构造
        """保存连接 id。"""
        自身.connectionId=connectionId#连接id
        自身._路由={}#路由表
        自身._下一对象id=1#下一对象id
        自身._下一异常id=1#下一异常id
        自身._观察者=None#观察者

    def 设观察者(自身,观察者):#设置观察者
        """在 Runtime 与 DOM 会话组装完成后安装 Cordis 对象识别。"""
        自身._观察者=观察者#保存

    def 解析(自身,objectId):#解析
        """解析一个连接本地对象 id。"""
        return 自身._路由.get(cdp字符串id(objectId,'objectId'))#取路由

    def 完成(自身,realm,值,group):#完成投影
        """将 realm 完成结果转换为 CDP 字段。"""
        结果={'result':自身.远程(realm,值['result'],group)}#结果
        if 值.get('exceptionDetails') is not None:#有异常
            结果['exceptionDetails']=自身._异常(realm,值['exceptionDetails'],group)#异常
        return 结果#返回

    def 属性们(自身,realm,值,group):#属性投影
        """将 realm 属性描述符转换为 CDP 字段。"""
        结果={'result':[自身._属性(realm,项,group) for 项 in 值['properties']]}#属性
        if 值.get('internalProperties') is not None:#有内部
            结果['internalProperties']=[自身._内部属性(realm,项,group) for 项 in 值['internalProperties']]#内部
        if 值.get('privateProperties') is not None:#有私有
            结果['privateProperties']=[自身._私有属性(realm,项,group) for 项 in 值['privateProperties']]#私有
        if 值.get('exceptionDetails') is not None:#有异常
            结果['exceptionDetails']=自身._异常(realm,值['exceptionDetails'],group)#异常
        return 结果#返回

    def 控制台事件(自身,realm,值):#Console事件投影
        """将一次 realm Console 事件投影为 CDP Runtime 通知。"""
        if 值['type']=='console-api':#API调用
            事件=值['event']#事件
            上下文=事件.get('contextId')#上下文
            if 上下文 is None and realm.context.kind=='synthetic':#或合成
                上下文=realm.context.id#取id
            参数={'type':事件['type'],'args':[自身.远程(realm,项,'console') for 项 in 事件['arguments']],'timestamp':事件['timestamp']}#参数
            if 上下文 is not None:#有上下文
                参数['executionContextId']=上下文#写入
            if 事件.get('stackTrace') is not None:#有栈
                参数['stackTrace']=cdp栈跟踪(事件['stackTrace'])#栈
            return {'method':'Runtime.consoleAPICalled','params':参数}#通知
        事件=值['event']#异常事件
        上下文=事件.get('contextId')#上下文
        if 上下文 is None and realm.context.kind=='synthetic':#或合成
            上下文=realm.context.id#取id
        详情={**自身._异常(realm,事件['details'],'console')}#异常详情
        if 上下文 is not None:#有上下文
            详情['executionContextId']=上下文#写入
        return {'method':'Runtime.exceptionThrown','params':{'timestamp':事件['timestamp'],'exceptionDetails':详情}}#异常通知

    def 组内realms(自身,group):#组内realm
        """列出在某对象组中至少保留一个对象的 realm 会话。"""
        realms=set()#集合
        for 路由 in 自身._路由.values():#扫路由
            if 路由['group']==group:#同组
                realms.add(路由['realm'])#加入
        return list(realms)#数组

    def 释放(自身,objectId):#释放对象
        """忘记一个对外可见的对象 id。"""
        自身._路由.pop(cdp字符串id(objectId,'objectId'),None)#删除

    def 释放组(自身,group):#释放组
        """忘记某对象组下保留的全部 id。"""
        for 对象id,路由 in list(自身._路由.items()):#扫路由
            if 路由['group']==group:#同组
                del 自身._路由[对象id]#删除

    def 释放realm(自身,realm):#释放realm
        """忘记某个已关闭 realm 会话拥有的全部对象。"""
        for 对象id,路由 in list(自身._路由.items()):#扫路由
            if 路由['realm'] is realm:#同realm
                del 自身._路由[对象id]#删除

    def 清空(自身):#清空
        """忘记本 DevTools 连接上暴露的全部对象。"""
        自身._路由.clear()#清路由

    def 远程(自身,realm,值,group):#远程对象投影
        """投影一个公共 Runtime 值，并为本连接保留其后端句柄。"""
        对象=值.get('object')#对象包装
        对象id=None if 对象 is None else 自身._暴露(realm,对象['handle'] if isinstance(对象,dict) else 对象.handle,group)#暴露
        呈现=None#呈现
        if 对象id is not None and 值.get('semanticReference') is not None and 自身._观察者 is not None:#有呈现输入
            呈现=自身._观察者(对象id,realm.descriptor,值['semanticReference'],group)#观察
        描述符=值.get('descriptor',值)#描述符
        字段=dict(描述符) if isinstance(描述符,dict) else {}#基字段
        if 呈现 is not None:#有呈现
            if 呈现.get('subtype') is not None:#子类型
                字段['subtype']=呈现['subtype']#写入
            if 呈现.get('className') is not None:#类名
                字段['className']=呈现['className']#写入
            if 呈现.get('description') is not None:#描述
                字段['description']=呈现['description']#写入
        if 对象id is not None:#有对象id
            字段['objectId']=对象id#写入
        return 字段#返回

    def _属性(自身,realm,属性,group):#属性投影
        """属性描述符投影。"""
        字段=dict(属性)#基字段
        if 属性.get('value') is not None:#值
            字段['value']=自身.远程(realm,属性['value'],group)#值
        if 属性.get('get') is not None:#getter
            字段['get']=自身.远程(realm,属性['get'],group)#getter
        if 属性.get('set') is not None:#setter
            字段['set']=自身.远程(realm,属性['set'],group)#setter
        if 属性.get('symbol') is not None:#符号
            字段['symbol']=自身.远程(realm,属性['symbol'],group)#符号
        return 字段#返回

    def _内部属性(自身,realm,属性,group):#内部属性投影
        """内部属性投影。"""
        字段={'name':属性['name']}#名
        if 属性.get('value') is not None:#值
            字段['value']=自身.远程(realm,属性['value'],group)#值
        return 字段#返回

    def _私有属性(自身,realm,属性,group):#私有属性投影
        """私有属性投影。"""
        字段={'name':属性['name']}#名
        if 属性.get('value') is not None:#值
            字段['value']=自身.远程(realm,属性['value'],group)#值
        if 属性.get('get') is not None:#getter
            字段['get']=自身.远程(realm,属性['get'],group)#getter
        if 属性.get('set') is not None:#setter
            字段['set']=自身.远程(realm,属性['set'],group)#setter
        return 字段#返回

    def _异常(自身,realm,详情,group):#异常投影
        """异常详情投影。"""
        字段=dict(详情)#基字段
        字段['exceptionId']=自身._下一异常id#异常id
        自身._下一异常id+=1#推进
        if realm.context.kind=='synthetic':#合成上下文
            字段['executionContextId']=realm.context.id#写入
        if 详情.get('stackTrace') is not None:#有栈
            字段['stackTrace']=cdp栈跟踪(详情['stackTrace'])#栈
        if 详情.get('exception') is not None:#异常对象
            字段['exception']=自身.远程(realm,详情['exception'],group)#异常对象
        return 字段#返回

    def _暴露(自身,realm,handle,group):#暴露句柄
        """分配连接本地对象 id。"""
        对象id=cdp字符串id(f'runtime:{自身.connectionId}:{自身._下一对象id}','objectId')#分配id
        自身._下一对象id+=1#推进
        自身._路由[对象id]={'realm':realm,'handle':handle,'group':group}#登记
        return 对象id#返回

def cdp栈跟踪(栈):#栈投影
    """栈跟踪投影。"""
    结果={'callFrames':[{#调用帧
        'functionName':帧['functionName'],#函数名
        'scriptId':帧.get('scriptKey') or '0',#脚本id
        'url':帧['url'],#URL
        'lineNumber':帧['lineNumber'],#行
        'columnNumber':帧['columnNumber'],#列
    } for 帧 in 栈['callFrames']]}#callFrames结束
    if 栈.get('description') is not None:#描述
        结果['description']=栈['description']#写入
    if 栈.get('parent') is not None:#父栈
        结果['parent']=cdp栈跟踪(栈['parent'])#父栈
    return 结果#返回
