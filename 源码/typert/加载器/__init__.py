import json,os,importlib.util,threading#读清单、拼路径、动态导入与后台链
from concurrent.futures import Future as 原生结果#单次操作结果

class 加载器错误(Exception):
    """Typert 加载器配置或清单失败。"""

class 操作任务:
    """单次异步结果。"""
    def __init__(自身):
        """构造未决任务。"""
        自身.底层=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身.底层.done():#尚未结算
            自身.底层.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身.底层.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身.底层.set_exception(错误)#原样拒绝
            else:#非异常
                自身.底层.set_exception(加载器错误(错误))#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等待。"""
        return 自身.底层.result(timeout=超时)#取结果或抛错

__all__=[#仅中文公开名
    '宿主导出键','名称','注入','配置','校验Typert清单','应用',
]#公开面结束

宿主导出键='./typert'#package.json exports 里命名宿主面 typert 产物的键
成员种类=frozenset(['property','method','getter','setter','call','construct','index'])#合法成员 kind

def 收成错误(错误):
    """已是异常则原样，否则包一层加载器错误。"""
    return 错误 if isinstance(错误,BaseException) else 加载器错误(str(错误))#规范化

def 取Typert导出(包名,导出面):#读 package.json exports["./typert"]
    """把 ./typert 导出收成相对路径，接受字符串和一层条件形式。"""
    if not isinstance(导出面,dict) or 导出面 is None:#没有 exports 面
        return None#未声明
    if 宿主导出键 not in 导出面:#未声明该导出
        return None#跳过
    目标=导出面[宿主导出键]#取出 ./typert 目标
    if isinstance(目标,str):#字符串形式
        return 目标#直接用
    if isinstance(目标,dict) and 'default' in 目标:#一层条件对象
        回退=目标['default']#取 default 条件
        if isinstance(回退,str):#default 是字符串
            return 回退#用
    raise 加载器错误('typert-loader: '+包名+' exports["'+宿主导出键+'"] must be a string or an object with a string default')#非法导出形

def 要求对象(包名,值,主语):#要求普通对象
    """数组/null/非对象都不算。"""
    if not isinstance(值,dict) or 值 is None:#非法
        raise 加载器错误('typert-loader: '+包名+' '+主语+' must be an object')#不是对象
    return 值#收成字典

def 要求数组(包名,值,主语):#要求数组
    """不是数组则抛。"""
    if not isinstance(值,list):#非法
        raise 加载器错误('typert-loader: '+包名+' '+主语+' must be an array')#不是数组
    return 值#原样

def 要求字符串(包名,值,键,主语):#要求非空字符串字段
    """缺席、非字符串或空串则失败。"""
    字段=值[键] if 键 in 值 else None#取出
    if not isinstance(字段,str) or len(字段)==0:#缺或空
        raise 加载器错误('typert-loader: '+包名+' '+主语+' has a missing or empty '+键)#缺或空

def 要求文档(包名,值,主语):#要求文档字段形态
    """tags 必须是数组；可选字符串文档字段出现则必须是字符串。"""
    要求数组(包名,值['tags'] if 'tags' in 值 else None,主语+'.tags')#tags
    for 键 in ('description','summary','jsDoc'):#可选字符串文档字段
        if 键 in 值 and 值[键] is not None and not isinstance(值[键],str):#出现则必须是字符串
            raise 加载器错误('typert-loader: '+包名+' '+主语+'.'+键+' must be a string')#非字符串

def 要求成员列表(包名,值,主语):#要求成员列表
    """逐条校验 name/signature/kind。"""
    for 项 in 要求数组(包名,值,主语+'.members'):#逐条成员
        成员=要求对象(包名,项,主语+' member')#成员必须是对象
        要求字符串(包名,成员,'name',主语+' member')#name
        要求字符串(包名,成员,'signature',主语+' member')#signature
        种类=成员.get('kind')#kind
        if not isinstance(种类,str) or 种类 not in 成员种类:#非法 kind
            raise 加载器错误('typert-loader: '+包名+' '+主语+' member "'+str(成员.get('name'))+'" has invalid kind')#非法

