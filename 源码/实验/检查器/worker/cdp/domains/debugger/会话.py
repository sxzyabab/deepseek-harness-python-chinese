from .......基础设施.js特性 import PromiseEX as 期约扩展#后端方法的期约组合
from .....异常 import 检查器错误#包内错误
from .....共享.校验 import 精确键,可选布尔#校验
from ...协议 import 响应cdp请求,发送cdp失败#协议
from .cdp参数 import 解析调用帧求值,取请求脚本id#参数解析
from .投影器 import 调试器事件,脚本已解析事件#投影
from .脚本注册表 import 调试器脚本注册表#脚本注册表
import re#按行搜索

__all__=['Debugger域会话']#仅中文公开名

class Debugger域会话:#Debugger域会话
    '拥有 Debugger 生命周期、共享脚本投影与 Host 原生回退'
    def __init__(自身,传输,realms,运行时):#构造
        '装配脚本表并订阅 realm'
        自身.传输=传输#传输
        自身.realms=realms#会话集
        自身.运行时=运行时#Runtime
        自身._脚本=调试器脚本注册表()#脚本注册表
        自身._源拆除器={}#源拆除器
        自身._调试拆除器={}#调试拆除器
        自身._调用帧realms={}#调用帧realm
        原生=None#原生后端
        for realm in realms.全部():#找支持的
            能力=_能力(realm.nativeDomains)#能力
            if 能力['state']=='supported':#支持
                原生=能力['backend']#后端
                break#找到
        if 原生 is None:#无原生
            raise 检查器错误('检查器没有原生 Host 调试器传输')#抛错
        自身._原生=原生#保存后端
        自身._取消realm订阅=realms.订阅(自身._接收realm)#订阅
        自身._启用请求={}#启用请求
        自身._已启用=False#是否启用
        自身._已关闭=False#是否关闭

    def 处理(自身,请求):#处理请求
        '处理一条 Debugger 请求，包括 Client 只读源操作'
        if not 请求['method'].startswith('Debugger.'):#非Debugger
            return False#未拥有
        方法=请求['method']#方法
        if 方法=='Debugger.enable':#启用
            def 启用():#启用体
                '启用'
                return 自身._启用(请求['params'])#启用
            自身._响应(请求,启用)#响应
            return True#已拥有
        if 方法=='Debugger.disable':#禁用
            精确键(请求['params'],[],'Debugger.disable 参数')#无参
            自身._响应(请求,自身._禁用)#响应
            return True#已拥有
        if 方法=='Debugger.getScriptSource':#取源
            def 取源():#取源体
                '取脚本来源'
                return 自身._取脚本来源(请求['params'])#取源
            自身._响应(请求,取源)#响应
            return True#已拥有
        if 方法=='Debugger.searchInContent':#搜索
            def 搜索():#搜索体
                '内容搜索'
                return 自身._内容搜索(请求['params'])#搜索
            自身._响应(请求,搜索)#响应
            return True#已拥有
        if 方法=='Debugger.evaluateOnCallFrame':#帧求值
            def 帧求值():#帧求值体
                '帧上求值'
                return 自身._帧上求值(请求['params'])#求值
            自身._响应(请求,帧求值)#响应
            return True#已拥有
        if 方法=='Debugger.pause':#暂停
            精确键(请求['params'],[],'Debugger.pause 参数')#无参
            自身._响应(请求,自身._暂停)#响应
            return True#已拥有
        if 方法=='Debugger.resume':#恢复
            def 恢复():#恢复体
                '恢复'
                return 自身._恢复(请求['params'])#恢复
            自身._响应(请求,恢复)#响应
            return True#已拥有
        自身._转发原生(请求)#转发原生
        return True#已拥有

    def 关闭(自身):#关闭
        '拆除源与调试器订阅'
        if 自身._已关闭:#幂等
            return#返回
        自身._已关闭=True#置位
        自身._取消realm订阅()#取消订阅
        自身._卸能力()#卸能力
        自身._调用帧realms.clear()#清帧
        自身._脚本.清空()#清脚本
        自身.运行时.释放投影组('backtrace')#释回溯组

    def _启用(自身,参数):#启用
        'Debugger.enable，返回期约；失败则回滚并以原错误拒绝'
        精确键(参数,['maxScriptsCacheSize'],'Debugger.enable 参数')#键
        if 自身._已启用:#已启用
            已启用=期约扩展()#已启用时返回空结果的期约
            已启用.解决({})#空
            return 已启用#返回已解决的期约
        缓存=参数.get('maxScriptsCacheSize')#缓存大小
        if 缓存 is not None and (not isinstance(缓存,(int,float)) or isinstance(缓存,bool) or not (缓存==缓存) or 缓存<0):#非法
            raise 检查器错误('Debugger.enable 的 maxScriptsCacheSize 必须是非负数')#抛错
        启用请求={} if 缓存 is None else {'maxScriptsCacheSize':缓存}#启用请求
        自身._启用请求=启用请求#保存
        自身._已启用=True#置位
        def 回滚(错误):#启用失败后调用
            '撤销启用并尽力禁用各 realm，禁用结算后再以原错误拒绝'
            自身._已启用=False#清位
            自身._启用请求={}#清空请求
            自身._卸能力()#卸能力
            自身._脚本.清空()#清脚本
            def 重新抛出(禁用结果列表):#各 realm 禁用结算后调用
                '把启用失败的原错误交还调用方'
                raise 错误#再抛
            return 期约扩展.全部已结算([_能力(领域.debugger)['backend'].禁用() for 领域 in 自身.realms.全部() if _能力(领域.debugger)['state']=='supported']).然后(重新抛出)#尽力禁用
        def 发布全部目录(启用结果列表):#全部 realm 启用后调用
            '发布各 realm 目录，完成后合并启用结果'
            def 合并启用结果(目录结果列表):#各目录发布后调用
                '合并各 realm 的启用结果'
                return 合并结果(启用结果列表)#合并结果
            return 期约扩展.全部([自身._发布目录(领域) for 领域 in 自身.realms.全部()]).然后(合并启用结果)#各目录发布后再合并
        try:#附着各realm
            for 领域 in 自身.realms.全部():#附着
                自身._附着能力(领域)#附着能力
        except Exception as 错误:#附着源与调试订阅可能抛检查器错误，契约未定所以收不窄
            return 回滚(错误)#附着失败同样回滚
        return 期约扩展.全部([_能力(领域.debugger)['backend'].启用(启用请求) for 领域 in 自身.realms.全部() if _能力(领域.debugger)['state']=='supported']).然后(发布全部目录).捕获(回滚)#全部启用后再发布目录，失败则回滚

    def _禁用(自身):#禁用
        'Debugger.disable，返回期约'
        自身._已启用=False#清位
        自身._启用请求={}#清空
        自身._卸能力()#卸能力
        自身._调用帧realms.clear()#清帧
        自身._脚本.清空()#清脚本
        自身.运行时.释放投影组('backtrace')#释回溯
        return 期约扩展.全部([_能力(领域.debugger)['backend'].禁用() for 领域 in 自身.realms.全部() if _能力(领域.debugger)['state']=='supported']).然后(合并结果)#全部禁用后合并

    def _取脚本来源(自身,参数):#取脚本来源
        'Debugger.getScriptSource，返回期约'
        精确键(参数,['scriptId'],'Debugger.getScriptSource 参数')#键
        if not isinstance(参数.get('scriptId'),str):#类型
            raise 检查器错误('Debugger.getScriptSource 需要 scriptId')#抛错
        路由=自身._脚本.解析(参数['scriptId'])#路由
        if 路由 is not None:#本地
            def 包装源(源):#源读完后调用
                '包装成 CDP 结果'
                return {'scriptSource':源}#本地
            return 路由['source'].取脚本来源(路由['script']['scriptKey']).然后(包装源)#读完再包装
        if 自身._脚本.曾不支持(参数['scriptId']) or 参数['scriptId'].startswith('client:'):#Client失效
            raise 检查器错误('Client 脚本已不可用')#抛错
        return 自身._原生.请求('Debugger.getScriptSource',参数)#原生

    def _内容搜索(自身,参数):#内容搜索
        'Debugger.searchInContent，返回期约'
        精确键(参数,['scriptId','query','caseSensitive','isRegex'],'Debugger.searchInContent 参数')#键
        if not isinstance(参数.get('scriptId'),str) or not isinstance(参数.get('query'),str):#缺必填
            raise 检查器错误('Debugger.searchInContent 需要 scriptId 和 query')#抛错
        if 参数.get('caseSensitive') is not None and not isinstance(参数['caseSensitive'],bool):#大小写类型
            raise 检查器错误('Debugger.searchInContent 的 caseSensitive 必须是布尔')#抛错
        if 参数.get('isRegex') is not None and not isinstance(参数['isRegex'],bool):#正则类型
            raise 检查器错误('Debugger.searchInContent 的 isRegex 必须是布尔')#抛错
        路由=自身._脚本.解析(参数['scriptId'])#路由
        if 路由 is None:#无本地
            if 自身._脚本.曾不支持(参数['scriptId']) or 参数['scriptId'].startswith('client:'):#Client失效
                raise 检查器错误('Client 脚本已不可用')#抛错
            return 自身._原生.请求('Debugger.searchInContent',参数)#原生
        def 搜索源(源):#源读完后调用
            '按行搜索并包装成 CDP 结果'
            return {'result':按行搜索(源,参数['query'],参数.get('caseSensitive') is True,参数.get('isRegex') is True)}#结果
        return 路由['source'].取脚本来源(路由['script']['scriptKey']).然后(搜索源)#读完再搜索

    def _帧上求值(自身,参数):#帧上求值
        'Debugger.evaluateOnCallFrame，返回期约'
        解析=解析调用帧求值(参数)#解析
        if 解析['callFrameId'].startswith('client:'):#Client不可用
            raise 检查器错误('Client 原生调试不可用')#抛错
        领域=自身._调用帧realms.get(解析['callFrameId'])#调用帧 realm
        if 领域 is None: 领域=自身._支持调试的()#??支持调试的 realm
        对象组=解析.get('objectGroup')#对象组
        if 对象组 is None: 对象组='backtrace'#??backtrace，空串合法
        def 投影结果(完成):#帧上求值完成后调用
            '经 Runtime 对象表投影'
            return 自身.运行时.投影完成(领域,完成,对象组)#投影
        return 调试后端(领域).帧上求值({**解析,'objectGroup':对象组}).然后(投影结果)#求值完成后再投影

    def _暂停(自身):#暂停
        'Debugger.pause，返回期约'
        支持=[领域 for 领域 in 自身.realms.全部() if _能力(领域.debugger)['state']=='supported']#支持的
        if len(支持)==0:#全不支持
            raise 检查器错误('当前所有活动 realm 都不支持 Debugger.pause')#抛错
        return 期约扩展.全部([调试后端(领域).暂停() for 领域 in 支持]).然后(合并结果)#全部暂停后合并

    def _恢复(自身,参数):#恢复
        'Debugger.resume，返回期约'
        精确键(参数,['terminateOnResume'],'Debugger.resume 参数')#键
        请求=可选布尔(参数,'terminateOnResume')#可选
        支持=[领域 for 领域 in 自身.realms.全部() if _能力(领域.debugger)['state']=='supported']#支持的
        if len(支持)==0:#全不支持
            raise 检查器错误('当前所有活动 realm 都不支持 Debugger.resume')#抛错
        return 期约扩展.全部([调试后端(领域).恢复(请求) for 领域 in 支持]).然后(合并结果)#全部恢复后合并

    def _转发原生(自身,请求):#转发原生
        '转发原生 Debugger 方法'
        try:#校验路由
            不支持=自身._不支持路由(请求['params'])#不支持原因
            if 不支持 is not None:#有
                raise 检查器错误(不支持)#抛错
            参数=自身.运行时.原生参数(请求['params'])#本地化参数
        except Exception as 错误:#原生参数本地化可能抛检查器错误/KeyError，契约未定所以收不窄
            发送cdp失败(自身.传输,请求,错误)#失败响应
            return#返回
        def 原生请求():#原生请求体
            '转发原生方法，返回期约'
            return 自身._原生.请求(请求['method'],参数)#原生
        响应cdp请求(自身.传输,请求,原生请求)#原生请求

    def _不支持路由(自身,参数):#不支持路由
        '检查不支持原因'
        脚本id=取请求脚本id(参数)#脚本id
        if 脚本id is not None:#有脚本
            路由=自身._脚本.解析(脚本id)#路由
            if 路由 is not None and _能力(路由['realm'].debugger)['state']=='unsupported':#不支持
                return _能力(路由['realm'].debugger)['reason']#原因
            if 路由 is None and 自身._脚本.曾不支持(脚本id):#已退役
                return 'Client 脚本已不可用'#原因
        if isinstance(参数.get('url'),str):#有URL
            路由=自身._脚本.按url(参数['url'])#按URL
            if 路由 is not None and _能力(路由['realm'].debugger)['state']=='unsupported':#不支持
                return _能力(路由['realm'].debugger)['reason']#原因
        if isinstance(参数.get('urlRegex'),str):#有正则
            路由=自身._脚本.按url模式(参数['urlRegex'])#按模式
            if 路由 is not None and _能力(路由['realm'].debugger)['state']=='unsupported':#不支持
                return _能力(路由['realm'].debugger)['reason']#原因
        if isinstance(参数.get('scriptHash'),str):#有哈希
            路由=自身._脚本.按哈希(参数['scriptHash'])#按哈希
            if 路由 is not None and _能力(路由['realm'].debugger)['state']=='unsupported':#不支持
                return _能力(路由['realm'].debugger)['reason']#原因
        if isinstance(参数.get('objectId'),str):#有对象
            路由=自身.运行时.对象路由(参数['objectId'])#对象路由
            if 路由 is not None and _能力(路由['realm'].debugger)['state']=='unsupported':#不支持
                return _能力(路由['realm'].debugger)['reason']#原因
        return None#可转发

    def _接收realm(自身,事件):#处理realm事件
        '打开或关闭'
        if 事件['type']=='opened':#打开
            if 自身._已启用:#已启用
                def 记录启用失败(错误):#新 realm 启用被拒绝后调用
                    '记录启用失败的 realm'
                    print(f'检查器无法启用 Debugger realm {事件["session"].descriptor.label}:',错误)#记录
                自身._启用realm(事件['session']).捕获(记录启用失败)#启用失败只记录
            return#返回
        会话=事件['session']#会话
        源拆=自身._源拆除器.pop(会话.descriptor.realmId,None)#拆源
        if 源拆 is not None:#有
            源拆()#回调
        调拆=自身._调试拆除器.pop(会话.descriptor.realmId,None)#拆调试
        if 调拆 is not None:#有
            调拆()#回调
        for 帧id,所有者 in list(自身._调用帧realms.items()):#扫帧
            if 所有者 is 会话:#同会话
                del 自身._调用帧realms[帧id]#删除
        自身._脚本.移除realm(会话)#移除脚本

    def _启用realm(自身,领域):#启用单个realm
        '附着并启用，返回期约，目录发布后兑现'
        自身._附着能力(领域)#附着
        调试=_能力(领域.debugger)#能力
        if 调试['state']!='supported':#不支持调试
            return 自身._发布目录(领域)#只发布目录
        def 发布目录(启用结果):#启用完成后调用
            '发布目录'
            return 自身._发布目录(领域)#发布目录
        return 调试['backend'].启用(自身._启用请求).然后(发布目录)#启用完成后再发布目录

    def _附着能力(自身,领域):#附着能力
        '附着源与调试订阅'
        源=_能力(领域.sources)#源能力
        if 源['state']=='supported' and 领域.descriptor.realmId not in 自身._源拆除器:#源未附着
            后端=源['backend']#源后端
            def 收脚本(脚本):#脚本订阅
                '已启用则发布脚本'
                if 自身._已启用:#已启用
                    自身._发布脚本(领域,后端,脚本)#发布
            自身._源拆除器[领域.descriptor.realmId]=后端.订阅(收脚本)#订阅脚本
        调试=_能力(领域.debugger)#调试能力
        if 调试['state']=='supported' and 领域.descriptor.realmId not in 自身._调试拆除器:#调试未附着
            def 收调试(事件):#调试订阅
                '已启用则发布调试事件'
                if 自身._已启用:#已启用
                    自身._发布调试事件(领域,事件)#发布
            自身._调试拆除器[领域.descriptor.realmId]=调试['backend'].订阅(收调试)#订阅事件

    def _发布目录(自身,领域):#发布目录
        '列出并发布脚本，返回期约，发布完成后兑现'
        源=_能力(领域.sources)#源
        if not 自身._已启用 or 源['state']=='unsupported':#跳过
            已跳过=期约扩展()#无需发布时的期约
            已跳过.解决()#无结果，直接解决
            return 已跳过#返回已解决的期约
        def 发布脚本列表(脚本列表):#列脚本完成后调用
            '逐个发布脚本'
            for 脚本 in 脚本列表:#发布
                自身._发布脚本(领域,源['backend'],脚本)#发布
        return 源['backend'].列脚本().然后(发布脚本列表)#列脚本完成后再发布

    def _发布脚本(自身,realm,源,脚本):#发布脚本
        '注册并首次公告'
        注册=自身._脚本.注册({'realm':realm,'source':源,'script':脚本})#注册
        if 注册['fresh']:#首次
            自身.传输.发送(脚本已解析事件(realm,脚本))#公告

    def _发布调试事件(自身,realm,事件):#发布调试事件
        '暂停/恢复并投影'
        if 事件['type']=='paused':#暂停
            for 帧 in 事件['callFrames']:#记帧
                自身._调用帧realms[帧['callFrameId']]=realm#记帧
        elif 事件['type']=='resumed':#恢复
            for 帧id,所有者 in list(自身._调用帧realms.items()):#扫帧
                if 所有者 is realm:#同realm
                    del 自身._调用帧realms[帧id]#删除
            自身.运行时.释放投影组('backtrace')#释回溯
        自身.传输.发送(调试器事件(realm,事件,自身.运行时))#发送

    def _支持调试的(自身):#找支持调试的realm
        '找支持调试的 realm'
        for 候选 in 自身.realms.全部():#查找
            if _能力(候选.debugger)['state']=='supported':#支持
                return 候选#返回
        raise 检查器错误('当前没有活动 realm 支持调用帧求值')#无

    def _卸能力(自身):#卸全部能力
        '卸全部能力'
        for 拆除 in 自身._源拆除器.values():#拆源
            拆除()#回调
        自身._源拆除器.clear()#清源
        for 拆除 in 自身._调试拆除器.values():#拆调试
            拆除()#回调
        自身._调试拆除器.clear()#清调试

    def _响应(自身,请求,操作):#响应请求
        '委托协议响应'
        响应cdp请求(自身.传输,请求,操作)#委托

def _能力(值):#能力面
    '能力已是 dict'
    return 值#原样

def 调试后端(realm):#取调试后端
    '取调试后端'
    调试=_能力(realm.debugger)#能力
    if 调试['state']=='unsupported':#不支持
        raise 检查器错误(调试['reason'])#抛错
    return 调试['backend']#返回

def 合并结果(结果列表):#合并结果
    '合并多 realm 结果'
    合并={}#目标
    for 结果 in 结果列表:#合并
        合并.update(结果)#合并
    return 合并#返回

def 按行搜索(源,查询,区分大小写,是正则):#按行搜索
    '按行搜索源文本'
    表达式=re.compile(查询,re.ASCII if 区分大小写 else re.I|re.ASCII) if 是正则 else None#正则
    期望=查询 if 区分大小写 else 查询.lower()#期望子串
    结果=[]#结果
    for 行号,行内容 in enumerate(源.split('\n')):#扫行
        命中=表达式.search(行内容) is not None if 表达式 is not None else (行内容 if 区分大小写 else 行内容.lower()).find(期望)>=0#匹配
        if 命中:#收录
            结果.append({'lineNumber':行号,'lineContent':行内容})#收录
    return 结果#返回
