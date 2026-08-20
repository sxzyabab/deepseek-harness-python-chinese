"""上下文、服务与插件光纤共用的内部辅助。"""
import threading,traceback,weakref

_符号表={}#全局符号登记表

def 全局符号(名称):
    """按名取出或创建一份进程内唯一标记。"""
    if 名称 not in _符号表:
        _符号表[名称]=object()#新建标记
    return _符号表[名称]#返回标记

class 原型映射:
    """以父表为原型的映射，模拟 Object.create。"""
    def __init__(自身,原型=None):
        """空表或挂到父表上。"""
        自身._自有={}#本层自有键
        自身._原型=原型#父表

    def __getitem__(自身,键):
        """沿原型链取值，没有则为 None。"""
        if 键 in 自身._自有:
            return 自身._自有[键]#自有
        if 自身._原型 is not None:
            return 自身._原型[键]#上溯
        return None#相当于 undefined

    def __setitem__(自身,键,值):
        """写入本层自有键。"""
        自身._自有[键]=值#自有写入

    def __contains__(自身,键):
        """沿原型链询问键是否存在。"""
        if 键 in 自身._自有:
            return True#自有
        if 自身._原型 is not None:
            return 键 in 自身._原型#上溯
        return False#没有

    def get(自身,键,默认=None):
        """取值，没有则默认。"""
        值=自身[键]#沿链
        if 值 is None and 键 not in 自身:
            return 默认#缺失
        return 值#命中或显式空

    def keys(自身):
        """只交出本层自有键。"""
        return 自身._自有.keys()#自有键

    def 有自有(自身,键):
        """本层是否有该键。"""
        return 键 in 自身._自有#自有

    def 取原型(自身):
        """返回父表。"""
        return 自身._原型#父表

    def __iter__(自身):
        """按自有键迭代。"""
        return iter(自身._自有)#自有

class 可释放列表:
    """可按值 O(1) 删除的有序可释放值集合。"""
    def __init__(自身):
        """初始化空表。"""
        自身._序号=0#单调递增序号
        自身._映射={}#序号到值
        自身._弱表=weakref.WeakKeyDictionary()#值到序号

    @property
    def 长度(自身):
        """当前仍登记的条目数。"""
        return len(自身._映射)#条目数

    @property
    def length(自身):
        """当前仍登记的条目数。"""
        return 自身.长度#英文别名

    def 压入(自身,值):
        """按插入顺序登记，并返回按序号删除的释放器。"""
        自身._序号+=1#下一个序号
        序号=自身._序号#本条序号
        自身._映射[序号]=值#按序号存入
        自身._弱表[值]=序号#记录弱映射
        def 删除本条():
            """只删本序号。"""
            return 自身._映射.pop(序号,None) is not None#是否删掉
        return 删除本条#释放器

    def push(自身,值):
        """按插入顺序登记。"""
        return 自身.压入(值)#英文别名

    def 前插(自身,值):
        """插到表头并返回按序号删除的释放器。"""
        自身._序号+=1#下一个序号
        序号=自身._序号#本条序号
        新表={}#重建以改顺序
        新表[序号]=值#新项在前
        新表.update(自身._映射)#其余后附
        自身._映射=新表#换表
        自身._弱表[值]=序号#记录弱映射
        def 删除本条():
            """只删本序号。"""
            return 自身._映射.pop(序号,None) is not None#是否删掉
        return 删除本条#释放器

    unshift=前插#英文别名

    def 删除(自身,值):
        """按值删除。"""
        序号=自身._弱表.get(值)#查出序号
        if not 序号:
            return False#从未登记
        return 自身._映射.pop(序号,None) is not None#按序号删除

    def delete(自身,值):
        """按值删除。"""
        return 自身.删除(值)#英文别名

    def 清空(自身):
        """清空并按逆序交出剩余值。"""
        值列表=list(自身._映射.values())#当前全部值
        自身._映射.clear()#清空序号表
        值列表.reverse()#逆序
        return 值列表#供卸载反向释放

    def clear(自身):
        """清空并按逆序交出剩余值。"""
        return 自身.清空()#英文别名

    def __iter__(自身):
        """按插入顺序迭代当前值。"""
        return iter(自身._映射.values())#插入顺序

    def __repr__(自身):
        """检查器展示为列表快照。"""
        return repr(list(自身))#数组快照

