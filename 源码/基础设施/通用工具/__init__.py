from . import 系统性能监控

################################ 自由使用.号 ################################
from weakref import WeakKeyDictionary as 弱引用键字典#按对象身份存双下数据，对象回收后自动清
_对象内部数据表=弱引用键字典()#对象到它的双下数据面，不占用对象自身的属性槽
未传参=object()#没有传递该参数,用于区分传了None和默认为None
未命中=object()#沿属性链查找时表示链上没有该键

def 是双下划线字符串(名称)->bool:
    """名称是双下划线包裹的字符串时为真。"""
    return isinstance(名称,str) and 名称.startswith('__') and 名称.endswith('__')

class 自由点访问空间:
    '用户可以自由通过.读写而不触发内部机制'
    def __getattribute__(自身,键):
        """双下名只认数据面；未写入则拦截，不暴露解释器槽。"""
        if 是双下划线字符串(键):
            内部数据=获取内部数据存储(自身)#该对象的数据面
            if 键 not in 内部数据:
                raise AttributeError(键)
            return 内部数据[键]#用户数据
        #普通属性
        return object.__getattribute__(自身,键)

    def __setattr__(自身,键,值):
        """双下名落数据面，其余照常落实例。"""
        if 是双下划线字符串(键):
            内部数据=获取内部数据存储(自身)#该对象的数据面
            内部数据[键]=值#写入
            return
        #普通属性
        object.__setattr__(自身,键,值)

#symbol
私有键清单=(
    '阴影','接收者','原目标','元数据','初始化钩子',
    '检查原型','副作用','过滤器','隔离','拦截',
    '初始化','检查','配置','调用','扩展',
    '追踪器','解析配置','是上下文','组','插件配置',
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