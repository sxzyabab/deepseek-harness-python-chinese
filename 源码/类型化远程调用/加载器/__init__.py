'为已挂载的插件包自动登记 Typert 清单'
import hashlib,importlib.util,json,os,sys
from ...依赖.工具 import 文件url转路径

成员种类=set(('property','method','getter','setter','call','construct','index'))
宿主导出='./typert'
名称='typert-loader'
依赖=['typert','加载器']

class 配置模式:
    'packages 缺省为空数组。空数组表示不追加显式包，仍扫描加载器条目'
    def 校验数据(自身,数据):
        '归一成只含 packages 的字典'
        if 数据 is None:
            return {'packages':[]}
        if not isinstance(数据,dict):
            raise TypeError('typert-loader: 配置必须是对象')
        if 'packages' not in 数据 or 数据['packages'] is None:
            包列表=[]
        else:
            包列表=数据['packages']
        if not isinstance(包列表,list):
            raise TypeError('typert-loader: packages 必须是数组')
        for 名 in 包列表:
            if not isinstance(名,str) or len(名)==0:
                raise TypeError('typert-loader: packages 的每一项必须是非空字符串')
        return {'packages':list(包列表)}

配置=配置模式()

def 校验清单(包名,导出):
    '校验动态导入模块的 TYPERT 导出'
    if not isinstance(导出,dict):
        raise TypeError(f'typert-loader: {包名} 导出了 "{宿主导出}"，但模块里没有 TYPERT 清单对象')
    if 导出.get('package')!=包名:
        raise ValueError(
            f'typert-loader: {包名} 的 TYPERT 清单把 package 写成了 {json.dumps(导出.get("package"),ensure_ascii=False)}，清单必须属于导出它的包'
        )
    if 导出.get('face')!='host':
        raise ValueError(f'typert-loader: {包名} 导出了 "{宿主导出}"，但 TYPERT.face 不是 "host"')
    模式列表=导出.get('schemas')
    if not isinstance(模式列表,list):
        raise TypeError(f'typert-loader: {包名} 的 TYPERT.schemas 必须是数组')
    for 一项 in 模式列表:
        if not isinstance(一项,dict):
            raise TypeError(f'typert-loader: {包名} 的 TYPERT.schemas 里有非对象模式')
        要求字符串(包名,一项,'name','schema')
        if not callable(一项.get('create')):
            raise TypeError(f'typert-loader: {包名} 的 TYPERT 模式 "{一项.get("name")}" 没有 create() 工厂')
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
        if 'mode' in 事件项 and 事件项['mode'] is not None and not isinstance(事件项['mode'],str):
            raise TypeError(f'typert-loader: {包名} 的事件 "{事件项.get("name")}" 的 mode 必须是字符串')
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
    '要求值为对象。空对象仍然是对象'
    if not isinstance(值,dict):
        raise TypeError(f'typert-loader: {包名} 的 {主语} 必须是对象')
    return 值

def 要求数组(包名,值,主语):
    '要求值为数组。空数组仍然是数组'
    if not isinstance(值,list):
        raise TypeError(f'typert-loader: {包名} 的 {主语} 必须是数组')
    return 值

def 要求字符串(包名,值,键,主语):
    '要求字段为非空字符串'
    字段=值.get(键)
    if not isinstance(字段,str) or len(字段)==0:
        raise TypeError(f'typert-loader: {包名} 的 {主语} 缺少或空着 {键}')

def 要求文档(包名,值,主语):
    '要求文档字段形态'
    要求数组(包名,值.get('tags'),f'{主语}.tags')
    for 键 in ('description','summary','jsDoc'):
        if 键 in 值 and 值[键] is not None and not isinstance(值[键],str):
            raise TypeError(f'typert-loader: {包名} 的 {主语}.{键} 必须是字符串')

def 要求成员(包名,值,主语):
    '要求成员列表形态'
    for 一项 in 要求数组(包名,值,f'{主语}.members'):
        成员=要求对象(包名,一项,f'{主语} member')
        要求字符串(包名,成员,'name',f'{主语} member')
        要求字符串(包名,成员,'signature',f'{主语} member')
        if 成员.get('kind') not in 成员种类:
            raise TypeError(f'typert-loader: {包名} 的 {主语} 成员 "{成员.get("name")}" 的 kind 无效')

def 要求类型(包名,值,主语):
    '要求类型列表形态'
    for 一项 in 要求数组(包名,值,f'{主语}.types'):
        类型项=要求对象(包名,一项,f'{主语} type')
        要求字符串(包名,类型项,'name',f'{主语} type')
        要求字符串(包名,类型项,'declaration',f'{主语} type')

