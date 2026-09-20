"""加载器：为已挂载的插件包自动登记 Typert 清单。"""
from json import dumps as 编码json,loads as 解码json
from os.path import dirname as 目录名,join as 拼接路径
from pathlib import Path as 路径
from traceback import print_exc as 打印错误
from ..注册表.类型 import Typert贡献 as 贡献#贡献字典构造（dict 别名）

成员种类=set(('property','method','getter','setter','call','construct','index'))#允许的成员种类
宿主导出='./typert'#包导出键
名称='typert-loader'#插件名
依赖=('typert','loader')#依赖服务
配置={'packages':[]}#默认配置

def 校验清单(包名,导出):
    """校验动态导入模块的 TYPERT 导出。"""
    if not isinstance(导出,dict):
        raise TypeError(f'typert-loader: {包名} exports "{宿主导出}" but its module has no TYPERT manifest object')
    if 导出.get('package')!=包名:
        raise ValueError(f'typert-loader: {包名} TYPERT manifest names package {编码json(导出.get("package"))} — the manifest must be owned by the package that exports it')
    if 导出.get('face')!='host':
        raise ValueError(f'typert-loader: {包名} exports "{宿主导出}" but TYPERT.face is not "host"')
    模式列表=导出.get('schemas')
    if not isinstance(模式列表,list):
        raise TypeError(f'typert-loader: {包名} TYPERT.schemas must be an array')
    for 一项 in 模式列表:
        if not isinstance(一项,dict):
            raise TypeError(f'typert-loader: {包名} TYPERT.schemas contains a non-object schema')
        要求字符串(包名,一项,'name','schema')
        if not callable(一项.get('create')):
            raise TypeError(f'typert-loader: {包名} TYPERT schema "{一项.get("name")}" has no create() factory')
    模型=要求对象(包名,导出.get('model'),'TYPERT.model')
    服务列表=要求数组(包名,模型.get('services'),'TYPERT.model.services')
    事件列表=要求数组(包名,模型.get('events'),'TYPERT.model.events')
    对象列表=要求数组(包名,模型.get('objects'),'TYPERT.model.objects')
    for 一项 in 服务列表:
        服务项=要求对象(包名,一项,'service')
        要求文档(包名,服务项,'service')
        要求字符串(包名,服务项,'key','service')
        要求字符串(包名,服务项,'exportName','service')
        要求成员(包名,服务项.get('members'),f'service "{服务项.get("key")}"')
        要求类型(包名,服务项.get('types'),f'service "{服务项.get("key")}"')
    for 一项 in 事件列表:
        事件项=要求对象(包名,一项,'event')
        要求文档(包名,事件项,'event')
        要求字符串(包名,事件项,'name','event')
        要求字符串(包名,事件项,'signature',f'event "{事件项.get("name")}"')
        if 事件项.get('mode') is not None and not isinstance(事件项.get('mode'),str):
            raise TypeError(f'typert-loader: {包名} event "{事件项.get("name")}" mode must be a string')
    for 一项 in 对象列表:
        对象项=要求对象(包名,一项,'object')
        要求文档(包名,对象项,'object')
        要求字符串(包名,对象项,'name','object')
        要求字符串(包名,对象项,'exportName','object')
        要求成员(包名,对象项.get('members'),f'object "{对象项.get("name")}"')
        要求类型(包名,对象项.get('types'),f'object "{对象项.get("name")}"')
    for 一项 in 要求数组(包名,导出.get('invocations'),'TYPERT.invocations'):
        要求调用(包名,一项)
    return 导出

def 要求对象(包名,值,主语):
    """要求值为对象。"""
    if not isinstance(值,dict):
        raise TypeError(f'typert-loader: {包名} {主语} must be an object')
    return 值

def 要求数组(包名,值,主语):
    """要求值为数组。"""
    if not isinstance(值,list):
        raise TypeError(f'typert-loader: {包名} {主语} must be an array')
    return 值

def 要求字符串(包名,值,键,主语):
    """要求字段为非空字符串。"""
    字段=值.get(键)
    if not isinstance(字段,str) or 字段=='':
        raise TypeError(f'typert-loader: {包名} {主语} has a missing or empty {键}')

def 要求文档(包名,值,主语):
    """要求文档字段形态。"""
    要求数组(包名,值.get('tags'),f'{主语}.tags')
    for 键 in ('description','summary','jsDoc'):
        if 值.get(键) is not None and not isinstance(值.get(键),str):
            raise TypeError(f'typert-loader: {包名} {主语}.{键} must be a string')

