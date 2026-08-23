"""Typert Loader 集成：为已挂载的插件包自动注册清单。

对齐上游 `typert/loader/src/index.ts`。公开面仅中文名。
当一条 Loader 条目挂载时，解析该条目的 package.json；导出 `./typert` 的包
导入其宿主面并把 TYPERT 清单注册进 ctx.typert，条目卸载时撤回。
显式 packages 覆盖嵌在另一条 Loader 条目后面的插件。
扫描按条目名增量进行：internal/plugin 标脏，微任务 flush 再调和。
"""
import json,os,importlib.util#读清单、拼路径、动态导入
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现
是否thenable=cordis.工具.是否thenable#可等待

__all__=[#仅中文公开名
    '宿主导出键','名称','注入','配置','校验Typert清单','应用',
    'TYPERT_HOST_EXPORT','name','inject','Config','validateTypertManifest','apply',
]#公开面结束

宿主导出键='./typert'#package.json exports 里命名宿主面 typert 产物的键
TYPERT_HOST_EXPORT=宿主导出键#上游名
名称='typert-loader'#Cordis 插件名
name=名称#上游名
注入=['typert','loader']#依赖 typert 与 loader
inject=注入#上游名

成员种类=frozenset(['property','method','getter','setter','call','construct','index'])#合法成员 kind

配置={'packages':[]}#缺省只做 Loader 条目发现；packages 为显式包名列表
Config=配置#上游名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解开(值):#承诺则等待
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 收成错误(错误):#规范化未知失败
    """已是 Exception 则原样，否则包一层。"""
    return 错误 if isinstance(错误,BaseException) else Exception(str(错误))#规范化

def 取Typert导出(包名,导出面):#读 package.json exports["./typert"]
    """把 ./typert 导出收成相对路径，接受字符串和一层条件形式。"""
    if not isinstance(导出面,dict) or 导出面 is None:#没有 exports 面
        return None#未声明
    目标=导出面.get(宿主导出键)#取出 ./typert 目标
    if 目标 is None:#未声明该导出
        return None#跳过
    if isinstance(目标,str):#字符串形式
        return 目标#直接用
    if isinstance(目标,dict):#一层条件对象
        回退=目标.get('default')#取 default 条件
        if isinstance(回退,str):#default 是字符串
            return 回退#用
    raise Exception('typert-loader: '+包名+' exports["'+宿主导出键+'"] must be a string or an object with a string default')#非法导出形

def 要求对象(包名,值,主语):#要求普通对象
    """数组/null/非对象都不算。"""
    if not isinstance(值,dict) or 值 is None:#非法
        raise Exception('typert-loader: '+包名+' '+主语+' must be an object')#不是对象
    return 值#收成字典

def 要求数组(包名,值,主语):#要求数组
    """不是数组则抛。"""
    if not isinstance(值,list):#非法
        raise Exception('typert-loader: '+包名+' '+主语+' must be an array')#不是数组
    return 值#原样

def 要求字符串(包名,值,键,主语):#要求非空字符串字段
    """缺席、非字符串或空串则失败。"""
    字段=值.get(键) if isinstance(值,dict) else None#取出
    if not isinstance(字段,str) or len(字段)==0:#缺或空
        raise Exception('typert-loader: '+包名+' '+主语+' has a missing or empty '+键)#缺或空

def 要求文档(包名,值,主语):#要求文档字段形态
    """tags 必须是数组；可选字符串文档字段出现则必须是字符串。"""
    要求数组(包名,值.get('tags'),主语+'.tags')#tags
    for 键 in ('description','summary','jsDoc'):#可选字符串文档字段
        if 值.get(键) is not None and not isinstance(值.get(键),str):#出现则必须是字符串
            raise Exception('typert-loader: '+包名+' '+主语+'.'+键+' must be a string')#非字符串