def 要求类型列表(包名,值,主语):#要求类型列表
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
        raise 加载器错误('typert-loader: '+包名+' '+主语+' must use a strict codec')#不是 strict
    要求字符串(包名,编解码,'typeSymbol',主语)#typeSymbol
    if not 是否严格模式实例(编解码.get('schema')):#不是可 parse 实例
        raise 加载器错误('typert-loader: '+包名+' '+主语+' is not backed by a zod v4 schema')#不是模式实例

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
        raise 加载器错误('typert-loader: '+包名+' invocation "'+标识+'" receiver kind must be "direct" or "context"')#非法 kind
    线路集合=set()#已出现的 wire
    参数表={}#按 wire 索引参数
    查找数=0#lookup 源参数个数
    for 参数值 in 要求数组(包名,调用.get('parameters'),'invocation "'+标识+'" parameters'):#逐个参数
        参数=要求对象(包名,参数值,'invocation "'+标识+'" parameter')#参数必须是对象
        要求字符串(包名,参数,'name','invocation "'+标识+'" parameter')#name
        要求字符串(包名,参数,'wire','invocation "'+标识+'" parameter')#wire
        线路=参数['wire']#本参数 wire
        if 线路 in 线路集合:#重复
            raise 加载器错误('typert-loader: '+包名+' invocation "'+标识+'" repeats wire field "'+线路+'"')#重复 wire
        线路集合.add(线路)#记下
        if 参数.get('source')=='lookup':#lookup 源
            查找数+=1#累计
            要求字符串(包名,参数,'lookup','invocation "'+标识+'" lookup parameter')#lookup
        elif 参数.get('source')=='json':#json 源
            if 参数.get('lookup') is not None:#json 不得带 lookup
                raise 加载器错误('typert-loader: '+包名+' invocation "'+标识+'" JSON parameter declares a lookup')#互斥
        else:#未知 source
            raise 加载器错误('typert-loader: '+包名+' invocation "'+标识+'" parameter source must be "json" or "lookup"')#非法
        参数表[线路]=参数#按 wire 记下
        要求严格编解码(包名,参数.get('codec'),'invocation "'+标识+'" parameter codec')#参数 codec
    if 调用.get('cancellation') is not None:#可选取消约定
        取消=要求对象(包名,调用.get('cancellation'),'invocation "'+标识+'" cancellation')#取消必须是对象
        if 取消.get('parameter')!='signal':#必须是 signal
            raise 加载器错误('typert-loader: '+包名+' invocation "'+标识+'" cancellation parameter must be "signal"')#非法
    if 调用.get('scope') is not None:#可选直接作用域投影
        if 接收方.get('kind')!='direct':#Context 接收方不得声明
            raise 加载器错误('typert-loader: '+包名+' invocation "'+标识+'" Context receiver cannot declare a direct scope projection')#互斥
        作用域=要求对象(包名,调用.get('scope'),'invocation "'+标识+'" scope')#scope 必须是对象
        要求字符串(包名,作用域,'context','invocation "'+标识+'" scope')#context
        要求字符串(包名,作用域,'wire','invocation "'+标识+'" scope')#wire
        参数=参数表[作用域['wire']] if 作用域['wire'] in 参数表 else None#scope.wire 对应参数
        if 查找数!=1 or 参数 is None or ('source' not in 参数) or 参数['source']!='lookup' or ('lookup' not in 参数) or 参数['lookup']!=作用域['context']:#必须选中唯一 lookup
            raise 加载器错误('typert-loader: '+包名+' invocation "'+标识+'" scope wire "'+作用域['wire']+'" must select its only lookup parameter')#未对准
    if 接收方.get('kind')=='context' and 接收方.get('wire') in 线路集合:#Context wire 不得与参数撞名
        raise 加载器错误('typert-loader: '+包名+' invocation "'+标识+'" repeats Context wire field "'+接收方['wire']+'"')#重复
    要求严格编解码(包名,调用.get('result'),'invocation "'+标识+'" result codec')#结果 codec
    if 调用.get('sourceLocation') is not None:#可选源位置
        位置=要求对象(包名,调用.get('sourceLocation'),'invocation "'+标识+'" sourceLocation')#位置必须是对象
        要求字符串(包名,位置,'file','invocation "'+标识+'" sourceLocation')#file
        for 键 in ('line','column'):#行号与列号
            数=位置.get(键)#取出
            if not isinstance(数,int) or isinstance(数,bool) or 数<1:#必须是正整数
                raise 加载器错误('typert-loader: '+包名+' invocation "'+标识+'" sourceLocation.'+键+' must be a positive integer')#非正整数