def 要求成员(包名,值,主语):
    """要求成员列表形态。"""
    for 一项 in 要求数组(包名,值,f'{主语}.members'):
        成员=要求对象(包名,一项,f'{主语} member')
        要求字符串(包名,成员,'name',f'{主语} member')
        要求字符串(包名,成员,'signature',f'{主语} member')
        if 成员.get('kind') not in 成员种类:
            raise TypeError(f'typert-loader: {包名} {主语} member "{成员.get("name")}" has invalid kind')

def 要求类型(包名,值,主语):
    """要求类型列表形态。"""
    for 一项 in 要求数组(包名,值,f'{主语}.types'):
        类型项=要求对象(包名,一项,f'{主语} type')
        要求字符串(包名,类型项,'name',f'{主语} type')
        要求字符串(包名,类型项,'declaration',f'{主语} type')

def 要求调用(包名,值):
    """要求调用清单形态。"""
    调用=要求对象(包名,值,'invocation')
    for 键 in ('id','service','namespace','method'):
        要求字符串(包名,调用,键,'invocation')
    标识=调用.get('id')
    接收者=要求对象(包名,调用.get('invocation'),f'invocation "{标识}" receiver')
    if 接收者.get('kind')=='context':
        要求字符串(包名,接收者,'context',f'invocation "{标识}" Context receiver')
        要求字符串(包名,接收者,'wire',f'invocation "{标识}" Context receiver')
        要求严格编解码(包名,接收者.get('codec'),f'invocation "{标识}" Context codec')
    elif 接收者.get('kind')!='direct':
        raise TypeError(f'typert-loader: {包名} invocation "{标识}" receiver kind must be "direct" or "context"')
    线路集合=set()
    参数映射={}
    查找计数=0
    for 一项 in 要求数组(包名,调用.get('parameters'),f'invocation "{标识}" parameters'):
        参数=要求对象(包名,一项,f'invocation "{标识}" parameter')
        要求字符串(包名,参数,'name',f'invocation "{标识}" parameter')
        要求字符串(包名,参数,'wire',f'invocation "{标识}" parameter')
        线路=参数.get('wire')
        if 线路 in 线路集合:
            raise ValueError(f'typert-loader: {包名} invocation "{标识}" repeats wire field "{线路}"')
        线路集合.add(线路)
        if 参数.get('source')=='lookup':
            查找计数+=1
            要求字符串(包名,参数,'lookup',f'invocation "{标识}" lookup parameter')
        elif 参数.get('source')=='json':
            if 参数.get('lookup') is not None:
                raise ValueError(f'typert-loader: {包名} invocation "{标识}" JSON parameter declares a lookup')
        else:
            raise TypeError(f'typert-loader: {包名} invocation "{标识}" parameter source must be "json" or "lookup"')
        参数映射[线路]=参数
        要求严格编解码(包名,参数.get('codec'),f'invocation "{标识}" parameter codec')
    if 调用.get('cancellation') is not None:
        取消=要求对象(包名,调用.get('cancellation'),f'invocation "{标识}" cancellation')
        if 取消.get('parameter')!='signal':
            raise ValueError(f'typert-loader: {包名} invocation "{标识}" cancellation parameter must be "signal"')
    if 调用.get('scope') is not None:
        if 接收者.get('kind')!='direct':
            raise ValueError(f'typert-loader: {包名} invocation "{标识}" Context receiver cannot declare a direct scope projection')
        作用域=要求对象(包名,调用.get('scope'),f'invocation "{标识}" scope')
        要求字符串(包名,作用域,'context',f'invocation "{标识}" scope')
        要求字符串(包名,作用域,'wire',f'invocation "{标识}" scope')
        参数=参数映射.get(作用域.get('wire'))
        if 查找计数!=1 or 参数 is None or 参数.get('source')!='lookup' or 参数.get('lookup')!=作用域.get('context'):
            raise ValueError(f'typert-loader: {包名} invocation "{标识}" scope wire "{作用域.get("wire")}" must select its only lookup parameter')
    if 接收者.get('kind')=='context' and 接收者.get('wire') in 线路集合:
        raise ValueError(f'typert-loader: {包名} invocation "{标识}" repeats Context wire field "{接收者.get("wire")}"')
    要求严格编解码(包名,调用.get('result'),f'invocation "{标识}" result codec')
    if 调用.get('sourceLocation') is not None:
        位置=要求对象(包名,调用.get('sourceLocation'),f'invocation "{标识}" sourceLocation')
        要求字符串(包名,位置,'file',f'invocation "{标识}" sourceLocation')
        for 键 in ('line','column'):
            数字=位置.get(键)
            if not isinstance(数字,int) or isinstance(数字,bool) or 数字<1:
                raise TypeError(f'typert-loader: {包名} invocation "{标识}" sourceLocation.{键} must be a positive integer')