def 要求成员们(包名,值,主语):#要求成员列表
    """逐条校验 name/signature/kind。"""
    for 项 in 要求数组(包名,值,主语+'.members'):#逐条成员
        成员=要求对象(包名,项,主语+' member')#成员必须是对象
        要求字符串(包名,成员,'name',主语+' member')#name
        要求字符串(包名,成员,'signature',主语+' member')#signature
        种类=成员.get('kind')#kind
        if not isinstance(种类,str) or 种类 not in 成员种类:#非法 kind
            raise Exception('typert-loader: '+包名+' '+主语+' member "'+str(成员.get('name'))+'" has invalid kind')#非法

def 要求类型们(包名,值,主语):#要求类型列表
    """逐条校验 name/declaration。"""
    for 项 in 要求数组(包名,值,主语+'.types'):#逐条类型
        类型=要求对象(包名,项,主语+' type')#类型必须是对象
        要求字符串(包名,类型,'name',主语+' type')#name
        要求字符串(包名,类型,'declaration',主语+' type')#declaration

def 是否严格模式实例(模式):#是否带 parse 的边界模式
    """schemastery / zod 兼容：必须是对象且有可调用 parse。"""
    if 模式 is None or not isinstance(模式,object):#非对象
        return False#否
    if isinstance(模式,(str,bytes,bytearray,int,float,bool,list)):#标量/数组
        return False#否
    return callable(getattr(模式,'parse',None))#有 parse

def 要求严格编解码(包名,值,主语):#要求 strict codec
    """mode 必须 strict；须有 typeSymbol 与可 parse 的 schema。"""
    编解码=要求对象(包名,值,主语)#codec 必须是对象
    if 编解码.get('mode')!='strict':#只接受 strict
        raise Exception('typert-loader: '+包名+' '+主语+' must use a strict codec')#不是 strict
    要求字符串(包名,编解码,'typeSymbol',主语)#typeSymbol
    if not 是否严格模式实例(编解码.get('schema')):#不是可 parse 实例
        raise Exception('typert-loader: '+包名+' '+主语+' is not backed by a zod v4 schema')#不是模式实例