class 符号表:
    """避免与公开属性名冲突的共享符号。"""
    阴影=全局符号('cordis.shadow')#阴影上下文
    接收者=全局符号('cordis.receiver')#代理接收者
    原始=全局符号('cordis.original')#可追踪代理背后的原始目标
    元数据=全局符号('cordis.metadata')#装饰器元数据
    初始化钩子=全局符号('cordis.initHooks')#类插件延迟钩子
    检查原型=全局符号('cordis.checkProto')#inject 沿原型链
    副作用=全局符号('cordis.effect')#副作用诊断树
    过滤=全局符号('cordis.filter')#事件派发过滤器
    隔离=全局符号('cordis.isolate')#服务隔离表
    拦截=全局符号('cordis.intercept')#服务拦截配置表
    初始化=全局符号('cordis.init')#类插件初始化方法
    检查=全局符号('cordis.check')#服务可用性谓词
    配置=全局符号('cordis.config')#拦截配置幽灵类型
    调用=全局符号('cordis.invoke')#可调用服务的调用体
    扩展=全局符号('cordis.extend')#扩展服务实例
    追踪器=全局符号('cordis.tracker')#追踪器元数据
    解析配置=全局符号('cordis.resolveConfig')#合并拦截配置
    是=全局符号('cordis.is')#上下文品牌

符号=符号表#模块级别名
symbols=符号#英文别名

def 设符号(对象,键,值):
    """把符号键写到对象字典上。"""
    if isinstance(对象,dict):
        对象[键]=值#字典写入
        return 对象#原对象
    对象.__dict__[键]=值#实例字典
    return 对象#原对象

def 取符号(对象,键,默认=None):
    """从对象字典读符号键。"""
    if 对象 is None:
        return 默认#空
    if isinstance(对象,dict):
        return 对象.get(键,默认)#字典
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:
        return 默认#没有字典
    return 字典.get(键,默认)#符号值

def 是否构造器(函数):
    """判断插件回调是否应以类方式构造。"""
    return isinstance(函数,type)#类插件

def 拼接原型(原型一,原型二):
    """合并两条原型链，同时保留原型一上的描述符。"""
    if 原型一 is object:
        return 原型二#接到原型二
    父=拼接原型(原型一.__bases__[0],原型二) if 原型一.__bases__ else 原型二#递归合并
    结果=type('拼接原型',(父,),{})#新类型
    for 键,值 in 原型一.__dict__.items():
        if 键.startswith('__') and 键.endswith('__'):
            continue#跳过槽
        setattr(结果,键,值)#拷贝本层
    return 结果#拼接结果

def 是否对象(值):
    """判断是否为非空对象或函数。"""
    if 值 is None:
        return False#空
    if isinstance(值,bool):
        return False#布尔
    if isinstance(值,(str,bytes,int,float)):
        return False#原始值
    return True#对象或函数

def 取属性描述(目标,属性):
    """沿类型链查找属性。找不到则得到 None。"""
    if isinstance(目标,dict) and 属性 in 目标:
        return 目标[属性]#字典项
    字典=getattr(目标,'__dict__',None)#实例字典
    if 字典 is not None and 属性 in 字典:
        return 字典[属性]#实例自有
    类型=type(目标)#类型
    while 类型 is not None:
        if 属性 in 类型.__dict__:
            return 类型.__dict__[属性]#类型自有
        类型=类型.__base__ if 类型 is not object else None#上溯
    return None#未找到

class 属性覆盖:
    """把覆盖表叠到目标上的读取包装。"""
    def __init__(自身,目标,覆盖表):
        """保存目标与覆盖表。"""
        object.__setattr__(自身,'_目标',目标)#原目标
        object.__setattr__(自身,'_覆盖表',覆盖表)#覆盖表

    def __getattr__(自身,属性):
        """覆盖属性优先从覆盖表读。"""
        覆盖表=object.__getattribute__(自身,'_覆盖表')#覆盖表
        目标=object.__getattribute__(自身,'_目标')#原目标
        if 属性 in 覆盖表 and 属性!='constructor':
            return 覆盖表[属性]#覆盖值
        return getattr(目标,属性)#原目标

    def __setattr__(自身,属性,写入值):
        """覆盖属性写回覆盖表。"""
        if 属性 in ('_目标','_覆盖表'):
            object.__setattr__(自身,属性,写入值)#内部字段
            return
        覆盖表=object.__getattribute__(自身,'_覆盖表')#覆盖表
        目标=object.__getattribute__(自身,'_目标')#原目标
        if 属性 in 覆盖表 and 属性!='constructor':
            覆盖表[属性]=写入值#写覆盖表
            return
        setattr(目标,属性,写入值)#写原目标

    def __call__(自身,*位置参数,**关键字参数):
        """转发给目标。"""
        目标=object.__getattribute__(自身,'_目标')#原目标
        return 目标(*位置参数,**关键字参数)#调用

