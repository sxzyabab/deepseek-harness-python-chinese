"""上下文、服务与插件纤程共用的内部辅助。"""
import traceback,types
from collections import ChainMap as 链映射#本层差分叠父映射

################################ 自由使用.号 ################################
from weakref import WeakKeyDictionary as 弱引用键字典#按对象身份存双下数据，对象回收后自动清
_对象内部数据表=弱引用键字典()#对象到它的双下数据面，不占用对象自身的属性槽
未传参=object()
未命中=object()#沿属性链查找时表示链上没有该键

def 是双下划线字符串(名称)->bool:
    return isinstance(名称,str) and 名称.startswith('__') and 名称.endswith('__')

class 自由点访问空间:
    '用户可以自由通过.读写而不触发内部机制'
    def __getattribute__(自身,键):
        """双下名只认数据面；未写入则拦截，不暴露解释器槽。"""
        if 是双下划线字符串(键):
            内部数据=_对象内部数据表.setdefault(自身,{})#该对象的数据面
            if 键 not in 内部数据:
                raise AttributeError(键)
            return 内部数据[键]#用户数据
        #普通属性
        return object.__getattribute__(自身,键)

    def __setattr__(自身,键,值):
        """双下名落数据面，其余照常落实例。"""
        if 是双下划线字符串(键):
            内部数据=_对象内部数据表.setdefault(自身,{})#该对象的数据面
            内部数据[键]=值#写入
            return
        #普通属性
        object.__setattr__(自身,键,值)

#symbol
私有键清单=(
    '阴影','接收者','原目标','元数据','初始化钩子',
    '检查原型','副作用','过滤器','隔离','拦截',
    '初始化','检查','配置','调用','扩展',
    '追踪器','解析配置','是上下文','组','条目',
    ...
)

def 获取内部数据存储(对象)->dict:
    return _对象内部数据表.setdefault(对象,{})

def 获取内部数据(对象,键,默认值=未传参):
    "dict.get等级"
    存储=获取内部数据存储(对象)
    if 默认值 is 未传参:
        return 存储[键]
    else:
        return 存储.get(键,默认值)

def 设置内部数据默认值(对象,键,默认值):
    "dict.setdefault等价"
    存储=获取内部数据存储(对象)
    return 存储.setdefault(键,默认值)

def 设置内部数据(对象,键,值):
    "dict[]=?等价"
    获取内部数据存储(对象)[键]=值

################################ 差分映射 ################################
class 差分映射(链映射):
    def __init__(自身,*父映射):
        父=[]
        for 映射 in 父映射:
            if isinstance(映射,差分映射):
                父.extend(映射.maps)
            elif isinstance(映射,dict):
                父.append(映射)
            else:
                raise TypeError(f'未知映射类型: {type(映射).__name__}')
        super().__init__({},*父)

    def 本层键(自身)->list:
        "本层存储的键"
        return list(自身.maps[0])#自有键快照

    def 本层存在键(自身,键)->bool:
        "本层是否有该键，不上溯"
        return 键 in 自身.maps[0]#只看本层

    def 清点全链值(自身,键)->list:
        "从根到本层，依次交出该键在每一层的自有值"
        结果=[]#由根到叶
        if len(自身.maps)>1:
            父=自身.maps[1]#父表
            if isinstance(父,差分映射):
                结果=父.清点全链值(键)#先收祖先
            elif 键 in 父:
                结果=[父[键]]#普通映射只取一层
        if 键 in 自身.maps[0]:
            结果.append(自身.maps[0][键])#本层最后，优先级最高
        return 结果#由根到叶

    def 更换父映射(自身,父表):
        "换掉父表"
        if 父表 is None:
            自身.maps[:]=[自身.maps[0]]#只留本层
        else:
            自身.maps[:]=[自身.maps[0],父表]#重挂父表

    def 清空本层(自身,源=None):
        "清空本层自有键，再拷入源的自有键"
        自身.maps[0]={}
        if 源 is None:
            return#换成空表
        for 键 in 源:
            自身.maps[0][键]=源[键]#逐个拷入