def 校验Typert清单(包名,导出):#校验 TYPERT 清单
    """把动态导入的 typert 模块的 TYPERT 导出收窄成由包名拥有的贡献。"""
    if not isinstance(导出,dict) or 导出 is None:#不是清单对象
        raise 加载器错误('typert-loader: '+包名+' exports "'+宿主导出键+'" but its module has no TYPERT manifest object')#缺少
    if 导出.get('package')!=包名:#package 字段必须等于导出它的包
        raise 加载器错误('typert-loader: '+包名+' TYPERT manifest names package '+json.dumps(导出['package'] if 'package' in 导出 else None,ensure_ascii=False,separators=(',',':'),allow_nan=False)+' — the manifest must be owned by the package that exports it')#不符
    if 导出.get('face')!='host':#宿主面才由本 loader 注册
        raise 加载器错误('typert-loader: '+包名+' exports "'+宿主导出键+'" but TYPERT.face is not "host"')#face 不是 host
    if not isinstance(导出.get('schemas'),list):#schemas 必须是数组
        raise 加载器错误('typert-loader: '+包名+' TYPERT.schemas must be an array')#非数组
    for 值 in 导出['schemas']:#逐条校验 schema
        if not isinstance(值,dict) or 值 is None:#条目必须是对象
            raise 加载器错误('typert-loader: '+包名+' TYPERT.schemas contains a non-object schema')#混入非对象
        要求字符串(包名,值,'name','schema')#name
        if not 是否严格模式实例(值.get('schema')):#必须是可 parse 实例
            raise 加载器错误('typert-loader: '+包名+' TYPERT schema "'+str(值.get('name'))+'" is not a zod v4 schema instance')#不是
    模型=要求对象(包名,导出.get('model'),'TYPERT.model')#model 必须是对象
    服务列表=要求数组(包名,模型.get('services'),'TYPERT.model.services')#services
    事件列表=要求数组(包名,模型.get('events'),'TYPERT.model.events')#events
    对象列表=要求数组(包名,模型.get('objects'),'TYPERT.model.objects')#objects
    for 值 in 服务列表:#逐条校验 service
        服务=要求对象(包名,值,'service')#service 必须是对象
        要求文档(包名,服务,'service')#文档
        要求字符串(包名,服务,'key','service')#key
        要求字符串(包名,服务,'exportName','service')#exportName
        要求成员列表(包名,服务.get('members'),'service "'+服务['key']+'"')#成员
        要求类型列表(包名,服务.get('types'),'service "'+服务['key']+'"')#类型
    for 值 in 事件列表:#逐条校验 event
        事件=要求对象(包名,值,'event')#event 必须是对象
        要求文档(包名,事件,'event')#文档
        要求字符串(包名,事件,'name','event')#name
        要求字符串(包名,事件,'signature','event "'+事件['name']+'"')#signature
        if 事件.get('mode') is not None and not isinstance(事件.get('mode'),str):#可选 mode
            raise 加载器错误('typert-loader: '+包名+' event "'+事件['name']+'" mode must be a string')#mode 非字符串
    for 值 in 对象列表:#逐条校验 object
        对象=要求对象(包名,值,'object')#object 必须是对象
        要求文档(包名,对象,'object')#文档
        要求字符串(包名,对象,'name','object')#name
        要求字符串(包名,对象,'exportName','object')#exportName
        要求成员列表(包名,对象.get('members'),'object "'+对象['name']+'"')#成员
        要求类型列表(包名,对象.get('types'),'object "'+对象['name']+'"')#类型
    for 值 in 要求数组(包名,导出.get('invocations'),'TYPERT.invocations'):#逐条校验 invocation
        要求调用(包名,值)#校验一条
    return 导出#通过校验

def 解析包清单路径(锚点,包名):#从配置树锚点解析 package.json
    """优先 node_modules/<包名>/package.json，其次锚点旁直接包名目录。"""
    候选列表=[#解析候选
        os.path.join(锚点,'node_modules',*包名.split('/'),'package.json'),#pnpm/npm 布局
        os.path.join(锚点,包名,'package.json'),#工作区直接目录
    ]#候选结束
    for 路径 in 候选列表:#逐个试
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
        raise 加载器错误('typert-loader: '+包名+' exports "'+宿主导出键+'" but importing '+路径+' failed: missing '+实际)#导入失败
    规格=importlib.util.spec_from_file_location(包名.replace('/','.')+'.typert_host',实际)#按路径建规格
    if 规格 is None or 规格.loader is None:#无法建规格
        raise 加载器错误('typert-loader: '+包名+' exports "'+宿主导出键+'" but importing '+实际+' failed: no loader')#失败
    模块=importlib.util.module_from_spec(规格)#建模块
    规格.loader.exec_module(模块)#执行
    return 校验Typert清单(包名,getattr(模块,'TYPERT',None))#校验 TYPERT