def 要求调用(包名,值):#校验一条调用约定
    """校验 id/服务/命名空间/方法/参数/作用域/接收方。"""
    调用=要求对象(包名,值,'invocation')#必须是对象
    for 键 in ('id','service','namespace','method'):#四个必填字符串
        要求字符串(包名,调用,键,'invocation')#缺或空则失败
    标识=调用['id']#调用 id
    接收方=要求对象(包名,调用.get('invocation'),'invocation "'+标识+'" receiver')#接收方对象
    if 接收方.get('kind')=='context':#Context 接收方
        要求字符串(包名,接收方,'context','invocation "'+标识+'" Context receiver')#context
        要求字符串(包名,接收方,'wire','invocation "'+标识+'" Context receiver')#wire
        要求严格编解码(包名,接收方.get('codec'),'invocation "'+标识+'" Context codec')#codec
    elif 接收方.get('kind')!='direct':#既不是 context 也不是 direct
        raise Exception('typert-loader: '+包名+' invocation "'+标识+'" receiver kind must be "direct" or "context"')#非法 kind
    线路们=set()#已出现的 wire
    参数表={}#按 wire 索引参数
    查找数=0#lookup 源参数个数
    for 参数值 in 要求数组(包名,调用.get('parameters'),'invocation "'+标识+'" parameters'):#逐个参数
        参数=要求对象(包名,参数值,'invocation "'+标识+'" parameter')#参数必须是对象
        要求字符串(包名,参数,'name','invocation "'+标识+'" parameter')#name
        要求字符串(包名,参数,'wire','invocation "'+标识+'" parameter')#wire
        线路=参数['wire']#本参数 wire
        if 线路 in 线路们:#重复
            raise Exception('typert-loader: '+包名+' invocation "'+标识+'" repeats wire field "'+线路+'"')#重复 wire
        线路们.add(线路)#记下
        if 参数.get('source')=='lookup':#lookup 源
            查找数+=1#累计
            要求字符串(包名,参数,'lookup','invocation "'+标识+'" lookup parameter')#lookup
        elif 参数.get('source')=='json':#json 源
            if 参数.get('lookup') is not None:#json 不得带 lookup
                raise Exception('typert-loader: '+包名+' invocation "'+标识+'" JSON parameter declares a lookup')#互斥
        else:#未知 source
            raise Exception('typert-loader: '+包名+' invocation "'+标识+'" parameter source must be "json" or "lookup"')#非法
        参数表[线路]=参数#按 wire 记下
        要求严格编解码(包名,参数.get('codec'),'invocation "'+标识+'" parameter codec')#参数 codec
    if 调用.get('cancellation') is not None:#可选取消约定
        取消=要求对象(包名,调用.get('cancellation'),'invocation "'+标识+'" cancellation')#取消必须是对象
        if 取消.get('parameter')!='signal':#必须是 signal
            raise Exception('typert-loader: '+包名+' invocation "'+标识+'" cancellation parameter must be "signal"')#非法
    if 调用.get('scope') is not None:#可选直接作用域投影
        if 接收方.get('kind')!='direct':#Context 接收方不得声明
            raise Exception('typert-loader: '+包名+' invocation "'+标识+'" Context receiver cannot declare a direct scope projection')#互斥
        作用域=要求对象(包名,调用.get('scope'),'invocation "'+标识+'" scope')#scope 必须是对象
        要求字符串(包名,作用域,'context','invocation "'+标识+'" scope')#context
        要求字符串(包名,作用域,'wire','invocation "'+标识+'" scope')#wire
        参数=参数表.get(作用域['wire'])#scope.wire 对应参数
        if 查找数!=1 or 取字段(参数,'source')!='lookup' or 取字段(参数,'lookup')!=作用域['context']:#必须选中唯一 lookup
            raise Exception('typert-loader: '+包名+' invocation "'+标识+'" scope wire "'+作用域['wire']+'" must select its only lookup parameter')#未对准
    if 接收方.get('kind')=='context' and 接收方.get('wire') in 线路们:#Context wire 不得与参数撞名
        raise Exception('typert-loader: '+包名+' invocation "'+标识+'" repeats Context wire field "'+接收方['wire']+'"')#重复
    要求严格编解码(包名,调用.get('result'),'invocation "'+标识+'" result codec')#结果 codec
    if 调用.get('sourceLocation') is not None:#可选源位置
        位置=要求对象(包名,调用.get('sourceLocation'),'invocation "'+标识+'" sourceLocation')#位置必须是对象
        要求字符串(包名,位置,'file','invocation "'+标识+'" sourceLocation')#file
        for 键 in ('line','column'):#行号与列号
            数=位置.get(键)#取出
            if not isinstance(数,int) or isinstance(数,bool) or 数<1:#必须是正整数
                raise Exception('typert-loader: '+包名+' invocation "'+标识+'" sourceLocation.'+键+' must be a positive integer')#非正整数