################################ 有序槽位表 ################################
class 有序槽位表:
    "按插入序登记，可单条摘掉，清空时逆序交出"
    def __init__(自身):
        "初始化空表"
        自身.序号=0#单调递增序号
        自身.映射={}#序号:值

    def 压入(自身,值):
        "追加到表尾，返回只删本条的释放器"
        自身.序号+=1#分配序号
        序号=自身.序号#本条序号
        自身.映射[序号]=值#按序号存入
        def 摘掉本条():
            "只删本序号，重复调用返回假"
            return 自身.映射.pop(序号,None) is not None#是否真的删掉
        return 摘掉本条#释放器

    def 前插(自身,值):
        "插到表头，返回只删本条的释放器"
        自身.序号+=1#分配序号
        序号=自身.序号#本条序号
        重排={序号:值}#新项排在最前
        重排.update(自身.映射)#其余按原顺序接上
        自身.映射=重排#换表
        def 摘掉本条():
            "只删本序号，重复调用返回假"
            return 自身.映射.pop(序号,None) is not None#是否真的删掉
        return 摘掉本条#释放器

    def 删除(自身,值):
        "按对象身份删掉一条"
        for 序号 in list(自身.映射):
            if 自身.映射[序号] is 值:
                del 自身.映射[序号]#按身份删除
                return True#确实删掉
        return False#表里没有

    def 清空(自身):
        "清空并按逆序交出剩余值，供卸载时反向释放"
        值=list(自身.映射.values())#当前全部值
        自身.映射={}#清空
        值.reverse()#后登记的先释放
        return 值#逆序值列表

    @property
    def 长度(自身):
        "当前仍登记的条目数"
        return len(自身.映射)#条目数

    def __iter__(自身):
        return iter(list(自身.映射.values()))#迭代期间允许改表

    def __repr__(自身):
        return repr(list(自身))#列表快照

################################ 类型判断 ################################

def 是对象(值):
    "对应js的对象或函数"
    if 值 is None:
        return False#空值
    if isinstance(值,(bool,str,bytes,int,float)):
        return False#原始值
    return True#对象或函数

################################ 调用方上下文壳 ################################
def 套上调用方上下文(上下文,值):
    "值声明了追踪器就套壳，方法里读到的上下文变成调用方的"
    if not 是对象(值):
        return 值#原始值不用套壳
    追踪器=_对象内部数据表.get(值,{}).get('追踪器')#值上声明的追踪器
    if not 追踪器:
        return 值#没有追踪器，或已经是壳
    return 调用方上下文壳(上下文,值,追踪器)#套壳

class 返回值套壳方法:
    "先调原方法，返回值再套上调用方上下文"
    def __init__(自身,上下文,方法):
        自身._调用方=上下文#调用方上下文
        自身._方法=方法#原方法

    def __call__(自身,*位置参数,**关键字参数):
        return 套上调用方上下文(自身._调用方,自身._方法(*位置参数,**关键字参数))#调完再套壳

class 以壳为自身的方法:
    "用壳当自身去调，方法里读上下文就是调用方的"
    def __init__(自身,壳,函数):
        自身._壳=壳#充当自身
        自身._函数=函数#未绑定函数

    def __call__(自身,*位置参数,**关键字参数):
        调用方=object.__getattribute__(自身._壳,'_调用方')#调用方上下文
        return 套上调用方上下文(调用方,自身._函数(自身._壳,*位置参数,**关键字参数))#以壳为自身