def 应用(上下文,配置=None):
    """激活时扫描当前 Loader 条目，随后跟随条目挂载与卸载。"""
    if 配置 is None:#缺省
        配置={'packages':[]}#只做 Loader 条目发现
    if 'packages' not in 配置 or 配置['packages'] is None:#省略包列表
        显式包=[]#空
    else:#有列表
        显式包=list(配置['packages'])#显式包名列表
    锚点=上下文.基准网址#配置树锚点
    if 锚点 is None:#没有配置树锚点就无法解析插件包
        raise 加载器错误('typert-loader: ctx.baseUrl is unset — the loader needs the config-tree anchor to resolve plugin packages')#缺少 baseUrl
    已配置=set(显式包)#显式包名集合
    已登记={}#条目名 → 注销函数
    进行中={}#条目名 → 飞行中任务
    产物路径={}#包名 → 产物路径或 None
    清单缓存={}#包名 → 已导入清单
    脏=set()#待调和的条目名
    已排队=False#是否已排队一次微任务 flush
    存活=True#插件仍活着

    def 停扫():
        """不再 flush，丢掉未处理脏名。"""
        nonlocal 存活#改旗
        存活=False#不再 flush
        脏.clear()#丢掉未处理脏名

    def 寿命():
        """登记卸载时停扫。"""
        return 停扫#拆除器

    上下文.副作用(寿命,'typert loader lifetime')#生命周期

    def 解析产物(包名):
        """命中缓存则不再碰盘；否定判定缓存为 None 且永不失效。"""
        if 包名 in 产物路径:#命中缓存
            return 产物路径[包名]#含否定判定 None
        try:#解析 package.json
            清单路径=解析包清单路径(锚点,包名)#从配置树解析该包
        except FileNotFoundError as 原因:#解析失败
            if 包名 in 已配置:#显式配置的包必须能解析
                raise 加载器错误('typert-loader: configured package "'+包名+'" cannot be resolved from the config tree — add it to the composition package dependencies or remove it from packages') from 原因#配置树解析不到
            产物路径[包名]=None#缓存否定判定
            return None#跳过
        with open(清单路径,'r',encoding='utf-8') as 文件:#读 package.json
            包=json.load(文件)#解析
        导出面=包['exports'] if 'exports' in 包 else None#exports
        相对=取Typert导出(包名,导出面)#取出 ./typert 相对路径
        if 相对 is None and 包名 in 已配置:#显式包必须导出 ./typert
            raise 加载器错误('typert-loader: configured package "'+包名+'" does not export "'+宿主导出键+'"')#缺导出
        决议=None if 相对 is None else os.path.join(os.path.dirname(清单路径),相对)#没有导出则否定
        产物路径[包名]=决议#写入缓存
        return 决议#产物路径或 None

    def 加载清单(包名,路径):
        """同包复用同一次导入。"""
        if 包名 in 清单缓存:#已导入
            return 清单缓存[包名]#缓存
        try:#导入产物
            清单=导入产物模块(包名,路径)#动态导入并校验
        except Exception as 原因:#导入失败形态未钉死
            raise 加载器错误('typert-loader: '+包名+' exports "'+宿主导出键+'" but importing '+路径+' failed: '+str(原因)) from 原因#包成带包名的错
        清单缓存[包名]=清单#按包缓存
        return 清单#清单

    def 够格(条目名):
        """显式包始终够格；否则对照活着的 loader 条目。"""
        if 条目名 in 已配置:#显式包
            return True#够格
        for 条目 in 上下文.加载器.列出插件配置():#对照活着的 loader 条目
            选项=条目.选项#选项 dict
            if 'name' not in 选项:#无名
                continue#下一条
            if 选项['name']==条目名 and 条目.纤程 is not None and not 条目.已禁用:#已挂载且未禁用
                return True#够格
        return False#不够格

    def 处理一条(条目名):
        """对照活着的 loader 条目调和一个条目名；挂载则返回其任务。"""
        if not 够格(条目名):#不再够格则撤回
            拆除=已登记.pop(条目名,None)#已登记的拆除器
            if 拆除 is not None:#确实登记过
                拆除()#撤回注册，同步
            return None#撤回无飞行任务
        if 条目名 in 已登记 or 条目名 in 进行中:#已登记或飞行中
            return None#不再开任务
        路径=解析产物(条目名)#解析产物
        if 路径 is None:#不是 typert 贡献方
            return None#跳过
        def 任务():
            """导入飞行期间条目可能已卸载。"""
            清单=加载清单(条目名,路径)#导入
            if not 存活 or not 够格(条目名) or 条目名 in 已登记:#过期则放弃
                return#放弃
            已登记[条目名]=上下文.typert.register(清单)#登记并记下拆除器
        承诺=操作任务()#飞行中任务
        def 执行注册():
            """成功失败都从 pending 删掉。"""
            try:#执行任务体
                任务()#导入并登记
                承诺.兑现(None)#成功
            except Exception as 错误:#失败
                承诺.拒绝(错误)#上抛
            finally:#无论成败
                进行中.pop(条目名,None)#删掉
        threading.Thread(target=执行注册,daemon=True).start()#启动
        进行中[条目名]=承诺#记下飞行中任务
        return 承诺#交给 flush 等待

    def 刷新(遇错):
        """同步失败也要按包隔离；返回本轮任务列表。"""
        任务列表=[]#本轮任务
        for 条目名 in list(脏):#拷贝后删
            脏.discard(条目名)#先出脏集合
            try:#同步失败也要按包隔离
                任务=处理一条(条目名)#调和这一条
                if 任务 is not None:#有飞行任务
                    def 观察(当次=任务):
                        """等任务落定，失败交给遇错。"""
                        try:#等待
                            当次.等待()#落定
                        except Exception as 错误:#任务拒绝
                            遇错(收成错误(错误))#报告
                    threading.Thread(target=观察,daemon=True).start()#挂观察
                    任务列表.append(任务)#挂臂
            except 加载器错误 as 错误:#同步失败
                遇错(收成错误(错误))#同步失败交给 onError
        return 任务列表#本轮任务

    def 标脏(光纤):
        """无插件配置的 fiber 是子插件或手动挂载——丢掉。"""
        nonlocal 已排队#改旗
        条目=光纤.插件配置#fiber 上的插件配置
        if 条目 is None:#无条目
            return#丢掉
        选项=条目.选项#选项 dict
        if 'name' not in 选项:#无名
            return#丢掉
        条目名=选项['name']#条目名
        脏.add(条目名)#标脏
        if 已排队:#已排队则不再排
            return#幂等
        已排队=True#本轮只排一次微任务
        def 记日志(错):
            """稳态失败记日志。"""
            上下文.日志.错误(错)#记日志
        def 微任务():
            """微任务里调和脏名。"""
            nonlocal 已排队#改旗
            已排队=False#允许下一轮再排
            if not 存活:#已卸载
                return#停
            刷新(记日志)#稳态：失败记日志
        threading.Thread(target=微任务,daemon=True).start()#对齐 queueMicrotask：本轮事件后 flush

    上下文.监听('internal/plugin',标脏)#条目挂载/卸载

    for 包名 in 已配置:#显式包也标脏
        脏.add(包名)#标脏
    for 条目 in 上下文.加载器.列出插件配置():#当前全部条目标脏
        选项=条目.选项#选项 dict
        if 'name' in 选项:#有名
            脏.add(选项['name'])#条目标脏
    失败列表=[]#激活遍收集失败
    def 收集失败(错):
        """激活遍收集失败。"""
        失败列表.append(错)#记下
    任务列表=刷新(收集失败)#等本轮全部任务
    for 任务 in 任务列表:#等待任务
        try:#等待
            任务.等待()#落定
        except Exception as 错误:#异步失败
            失败列表.append(收成错误(错误))#收集
    if len(失败列表)>0:#已加载条目里有坏贡献方
        摘要='\n'.join('  - '+str(错) for 错 in 失败列表)#各包错误
        raise 加载器错误('typert-loader: '+str(len(失败列表))+' typert contributor(s) failed to register:\n'+摘要)#聚合成一次大声失败

名称='typert-loader'#Cordis 插件名
注入=['typert','loader']#依赖 typert 与 loader
配置={'packages':[]}#缺省只做 Loader 条目发现；packages 为显式包名列表
name=名称#框架槽
inject=注入#框架槽
Config=配置#框架槽
apply=应用#框架槽