def 叠属性(目标,覆盖表=None):
    """返回把属性叠到目标上的包装。覆盖表为空则返回原目标。"""
    if not 覆盖表:
        return 目标#不建包装
    return 属性覆盖(目标,覆盖表)#包装

def 叠单属性(目标,属性,值):
    """叠上一条只读覆盖属性。"""
    return 叠属性(目标,{属性:值})#单属性覆盖

def 取可追踪(上下文,值):
    """包装服务或函数，使方法调用看到调用方当前激活的上下文。"""
    if not 是否对象(值):
        return 值#原始值无需包装
    if 取符号(值,符号.阴影) is not None and 符号.阴影 in getattr(值,'__dict__',{}):
        return object.__getattribute__(值,'__dict__').get('_原型上下文',值)#揭开阴影
    追踪器=取符号(值,符号.追踪器)#符号追踪器
    if 追踪器 is None:
        追踪器=getattr(值,'_追踪器',None)#字段追踪器
    if not 追踪器:
        return 值#未声明追踪器
    return 创建可追踪(上下文,值,追踪器)#生成可追踪包装

def 创建阴影(上下文,目标,属性,接收者):
    """把属性重绑到带阴影的子上下文。"""
    if not 属性:
        return 接收者#没有要重绑的属性
    原始=getattr(目标,属性,None)#取出原始值
    if not 原始:
        return 接收者#目标没有该属性
    扩展=上下文.extend({符号.阴影:原始})#带阴影的子上下文
    return 叠单属性(接收者,属性,扩展)#重绑属性

class 阴影方法:
    """以外部包装为 this 时改绑到阴影接收者。"""
    def __init__(自身,上下文,值,外部,阴影):
        """保存调用改绑所需对象。"""
        自身._上下文=上下文#调用方上下文
        自身._值=值#原方法
        自身._外部=外部#外部包装
        自身._阴影=阴影#阴影接收者

    def __call__(自身,*位置参数,**关键字参数):
        """改绑 this 后再把返回值做成可追踪。"""
        return 取可追踪(自身._上下文,自身._值(*位置参数,**关键字参数))#调用并包装

class 可追踪包装:
    """按追踪器重绑 ctx 与关联服务。"""
    def __init__(自身,上下文,值,追踪器):
        """保存追踪状态。"""
        object.__setattr__(自身,'_上下文',上下文)#调用方上下文
        object.__setattr__(自身,'_值',值)#原始目标
        object.__setattr__(自身,'_追踪器',追踪器)#追踪器

    def __getattr__(自身,属性):
        """读取时重绑 ctx 或转发关联属性。"""
        上下文=object.__getattribute__(自身,'_上下文')#调用方
        值=object.__getattribute__(自身,'_值')#目标
        追踪器=object.__getattribute__(自身,'_追踪器')#追踪器
        if 属性==符号.原始:
            return 值#原始目标
        属性名=追踪器.get('property') if isinstance(追踪器,dict) else None#追踪属性名
        if 属性==属性名:
            return 上下文#返回调用方上下文
        关联=追踪器.get('associate') if isinstance(追踪器,dict) else None#关联服务名
        if 关联 and hasattr(上下文,'reflect'):
            键=f'{关联}.{属性}'#关联键
            属性表=getattr(上下文.reflect,'属性表',{})#已声明属性
            if 键 in 属性表:
                return getattr(上下文,键)#转发到上下文
        内层=getattr(值,属性)#从目标读
        内层追踪=取符号(内层,符号.追踪器) if 是否对象(内层) else None#嵌套追踪器
        if 内层追踪:
            return 创建可追踪(上下文,内层,内层追踪)#递归包装
        无阴影=追踪器.get('noShadow') if isinstance(追踪器,dict) else False#是否保留来源
        if not 无阴影 and callable(内层) and not isinstance(内层,type):
            阴影=创建阴影(上下文,值,属性名,自身)#建阴影
            return 阴影方法(上下文,内层,自身,阴影)#阴影方法
        return 内层#原样返回

    def __setattr__(自身,属性,写入值):
        """写入时同样走关联或阴影。"""
        if 属性 in ('_上下文','_值','_追踪器'):
            object.__setattr__(自身,属性,写入值)#内部字段
            return
        上下文=object.__getattribute__(自身,'_上下文')#调用方
        值=object.__getattribute__(自身,'_值')#目标
        追踪器=object.__getattribute__(自身,'_追踪器')#追踪器
        if 属性==符号.原始:
            raise AttributeError('禁止改写原始目标指针')#拒绝
        属性名=追踪器.get('property') if isinstance(追踪器,dict) else None#追踪属性
        if 属性==属性名:
            raise AttributeError('禁止改写追踪属性')#拒绝
        关联=追踪器.get('associate') if isinstance(追踪器,dict) else None#关联服务名
        if 关联 and hasattr(上下文,'reflect'):
            键=f'{关联}.{属性}'#关联键
            属性表=getattr(上下文.reflect,'属性表',{})#已声明属性
            if 键 in 属性表:
                setattr(上下文,键,写入值)#转发写
                return
        创建阴影(上下文,值,属性名,自身)#用阴影接收者写入
        setattr(值,属性,写入值)#写到目标

    def __call__(自身,*位置参数,**关键字参数):
        """作为函数调用时走调用体分发。"""
        值=object.__getattribute__(自身,'_值')#目标
        return 应用可追踪(自身,值,None,位置参数)#分发

    def __repr__(自身):
        """委托原始目标的展示。"""
        值=object.__getattribute__(自身,'_值')#目标
        return repr(值)#原展示