def 要求调用(包名,值):
    '要求调用清单形态'
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
        raise TypeError(f'typert-loader: {包名} 的调用 "{标识}" 的接收者 kind 必须是 "direct" 或 "context"')
    线路集合=set()
    参数映射={}
    查找计数=0
    for 一项 in 要求数组(包名,调用.get('parameters'),f'invocation "{标识}" parameters'):
        参数=要求对象(包名,一项,f'invocation "{标识}" parameter')
        要求字符串(包名,参数,'name',f'invocation "{标识}" parameter')
        要求字符串(包名,参数,'wire',f'invocation "{标识}" parameter')
        线路=参数.get('wire')
        if 线路 in 线路集合:
            raise ValueError(f'typert-loader: {包名} 的调用 "{标识}" 重复了线路字段 "{线路}"')
        线路集合.add(线路)
        if 参数.get('source')=='lookup':
            查找计数+=1
            要求字符串(包名,参数,'lookup',f'invocation "{标识}" lookup parameter')
        elif 参数.get('source')=='json':
            if 参数.get('lookup') is not None:
                raise ValueError(f'typert-loader: {包名} 的调用 "{标识}" 的 JSON 参数声明了 lookup')
        else:
            raise TypeError(f'typert-loader: {包名} 的调用 "{标识}" 的参数 source 必须是 "json" 或 "lookup"')
        参数映射[线路]=参数
        要求严格编解码(包名,参数.get('codec'),f'invocation "{标识}" parameter codec')
    if 'cancellation' in 调用 and 调用['cancellation'] is not None:
        取消=要求对象(包名,调用['cancellation'],f'invocation "{标识}" cancellation')
        if 取消.get('parameter')!='signal':
            raise ValueError(f'typert-loader: {包名} 的调用 "{标识}" 的取消参数必须是 "signal"')
    if 'scope' in 调用 and 调用['scope'] is not None:
        if 接收者.get('kind')!='direct':
            raise ValueError(f'typert-loader: {包名} 的调用 "{标识}" 的 Context 接收者不能再声明直接作用域投影')
        作用域=要求对象(包名,调用['scope'],f'invocation "{标识}" scope')
        要求字符串(包名,作用域,'context',f'invocation "{标识}" scope')
        要求字符串(包名,作用域,'wire',f'invocation "{标识}" scope')
        参数=参数映射.get(作用域.get('wire'))
        if 查找计数!=1 or 参数 is None or 参数.get('source')!='lookup' or 参数.get('lookup')!=作用域.get('context'):
            raise ValueError(f'typert-loader: {包名} 的调用 "{标识}" 的作用域线路 "{作用域.get("wire")}" 必须选中它唯一的 lookup 参数')
    if 接收者.get('kind')=='context' and 接收者.get('wire') in 线路集合:
        raise ValueError(f'typert-loader: {包名} 的调用 "{标识}" 重复了 Context 线路字段 "{接收者.get("wire")}"')
    要求严格编解码(包名,调用.get('result'),f'invocation "{标识}" result codec')
    if 'sourceLocation' in 调用 and 调用['sourceLocation'] is not None:
        位置=要求对象(包名,调用['sourceLocation'],f'invocation "{标识}" sourceLocation')
        要求字符串(包名,位置,'file',f'invocation "{标识}" sourceLocation')
        for 键 in ('line','column'):
            数字=位置.get(键)
            if not isinstance(数字,int) or isinstance(数字,bool) or 数字<1:
                raise TypeError(f'typert-loader: {包名} 的调用 "{标识}" 的 sourceLocation.{键} 必须是正整数')

def 要求严格编解码(包名,值,主语):
    '要求严格编解码形态'
    编解码=要求对象(包名,值,主语)
    if 编解码.get('mode')!='strict':
        raise TypeError(f'typert-loader: {包名} 的 {主语} 必须使用严格编解码')
    要求字符串(包名,编解码,'typeSymbol',主语)
    for 方法名 in ('decode','encode'):
        if 方法名 in 编解码 and 编解码[方法名] is not None and not callable(编解码[方法名]):
            raise TypeError(f'typert-loader: {包名} 的 {主语} 的 {方法名} 必须是函数')
    if not callable(编解码.get('create')):
        raise TypeError(f'typert-loader: {包名} 的 {主语} 没有 create() 工厂')