class 调用方上下文壳:
    "读追踪属性换成调用方上下文；关联服务成员转发到上下文"
    __slots__=('_调用方','_原目标','_追踪器')#无实例字典，其余读取走 __getattr__

    def __init__(自身,上下文,值,追踪器):
        object.__setattr__(自身,'_调用方',上下文)#调用方上下文
        object.__setattr__(自身,'_原目标',值)#被代理的原对象
        object.__setattr__(自身,'_追踪器',追踪器)#追踪器

    def __getattr__(自身,属性):
        if 属性.startswith('__') and 属性.endswith('__'):
            raise AttributeError(属性)#协议名不转发，避免 __dict__ 读到原目标
        调用方=object.__getattribute__(自身,'_调用方')#调用方上下文
        原目标=object.__getattribute__(自身,'_原目标')#原对象
        追踪器=object.__getattribute__(自身,'_追踪器')#追踪器
        if 属性==追踪器.get('追踪属性'):
            return 调用方#换成调用方上下文
        关联=追踪器.get('关联服务')#关联服务名
        if 关联 and f'{关联}.{属性}' in getattr(调用方.反射,'属性表',{}):
            return getattr(调用方,f'{关联}.{属性}')#转发到上下文
        内层=getattr(原目标,属性)#从原目标读
        内层追踪器=_对象内部数据表.get(内层,{}).get('追踪器') if 是对象(内层) else None#嵌套追踪器
        if 内层追踪器:
            return 调用方上下文壳(调用方,内层,内层追踪器)#递归套壳
        if callable(内层) and not isinstance(内层,type):
            if getattr(内层,'__self__',None) is 原目标:
                return 以壳为自身的方法(自身,内层.__func__)#绑定方法：自身换成壳
            return 返回值套壳方法(调用方,内层)#其余可调用：只套返回值
        return 内层#其余原样

    def __setattr__(自身,属性,写入值):
        调用方=object.__getattribute__(自身,'_调用方')#调用方上下文
        原目标=object.__getattribute__(自身,'_原目标')#原对象
        追踪器=object.__getattribute__(自身,'_追踪器')#追踪器
        if 属性==追踪器.get('追踪属性'):
            raise AttributeError('不能改写调用方上下文壳的追踪属性')#拒绝改写
        关联=追踪器.get('关联服务')#关联服务名
        if 关联 and f'{关联}.{属性}' in getattr(调用方.反射,'属性表',{}):
            setattr(调用方,f'{关联}.{属性}',写入值)#转发到上下文
            return
        setattr(原目标,属性,写入值)#写回原目标

    def __call__(自身,*位置参数,**关键字参数):
        return 用壳当自身去调(自身,object.__getattribute__(自身,'_原目标'),位置参数,关键字参数)#分发

    def __repr__(自身):
        return repr(object.__getattribute__(自身,'_原目标'))#展示原目标

def 用壳当自身去调(壳,值,位置参数,关键字参数=None):
    "以壳为自身调用值，调用体里读到的是调用方上下文"
    关键字参数=关键字参数 or {}#默认无关键字参数
    调用体=_对象内部数据表.get(值,{}).get('调用')#值上声明的调用体
    if 调用体 is None:
        类调用=getattr(type(值),'__call__',None)#类上的调用协议
        调用体=类调用 if isinstance(类调用,types.FunctionType) else None#只有自定义的才换自身
    if 调用体 is None:
        return 值(*位置参数,**关键字参数)#函数与内建可调用值没有可换的自身
    未绑定=getattr(调用体,'__func__',调用体)#取出未绑定函数
    return 未绑定(壳,*位置参数,**关键字参数)#自身换成壳

class 可点可调服务:
    "既是对象又能直接 () 的服务"
    def __init__(自身,名称,原型,追踪器):
        自身.名称=名称#服务名
        自身._原型=原型#方法来源
        设置内部数据(自身,'追踪器',追踪器)#值上声明的追踪器

    def __call__(自身,*位置参数):
        壳=调用方上下文壳(getattr(自身,'上下文',None),自身,_对象内部数据表.get(自身,{}).get('追踪器'))#套壳
        return 用壳当自身去调(壳,自身,位置参数)#分发

    def __getattr__(自身,属性):
        return getattr(object.__getattribute__(自身,'_原型'),属性)#落到方法原型

################################ 异常 ################################
class 聚合错误(Exception):
    """把多份失败收成一条错误。"""
    def __init__(自身,错误列表:list,消息:str=''):
        """保存子错误列表。"""
        super().__init__(消息 or str(错误列表))#聚合消息
        自身.错误列表=list(错误列表)#子错误

def 构建外层栈():
    """抓一份调用点之上的调用栈，供登记时保存。"""
    return traceback.format_stack()[:-1]#丢掉本辅助自身的帧

def 运行_自带错误栈(回调:callable,调用栈:list=None):
    "运行回调，把登记点的外层调用栈挂到它抛出的错误上"
    #没有给栈,直接用当前的
    if 调用栈 is None:
        调用栈=traceback.format_stack()[:-1]#丢弃这行的调用信息
    try:
        return 回调()#执行被包装的回调
    except Exception as e:
        e.调用栈=调用栈#挂上登记点，日志展开错误时一并输出
        raise#原样抛给调用方

def 绑定对象(回调:callable,对象:object):
    """把派发对象绑成回调的第一个参数，对应 JavaScript 的 this。"""
    if 对象 is None:
        return 回调#没有派发对象
    未绑定=getattr(回调,'__func__',回调)#取出未绑定函数
    def 包装(*位置参数):
        """把派发对象放到参数最前面。"""
        return 未绑定(对象,*位置参数)#补上接收者
    return 包装#绑定后的回调