def 创建可追踪(上下文,值,追踪器):
    """按追踪器生成可追踪包装。"""
    无阴影=追踪器.get('noShadow') if isinstance(追踪器,dict) else False#是否保留来源
    字典=getattr(上下文,'__dict__',None)#上下文字典
    if 字典 is not None and 符号.阴影 in 字典 and not 无阴影:
        上下文=字典.get('_原型上下文',上下文)#剥掉阴影
    return 可追踪包装(上下文,值,追踪器)#包装

def 应用可追踪(代理,值,绑定this,参数列表):
    """经调用体或普通调用执行。"""
    调用体=取符号(值,符号.调用)#符号调用体
    if 调用体 is None:
        调用体=getattr(值,'_调用',None)#字段调用体
    if not 调用体:
        return 值(*参数列表)#普通调用
    未绑定=getattr(调用体,'__func__',调用体)#未绑定
    return 未绑定(代理,*参数列表)#绑到可追踪代理

class 可调用服务:
    """通过调用体分发的可调用服务对象。"""
    def __init__(自身,名称,原型,追踪器):
        """保存名称、原型与追踪器。"""
        object.__setattr__(自身,'_名称',名称)#服务名
        object.__setattr__(自身,'_原型',原型)#原型对象
        object.__setattr__(自身,'_追踪器',追踪器)#追踪器
        object.__setattr__(自身,'name',名称)#函数名
        自身.__dict__[符号.追踪器]=追踪器#符号追踪器

    def __call__(自身,*位置参数,**关键字参数):
        """每次调用按当前 ctx 生成可追踪代理。"""
        上下文=getattr(自身,'ctx',None)#当前上下文
        代理=创建可追踪(上下文,自身,object.__getattribute__(自身,'_追踪器'))#可追踪
        return 应用可追踪(代理,自身,None,位置参数)#分发

    def __getattr__(自身,属性):
        """方法查找落到原型。"""
        原型=object.__getattribute__(自身,'_原型')#原型
        return getattr(原型,属性)#委托

    def __setattr__(自身,属性,写入值):
        """字段写到自身字典。"""
        object.__setattr__(自身,属性,写入值)#直接写

def 创建可调用(名称,原型,追踪器):
    """创建通过调用体分发的可调用服务对象。"""
    return 可调用服务(名称,原型,追踪器)#可调用包装

class 栈信息:
    """内层调用位置锚点。"""
    def __init__(自身):
        """记录本层偏移与错误对象。"""
        自身.偏移=1#需要剥掉的内层栈帧偏移
        自身.错误=Exception()#捕获内层位置
        自身.offset=自身.偏移#英文别名
        自身.error=自身.错误#英文别名

def 处理错误(栈信息对象,原因,获取外层栈):
    """把外层调用点栈帧拼进错误。"""
    if not isinstance(原因,BaseException):
        外层=Exception(原因)#包一层
        外层._外层栈=获取外层栈()#外层帧
        raise 外层#抛出
    原因._外层栈=获取外层栈()#挂上外层栈
    raise 原因#抛出改写后的原因