def 校验Typert清单(包名,导出):#校验 TYPERT 清单
    """把动态导入的 typert 模块的 TYPERT 导出收窄成由包名拥有的贡献。"""
    if not isinstance(导出,dict) or 导出 is None:#不是清单对象
        raise Exception('typert-loader: '+包名+' exports "'+宿主导出键+'" but its module has no TYPERT manifest object')#缺少
    if 导出.get('package')!=包名:#package 字段必须等于导出它的包
        raise Exception('typert-loader: '+包名+' TYPERT manifest names package '+json.dumps(导出.get('package'))+' — the manifest must be owned by the package that exports it')#不符
    if 导出.get('face')!='host':#宿主面才由本 loader 注册
        raise Exception('typert-loader: '+包名+' exports "'+宿主导出键+'" but TYPERT.face is not "host"')#face 不是 host
    if not isinstance(导出.get('schemas'),list):#schemas 必须是数组
        raise Exception('typert-loader: '+包名+' TYPERT.schemas must be an array')#非数组
    for 值 in 导出['schemas']:#逐条校验 schema
        if not isinstance(值,dict) or 值 is None:#条目必须是对象
            raise Exception('typert-loader: '+包名+' TYPERT.schemas contains a non-object schema')#混入非对象
        要求字符串(包名,值,'name','schema')#name
        if not 是否严格模式实例(值.get('schema')):#必须是可 parse 实例
            raise Exception('typert-loader: '+包名+' TYPERT schema "'+str(值.get('name'))+'" is not a zod v4 schema instance')#不是
    模型=要求对象(包名,导出.get('model'),'TYPERT.model')#model 必须是对象
    服务们=要求数组(包名,模型.get('services'),'TYPERT.model.services')#services
    事件们=要求数组(包名,模型.get('events'),'TYPERT.model.events')#events
    对象们=要求数组(包名,模型.get('objects'),'TYPERT.model.objects')#objects
    for 值 in 服务们:#逐条校验 service
        服务=要求对象(包名,值,'service')#service 必须是对象
        要求文档(包名,服务,'service')#文档
        要求字符串(包名,服务,'key','service')#key
        要求字符串(包名,服务,'exportName','service')#exportName
        要求成员们(包名,服务.get('members'),'service "'+服务['key']+'"')#成员
        要求类型们(包名,服务.get('types'),'service "'+服务['key']+'"')#类型
    for 值 in 事件们:#逐条校验 event
        事件=要求对象(包名,值,'event')#event 必须是对象
        要求文档(包名,事件,'event')#文档
        要求字符串(包名,事件,'name','event')#name
        要求字符串(包名,事件,'signature','event "'+事件['name']+'"')#signature
        if 事件.get('mode') is not None and not isinstance(事件.get('mode'),str):#可选 mode
            raise Exception('typert-loader: '+包名+' event "'+事件['name']+'" mode must be a string')#mode 非字符串
    for 值 in 对象们:#逐条校验 object
        对象=要求对象(包名,值,'object')#object 必须是对象
        要求文档(包名,对象,'object')#文档
        要求字符串(包名,对象,'name','object')#name
        要求字符串(包名,对象,'exportName','object')#exportName
        要求成员们(包名,对象.get('members'),'object "'+对象['name']+'"')#成员
        要求类型们(包名,对象.get('types'),'object "'+对象['name']+'"')#类型
    for 值 in 要求数组(包名,导出.get('invocations'),'TYPERT.invocations'):#逐条校验 invocation
        要求调用(包名,值)#校验一条
    return 导出#通过校验

validateTypertManifest=校验Typert清单#上游名

def 解析包清单路径(锚点,包名):#从配置树锚点解析 package.json
    """优先 node_modules/<包名>/package.json，其次锚点旁直接包名目录。"""
    候选们=[#解析候选
        os.path.join(锚点,'node_modules',*包名.split('/'),'package.json'),#pnpm/npm 布局
        os.path.join(锚点,包名,'package.json'),#工作区直接目录
    ]#候选结束
    for 路径 in 候选们:#逐个试
        if os.path.isfile(路径):#命中
            return 路径#绝对路径
    raise FileNotFoundError(包名+'/package.json')#解析失败

def 产物改为Python(路径):#迁移约定：js 产物对应同名 py
    """把 lib/typert.host.js 收成同目录 .py，便于 Python 面导入。"""
    if 路径.endswith('.js'):#原版 js 产物
        return 路径[:-3]+'.py'#并行 py
    return 路径#已是 py 或其他

def 导入产物模块(包名,路径):#按文件路径动态导入并取 TYPERT
    """从产物文件加载模块，读 TYPERT 导出。"""
    实际=产物改为Python(路径)#迁移面产物
    if not os.path.isfile(实际):#产物不存在
        raise Exception('typert-loader: '+包名+' exports "'+宿主导出键+'" but importing '+路径+' failed: missing '+实际)#导入失败
    规格=importlib.util.spec_from_file_location(包名.replace('/','.')+'.typert_host',实际)#按路径建规格
    if 规格 is None or 规格.loader is None:#无法建规格
        raise Exception('typert-loader: '+包名+' exports "'+宿主导出键+'" but importing '+实际+' failed: no loader')#失败
    模块=importlib.util.module_from_spec(规格)#建模块
    规格.loader.exec_module(模块)#执行
    return 校验Typert清单(包名,getattr(模块,'TYPERT',None))#校验 TYPERT

