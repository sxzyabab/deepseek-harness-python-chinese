from . import 系统性能监控
from . import (
    数值判定,
    文本工具,
    序列化编码,
    时间工具,
    线程工具,
    并发原语,
    观察者,
    帧协议,
    sse协议,
    jsonrpc协议,
)
from .数值判定 import (
    最大安全整数,是否有限数,是否整值数,是否正有限数,是否正安全整数,是否非负安全整数,是否有限json数字,
)
from .文本工具 import (
    utf8字节数,截断utf8字节,保留utf8尾部字节,路径转正斜杠,相对正斜杠路径,
)
from .序列化编码 import (
    紧凑json编码,读取json文件,字节转base64url,base64url转字节,严格解码base64,摘要十六进制,
    json转base64url令牌,base64url令牌转json,构造dataurl,解析dataurl,
)
from .时间工具 import 当前毫秒,毫秒转UTC的ISO文本,当前UTC的ISO文本
from .线程工具 import 启动守护线程
from .并发原语 import (
    已中止错误,任务被拒绝错误,操作任务,中止信号,中止控制器,已中止,若已中止则抛出,合成信号,
    并发执行全部,串行执行器,
)
from .观察者 import 通知失败错误,观察者集合,可观察状态
from .帧协议 import (
    帧协议错误,编码长度前缀帧,长度前缀帧解码器,编码内容长度帧,内容长度帧解码器,编码ndjson行,换行帧解码器,
)
from .sse协议 import sse消息,编码sse事件,编码sse注释,sse解码器
from .jsonrpc协议 import (
    解析错误码,无效请求码,方法未找到码,无效参数码,内部错误码,jsonrpc响应错误,
    构造jsonrpc请求,构造jsonrpc通知,构造jsonrpc成功响应,构造jsonrpc错误响应,
    分类jsonrpc消息,未决请求表,
)
from collections import ChainMap as 链映射

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