def 拼接错误(回调,获取外层栈=None):
    """运行回调，并把外层调用点栈帧拼进抛出的错误。"""
    if 获取外层栈 is None:
        获取外层栈=构建外层栈()#默认捕获当前栈
    信息=栈信息()#本层锚点
    try:
        结果=回调(信息)#执行被包装的回调
        if 是否对象(结果) and callable(getattr(结果,'then',None)):
            def 拒绝(原因):
                """拒绝时拼接外层栈。"""
                处理错误(信息,原因,获取外层栈)#改栈再抛
            结果.then(None,拒绝)#挂拒绝处理
            return 结果#thenable
        return 结果#同步返回
    except BaseException as 原因:
        处理错误(信息,原因,获取外层栈)#同步抛错改栈

def 构建外层栈(偏移=0):
    """捕获一份惰性栈帧供应器，供稍后拼接错误栈。"""
    外层=traceback.format_stack()#立刻抓当前栈
    def 取出():
        """延迟切出外层帧。"""
        return 外层[0:max(0,len(外层)-(3+偏移))]#跳过本辅助
    return 取出#供应器

class 承诺:
    """可等待的一次性结果，用来代替 Promise。"""
    def __init__(自身):
        """初始化未完成状态。"""
        自身._事件=threading.Event()#完成事件
        自身._结果=None#兑现值
        自身._错误=None#拒绝原因
        自身._已定=False#是否已结算

    def 兑现(自身,值=None):
        """成功结算。"""
        if 自身._已定:
            return#忽略二次结算
        自身._已定=True#标记已定
        自身._结果=值#保存结果
        自身._事件.set()#放行等待方

    def 拒绝(自身,错误):
        """失败结算。"""
        if 自身._已定:
            return#忽略二次结算
        自身._已定=True#标记已定
        自身._错误=错误#保存原因
        自身._事件.set()#放行等待方

    def 等待(自身):
        """阻塞直到结算，失败则抛出。"""
        自身._事件.wait()#等待
        if 自身._错误 is not None:
            raise 自身._错误#失败
        return 自身._结果#成功值

    def then(自身,兑现=None,拒绝=None):
        """结算后调用兑现或拒绝。"""
        try:
            值=自身.等待()#阻塞取结果
            if 兑现:
                return 兑现(值)#转发成功
            return 值#原值
        except BaseException as 错误:
            if 拒绝:
                return 拒绝(错误)#转发失败
            raise#继续抛

    def catch(自身,拒绝):
        """只处理失败。"""
        return 自身.then(None,拒绝)#委托 then

def 已兑现(值=None):
    """立刻兑现的承诺。"""
    结果=承诺()#新承诺
    结果.兑现(值)#立刻成功
    return 结果#已完成

def 是否thenable(值):
    """值为带 then 的对象时为真。"""
    return 是否对象(值) and callable(getattr(值,'then',None))#thenable

class 聚合错误(Exception):
    """多份失败聚合成一条错误。"""
    def __init__(自身,错误列表,消息=''):
        """保存子错误列表。"""
        super().__init__(消息 or str(错误列表))#消息
        自身.errors=list(错误列表)#子错误
        自身.错误列表=自身.errors#中文别名

def 绑到(回调,thisArg):
    """把派发 this 绑成回调的第一个参数。"""
    if thisArg is None:
        return 回调#无 this
    未绑定=getattr(回调,'__func__',回调)#揭开绑定方法
    def 包装(*位置参数,**关键字参数):
        """以 thisArg 为第一个参数调用。"""
        return 未绑定(thisArg,*位置参数,**关键字参数)#传入 this
    return 包装#绑定后的回调

def 有自有(对象,键):
    """本层是否有该键。"""
    if isinstance(对象,原型映射):
        return 对象.有自有(键)#原型映射
    if isinstance(对象,dict):
        return 键 in 对象#字典
    字典=getattr(对象,'__dict__',None)#实例
    if 字典 is None:
        return False#没有
    return 键 in 字典#自有

def 取对象原型(对象):
    """取出原型映射的父表。"""
    if isinstance(对象,原型映射):
        return 对象.取原型()#父表
    return None#无原型

DisposableList=可释放列表#英文别名
composeError=拼接错误#英文别名
buildOuterStack=构建外层栈#英文别名
getTraceable=取可追踪#英文别名
isConstructor=是否构造器#英文别名
isObject=是否对象#英文别名
createCallable=创建可调用#英文别名
joinPrototype=拼接原型#英文别名
getPropertyDescriptor=取属性描述#英文别名
withProps=叠属性#英文别名