def 应用(上下文,配置=None):#插件入口
    """激活时扫描当前 Loader 条目，随后跟随条目挂载与卸载。"""
    if 配置 is None:#缺省
        配置={'packages':[]}#只做 Loader 条目发现
    显式包=list(配置.get('packages') or [])#显式包名列表
    锚点=getattr(上下文,'baseUrl',None)#配置树锚点
    if 锚点 is None:#没有配置树锚点就无法解析插件包
        raise Exception('typert-loader: ctx.baseUrl is unset — the loader needs the config-tree anchor to resolve plugin packages')#缺少 baseUrl
    已配置=set(显式包)#显式包名集合
    已登记={}#条目名 → 注销函数
    进行中={}#条目名 → 飞行中任务
    产物路径={}#包名 → 产物路径或 None
    清单缓存={}#包名 → 已导入清单
    脏=set()#待调和的条目名
    已排队=False#是否已排队一次微任务 flush
    存活=True#插件仍活着

    def 停扫():#卸载时停扫
        """不再 flush，丢掉未处理脏名。"""
        nonlocal 存活#改旗
        存活=False#不再 flush
        脏.clear()#丢掉未处理脏名

    上下文.effect(lambda:停扫,'typert loader lifetime')#生命周期

    def 解析产物(包名):#解析包的 ./typert 产物路径
        """命中缓存则不再碰盘；否定判定缓存为 None 且永不失效。"""
        if 包名 in 产物路径:#命中缓存
            return 产物路径[包名]#含否定判定 None
        try:#解析 package.json
            清单路径=解析包清单路径(锚点,包名)#从配置树解析该包
        except Exception as 原因:#解析失败
            if 包名 in 已配置:#显式配置的包必须能解析
                raise Exception('typert-loader: configured package "'+包名+'" cannot be resolved from the config tree — add it to the composition package dependencies or remove it from packages') from 原因#配置树解析不到
            产物路径[包名]=None#缓存否定判定
            return None#跳过
        with open(清单路径,'r',encoding='utf-8') as 文件:#读 package.json
            包=json.load(文件)#解析
        相对=取Typert导出(包名,包.get('exports'))#取出 ./typert 相对路径
        if 相对 is None and 包名 in 已配置:#显式包必须导出 ./typert
            raise Exception('typert-loader: configured package "'+包名+'" does not export "'+宿主导出键+'"')#缺导出
        决议=None if 相对 is None else os.path.join(os.path.dirname(清单路径),相对)#没有导出则否定
        产物路径[包名]=决议#写入缓存
        return 决议#产物路径或 None

    def 加载清单(包名,路径):#导入并校验清单
        """同包复用同一次导入。"""
        if 包名 in 清单缓存:#已导入
            return 清单缓存[包名]#缓存
        try:#导入产物
            清单=导入产物模块(包名,路径)#动态导入并校验
        except Exception as 原因:#导入失败
            raise Exception('typert-loader: '+包名+' exports "'+宿主导出键+'" but importing '+路径+' failed: '+str(原因)) from 原因#包成带包名的错
        清单缓存[包名]=清单#按包缓存
        return 清单#清单

    def 够格(条目名):#该条目名现在是否应注册
        """显式包始终够格；否则对照活着的 loader 条目。"""
        if 条目名 in 已配置:#显式包
            return True#够格
        for 条目 in 上下文.loader.entries():#对照活着的 loader 条目
            if 取字段(取字段(条目,'options'),'name')==条目名 and 取字段(条目,'fiber') is not None and not 取字段(条目,'disabled'):#已挂载且未禁用
                return True#够格
        return False#不够格

    def 处理一条(条目名):#调和一条
        """对照活着的 loader 条目调和一个条目名；挂载则返回其异步任务结果。"""
        if not 够格(条目名):#不再够格则撤回
            拆除=已登记.pop(条目名,None)#已登记的 disposer
            if 拆除 is not None:#确实登记过
                return 解开(拆除())#撤回注册
            return None#本来就没登记
        if 条目名 in 已登记 or 条目名 in 进行中:#已登记或飞行中
            return None#不再开任务
        路径=解析产物(条目名)#解析产物
        if 路径 is None:#不是 typert 贡献方
            return None#跳过
        def 任务():#导入完成后注册
            """导入飞行期间条目可能已卸载。"""
            清单=加载清单(条目名,路径)#导入
            if not 存活 or not 够格(条目名) or 条目名 in 已登记:#过期则放弃
                return#放弃
            已登记[条目名]=上下文.typert.register(清单)#登记并记下 disposer
        锚=已兑现(None)#飞行中任务锚点
        承诺=锚.then(lambda _=None:任务())#then 臂执行注册
        进行中[条目名]=承诺#记下飞行中任务
        def 结算(_=None):#从 pending 删掉
            """成功失败都结算。"""
            进行中.pop(条目名,None)#删掉
        承诺.then(结算,结算)#两臂结算
        return 承诺#交给 flush 等待

    def 刷新(遇错):#调和当前脏集合
        """同步失败也要按包隔离；返回本轮异步任务列表。"""
        任务们=[]#本轮异步任务
        for 条目名 in list(脏):#拷贝后删
            脏.discard(条目名)#先出脏集合
            try:#同步失败也要按包隔离
                任务=处理一条(条目名)#调和这一条
                if 任务 is not None:#有异步
                    def 捕(错误,遇=遇错):#异步失败交给 onError
                        """转成 Error 再报告。"""
                        遇(收成错误(错误))#报告
                    任务们.append(任务.then(lambda _=None:None,捕) if hasattr(任务,'then') else 任务)#挂臂
            except Exception as 错误:#同步失败
                遇错(收成错误(错误))#同步失败交给 onError
        return 任务们#本轮异步任务

    def 标脏(光纤):#条目挂载/卸载都走这里
        """无条目的 fiber 是子插件或手动挂载——丢掉。"""
        nonlocal 已排队#改旗
        条目=取字段(光纤,'entry')#fiber 上的条目
        选项=取字段(条目,'options') if 条目 is not None else None#options
        条目名=取字段(选项,'name') if 选项 is not None else None#条目名
        if 条目名 is None:#无条目：子插件或手动挂载
            return#丢掉
        脏.add(条目名)#标脏
        if 已排队:#已排队则不再排
            return#幂等
        已排队=True#本轮只排一次微任务
        def 微任务(_=None):#微任务里调和脏名
            """稳态：失败记日志。"""
            nonlocal 已排队#改旗
            已排队=False#允许下一轮再排
            if not 存活:#已卸载
                return#停
            刷新(lambda 错:上下文.logger.error(错))#稳态：失败记日志

        微=已兑现(None)#微任务锚点
        微.then(微任务)#对齐 queueMicrotask：本轮事件后 flush

    上下文.on('internal/plugin',标脏)#条目挂载/卸载

    for 包名 in 已配置:#显式包也标脏
        脏.add(包名)#标脏
    for 条目 in 上下文.loader.entries():#当前全部条目标脏
        脏.add(取字段(取字段(条目,'options'),'name'))#条目标脏
    失败们=[]#激活遍收集失败
    任务们=刷新(lambda 错:失败们.append(错))#等本轮全部任务
    for 任务 in 任务们:#等待异步
        if 是否thenable(任务):#可等待
            try:#等待
                解开(任务)#落定
            except Exception as 错误:#异步失败
                失败们.append(收成错误(错误))#收集
    if len(失败们)>0:#已加载条目里有坏贡献方
        摘要='\n'.join('  - '+str(错) for 错 in 失败们)#各包错误
        raise Exception('typert-loader: '+str(len(失败们))+' typert contributor(s) failed to register:\n'+摘要)#聚合成一次大声失败

apply=应用#上游名