def 导出键(包名,导出字段):
    '解析 ./typert 导出路径。没有该键时返回 None'
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
    raise TypeError(f'typert-loader: {包名} 的 exports["{宿主导出}"] 必须是字符串，或带字符串 default 的对象')

def 是子路径说明符(包名):
    '包根可以解析。子路径与多层作用域路径不能'
    第一斜杠=包名.find('/')
    if 第一斜杠<0:
        return False
    if not 包名.startswith('@'):
        return True
    return 包名.find('/',第一斜杠+1)>=0

def 基准目录(网址):
    '配置树锚点所在目录。file URL 先转成本地路径'
    文本=str(网址)
    if 文本.startswith('file:'):
        文本=文件url转路径(文本)
    if os.path.isdir(文本):
        return 文本
    return os.path.dirname(文本)

def 沿模块目录找包(包名,目录):
    '从目录向上找 node_modules 里的包根'
    片段=包名.split('/')
    当前=目录
    while True:
        候选=os.path.join(当前,'node_modules',*片段)
        if os.path.isfile(os.path.join(候选,'package.json')):
            return 候选
        上一=os.path.dirname(当前)
        if 上一==当前:
            return None
        当前=上一

def 加载模块(路径文本):
    '按文件加载清单模块。模块名用内容路径的摘要，避免把路径写进模块表'
    摘要=hashlib.sha256(os.path.abspath(路径文本).encode('utf-8')).hexdigest()[:16]
    模块名='typert_manifest_'+摘要
    已有=sys.modules.get(模块名)
    if 已有 is not None:
        return 已有
    规格=importlib.util.spec_from_file_location(模块名,路径文本)
    if 规格 is None or 规格.loader is None:
        raise ImportError('无法加载清单模块')
    模块=importlib.util.module_from_spec(规格)
    sys.modules[模块名]=模块
    已执行=False
    try:
        规格.loader.exec_module(模块)
        已执行=True
    finally:
        if not 已执行:
            sys.modules.pop(模块名,None)
    return 模块

def 读导出(路径文本):
    'JSON 清单读 TYPERT 键；Python 模块读 TYPERT 属性。失败说明不带路径'
    if 路径文本.endswith('.json'):
        try:
            文件=open(路径文本,encoding='utf-8')
            try:
                数据=json.load(文件)
            finally:
                文件.close()
        except (OSError,ValueError):
            raise RuntimeError('typert-loader: 清单文件无法读取') from None
        if not isinstance(数据,dict) or 'TYPERT' not in 数据:
            return None
        return 数据['TYPERT']
    try:
        模块=加载模块(路径文本)
    except Exception:
        raise RuntimeError('typert-loader: 清单模块无法导入') from None
    if not hasattr(模块,'TYPERT'):
        return None
    return getattr(模块,'TYPERT')

def 条目名属于(条目):
    '插件配置上的 name。缺键与显式 None 都视为没有名字'
    选项=getattr(条目,'选项',None)
    if not isinstance(选项,dict) or 'name' not in 选项:
        return None
    return 选项['name']