def 要求严格编解码(包名,值,主语):
    """要求严格编解码形态。"""
    编解码=要求对象(包名,值,主语)
    if 编解码.get('mode')!='strict':
        raise TypeError(f'typert-loader: {包名} {主语} must use a strict codec')
    要求字符串(包名,编解码,'typeSymbol',主语)
    if not callable(编解码.get('create')):
        raise TypeError(f'typert-loader: {包名} {主语} has no create() factory')

def 导出键(包名,导出字段):
    """解析 ./typert 导出路径。"""
    if not isinstance(导出字段,dict):
        return None
    if 宿主导出 not in 导出字段:
        return None
    目标=导出字段[宿主导出]
    if isinstance(目标,str):
        return 目标
    if isinstance(目标,dict):
        回退=目标.get('default')
        if isinstance(回退,str):
            return 回退
    raise TypeError(f'typert-loader: {包名} exports["{宿主导出}"] must be a string or an object with a string default')

def 转错误(错误):
    """把任意失败规范成异常。"""
    return 错误 if isinstance(错误,BaseException) else RuntimeError(str(错误))

def 应用(上下文,配置=None):
    """扫描当前加载器条目，并在生命周期内跟随挂载与卸载。"""
    实际配置=配置 or {}
    基础地址=getattr(上下文,'基础地址',None) or getattr(上下文,'baseUrl',None)
    if 基础地址 is None:
        raise RuntimeError('typert-loader: ctx.baseUrl is unset — the loader needs the config-tree anchor to resolve plugin packages')
    已配置=set(实际配置.get('packages') or [])
    已登记={}
    进行中={}
    制品路径={}
    清单缓存={}
    脏名=set()
    刷新排队=False
    活动=True

    def 解析制品(包名):
        """解析包的 typert 制品。"""
        if 包名 in 制品路径:
            return 制品路径[包名]
        第一斜杠=包名.find('/')
        if 第一斜杠>=0 and (not 包名.startswith('@') or 包名.find('/',第一斜杠+1)>=0):
            if 包名 in 已配置:
                raise RuntimeError(f'typert-loader: configured package "{包名}" cannot be resolved from the config tree — add it to the composition package dependencies or remove it from packages')
            制品路径[包名]=None
            return None
        try:
            包解析器=None
            if hasattr(上下文,'获取'):
                包解析器=上下文.获取('pluginPackages')
            elif hasattr(上下文,'get'):
                包解析器=上下文.get('pluginPackages')
            已解析包=None
            if 包解析器 is not None:
                if hasattr(包解析器,'包属于'):
                    已解析包=包解析器.包属于(包名,基础地址)
                elif hasattr(包解析器,'packageOf'):
                    已解析包=包解析器.packageOf(包名,基础地址)
                if 已解析包 is None:
                    raise RuntimeError('package is absent from the active resolver')
            if 已解析包 is None:
                清单路径=拼接路径(str(基础地址),包名,'package.json')
                清单=None
            else:
                清单路径=已解析包.get('manifestPath') if isinstance(已解析包,dict) else getattr(已解析包,'清单路径',None) or getattr(已解析包,'manifestPath',None)
                清单=已解析包.get('manifest') if isinstance(已解析包,dict) else getattr(已解析包,'清单',None) or getattr(已解析包,'manifest',None)
        except Exception as 原因:
            if 包名 in 已配置:
                raise RuntimeError(f'typert-loader: configured package "{包名}" cannot be resolved from the config tree — add it to the composition package dependencies or remove it from packages') from 原因
            制品路径[包名]=None
            return None
        if 清单 is None:
            清单=解码json(路径(清单路径).read_text(encoding='utf-8'))
        清单名=清单.get('name') if isinstance(清单.get('name'),str) else 包名
        相对=导出键(清单名,清单.get('exports'))
        if 相对 is None and 包名 in 已配置:
            raise RuntimeError(f'typert-loader: configured package "{包名}" does not export "{宿主导出}"')
        已解析=None if 相对 is None else {'packageName':清单名,'path':拼接路径(目录名(清单路径),相对)}
        制品路径[包名]=已解析
        return 已解析

    def 加载清单(包名,路径文本):
        """导入并校验清单。"""
        if 包名 in 清单缓存:
            return 清单缓存[包名]
        模块=路径(路径文本)
        数据=解码json(模块.read_text(encoding='utf-8')) if 模块.suffix=='.json' else {'TYPERT':贡献(package=包名,face='host')}
        结果=校验清单(包名,数据.get('TYPERT'))
        清单缓存[包名]=结果
        return 结果

    def 合格(条目名):
        """判断条目是否仍应登记。"""
        if 条目名 in 已配置:
            return True
        加载器=getattr(上下文,'加载器',None) or getattr(上下文,'loader',None)
        if 加载器 is None:
            return False
        条目函数=getattr(加载器,'条目',None) or getattr(加载器,'entries',None)
        if 条目函数 is None:
            return False
        for 条目 in 条目函数():
            选项=getattr(条目,'选项',None) or getattr(条目,'options',None) or {}
            名称值=选项.get('name') if isinstance(选项,dict) else getattr(选项,'name',None)
            纤维=getattr(条目,'纤维',None) if hasattr(条目,'纤维') else getattr(条目,'fiber',None)
            禁用=getattr(条目,'禁用',False) if hasattr(条目,'禁用') else getattr(条目,'disabled',False)
            if 名称值==条目名 and 纤维 is not None and not 禁用:
                return True
        return False

    def 处理一项(条目名):
        """对单个条目做一次调和。"""
        if not 合格(条目名):
            释放=已登记.pop(条目名,None)
            if 释放 is not None:
                释放()
            return None
        if 条目名 in 已登记 or 条目名 in 进行中:
            return None
        制品=解析制品(条目名)
        if 制品 is None:
            return None
        def 任务():
            清单=加载清单(制品['packageName'],制品['path'])
            if not 活动 or not 合格(条目名) or 条目名 in 已登记:
                return
            注册表=getattr(上下文,'typert',None)
            if 注册表 is None:
                return
            已登记[条目名]=注册表.登记(清单)
        进行中[条目名]=任务
        try:
            任务()
        finally:
            进行中.pop(条目名,None)
        return None

    def 刷新(出错回调):
        """冲刷脏条目。"""
        任务列表=[]
        for 条目名 in list(脏名):
            脏名.discard(条目名)
            try:
                处理一项(条目名)
            except Exception as 错误:
                出错回调(转错误(错误))
        return 任务列表

    def 停用():
        nonlocal 活动
        活动=False
        脏名.clear()

    if hasattr(上下文,'效果'):
        上下文.效果(lambda:停用,'typert loader lifetime')

    def 插件事件(纤维):
        nonlocal 刷新排队
        条目=getattr(纤维,'条目',None) or getattr(纤维,'entry',None)
        选项=getattr(条目,'选项',None) if 条目 is not None else None
        if 选项 is None:
            选项=getattr(条目,'options',None) if 条目 is not None else None
        条目名=选项.get('name') if isinstance(选项,dict) else getattr(选项,'name',None) if 选项 is not None else None
        if 条目名 is None:
            return
        脏名.add(条目名)
        if 刷新排队:
            return
        刷新排队=True
        def 冲刷():
            nonlocal 刷新排队
            刷新排队=False
            if not 活动:
                return
            刷新(lambda 错误:打印错误())
        冲刷()

    if hasattr(上下文,'on'):
        上下文.on('internal/plugin',插件事件)
    for 包名 in 已配置:
        脏名.add(包名)
    加载器=getattr(上下文,'加载器',None) or getattr(上下文,'loader',None)
    if 加载器 is not None:
        条目函数=getattr(加载器,'条目',None) or getattr(加载器,'entries',None)
        if 条目函数 is not None:
            for 条目 in 条目函数():
                选项=getattr(条目,'选项',None) or getattr(条目,'options',None) or {}
                名称值=选项.get('name') if isinstance(选项,dict) else getattr(选项,'name',None)
                if 名称值 is not None:
                    脏名.add(名称值)
    失败=[]
    刷新(lambda 错误:失败.append(错误))
    if 失败:
        文本='\n'.join(f'  - {一项.args[0] if 一项.args else 一项}' for 一项 in 失败)
        raise RuntimeError(f'typert-loader: {len(失败)} typert contributor(s) failed to register:\n{文本}')

__all__=['宿主导出','名称','依赖','配置','校验清单','应用']
name=名称
inject=依赖
apply=应用