def 应用(上下文,配置=None):
    '扫描当前加载器条目，并在本插件寿命内跟随挂载与卸载'
    实际配置=配置模式().校验数据(配置)
    基础地址=getattr(上下文,'基准网址',None)
    if 基础地址 is None:
        raise RuntimeError('typert-loader: 上下文没有基准网址，无法从配置树解析插件包')
    已配置=set(实际配置['packages'])
    已登记={}
    进行中=set()
    制品路径={}
    负缓存=set()
    清单缓存={}
    脏名=set()
    正在冲刷=False
    活动=True

    def 登记寿命():
        '卸载时停止接收新的脏条目'
        def 停用():
            nonlocal 活动
            活动=False
            脏名.clear()
        return 停用

    def 解析制品(包名):
        '解析包的 typert 制品。否定结论按包名缓存，重启前不失效'
        if 包名 in 负缓存:
            return None
        if 包名 in 制品路径:
            return 制品路径[包名]
        if 是子路径说明符(包名):
            if 包名 in 已配置:
                raise RuntimeError(f'typert-loader: 已配置的包 "{包名}" 不能从配置树解析，把它加进组合的包依赖，或从 packages 里去掉')
            负缓存.add(包名)
            return None
        try:
            包解析器=上下文.获取服务('pluginPackages',False)
            已解析包=None if 包解析器 is None else 包解析器.包属于(包名,基础地址)
            if 包解析器 is not None and 已解析包 is None:
                raise RuntimeError('活动解析器里没有这个包')
            if isinstance(已解析包,dict):
                清单路径=已解析包['manifestPath']
                清单=已解析包['manifest']
            else:
                目录=沿模块目录找包(包名,基准目录(基础地址))
                if 目录 is None:
                    raise RuntimeError('活动解析器里没有这个包')
                清单路径=os.path.join(目录,'package.json')
                文件=open(清单路径,encoding='utf-8')
                try:
                    清单=json.load(文件)
                finally:
                    文件.close()
        except Exception:
            if 包名 in 已配置:
                raise RuntimeError(
                    f'typert-loader: 已配置的包 "{包名}" 不能从配置树解析，把它加进组合的包依赖，或从 packages 里去掉'
                ) from None
            负缓存.add(包名)
            return None
        清单名=清单['name'] if isinstance(清单,dict) and isinstance(清单.get('name'),str) else 包名
        导出字段=清单.get('exports') if isinstance(清单,dict) else None
        相对=导出键(清单名,导出字段)
        if 相对 is None and 包名 in 已配置:
            raise RuntimeError(f'typert-loader: 已配置的包 "{包名}" 没有导出 "{宿主导出}"')
        if 相对 is None:
            负缓存.add(包名)
            return None
        已解析={'packageName':清单名,'path':os.path.join(os.path.dirname(清单路径),相对)}
        制品路径[包名]=已解析
        return 已解析

    def 加载清单(包名,路径文本):
        '导入并校验清单。同一包名只导入一次，失败也缓存'
        if 包名 in 清单缓存:
            缓存=清单缓存[包名]
            if isinstance(缓存,BaseException):
                raise 缓存
            return 缓存
        try:
            结果=校验清单(包名,读导出(路径文本))
        except Exception as 错误:
            清单缓存[包名]=错误
            raise
        清单缓存[包名]=结果
        return 结果

    def 合格(条目名):
        '显式配置的包始终合格。其余要有未禁用且已挂上纤程的同名条目'
        if 条目名 in 已配置:
            return True
        加载器=上下文.获取服务('加载器',False)
        if 加载器 is None:
            return False
        for 条目 in 加载器.列出插件配置():
            if 条目名属于(条目)==条目名 and getattr(条目,'纤程',None) is not None and not 条目.已禁用:
                return True
        return False

    def 处理一项(条目名):
        '对单个条目做一次调和'
        if not 合格(条目名):
            释放=已登记.pop(条目名,None)
            if 释放 is not None:
                释放()
            return
        if 条目名 in 已登记 or 条目名 in 进行中:
            return
        制品=解析制品(条目名)
        if 制品 is None:
            return
        进行中.add(条目名)
        try:
            清单=加载清单(制品['packageName'],制品['path'])
            if not 活动 or not 合格(条目名) or 条目名 in 已登记:
                return
            已登记[条目名]=上下文.typert.register(清单)
        finally:
            进行中.discard(条目名)

    def 冲刷(出错回调):
        '把脏名字冲掉。冲刷过程中新脏的名字留到下一轮'
        nonlocal 正在冲刷
        if 正在冲刷:
            return
        正在冲刷=True
        try:
            while len(脏名)>0:
                快照=list(脏名)
                for 条目名 in 快照:
                    脏名.discard(条目名)
                for 条目名 in 快照:
                    try:
                        处理一项(条目名)
                    except Exception as 错误:
                        出错回调(错误)
        finally:
            正在冲刷=False

    def 插件事件(纤程):
        '纤程挂上插件配置后，把条目名标脏并马上调和'
        条目=getattr(纤程,'插件配置',None)
        if 条目 is None:
            return
        条目名=条目名属于(条目)
        if 条目名 is None:
            return
        脏名.add(条目名)
        if 正在冲刷 or not 活动:
            return
        冲刷(上下文.日志.错误)

    上下文.副作用(登记寿命,'类型化远程调用加载器寿命')
    上下文.监听('internal/plugin',插件事件)
    for 包名 in 实际配置['packages']:
        脏名.add(包名)
    加载器=上下文.获取服务('加载器',False)
    if 加载器 is not None:
        for 条目 in 加载器.列出插件配置():
            条目名=条目名属于(条目)
            if 条目名 is not None:
                脏名.add(条目名)
    失败=[]
    冲刷(失败.append)
    if len(失败)>0:
        文本='\n'.join(f'  - {一项}' for 一项 in 失败)
        raise RuntimeError(f'typert-loader: {len(失败)} 个贡献者登记失败:\n{文本}')

__all__=['宿主导出','名称','依赖','配置','校验清单','应用']
name=名称
inject=依赖
Config=配置
apply=应用
