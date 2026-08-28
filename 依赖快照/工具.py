import base64,datetime,math,re
import traceback,types
from collections import ChainMap as 链映射

def 字典键过滤(字典:dict,过滤器):#过滤键值
    "字典版过滤器"
    结果={}#过滤结果
    for 键,值 in 字典.items():#遍历键值
        if 过滤器(键,值):#判断通过
            结果[键]=值#保留通过项
    return 结果#新字典

def 字典值转换(字典:dict,转换器):#变换值
    "批量处理字典的值"
    结果={}#新字典
    for 键,值 in 字典.items():#遍历键值
        结果[键]=转换器(值,键)#写入变换值
    return 结果#新字典

def 复制字典(源字典:dict,*,键白名单=None,保证键存在=False):#挑选键
    "更高级的字典复制,支持自行挑选需要的键及确保他们存在"
    if 键白名单 is None:#无键白名单则浅拷贝
        return dict(源字典)#全部拷贝
    结果={}#挑选结果
    for 键 in 键白名单:#按键收集
        if 保证键存在 or 键 in 源字典:#强制或键存在
            结果[键]=源字典[键] if 键 in 源字典 else None#写入选中键
    return 结果#返回挑选结果

def 定义属性(对象,键,值):#定义属性
    """写入自有属性并返回对象。"""
    if isinstance(对象,dict):#字典
        对象[键]=值#字典写入
    else:#实例或函数
        对象.__dict__[键]=值#写入实例字典
    return 对象#返回原对象

#============================== 字符串 ==============================
状态_分隔=0#分隔状态
状态_大写=1#大写状态
状态_小写=2#小写状态
连字符码=45#连字符码点
下划线码=95#下划线码点
大写起点=65#大写字母起点
大写终点=90#大写字母终点
小写起点=97#小写字母起点
小写终点=122#小写字母终点
大小写偏移=32#大小写码点差

def 统一分隔格式(文本:str,清理分隔符:list[int],目标分隔符:int):#分词改写
    "将常见的文本分隔形式统一为所需的分隔符(驼峰、下划线、短横等,支持混用)"
    输出=[]#输出码点
    状态=状态_分隔#当前状态
    下标=0#扫描索引
    while 下标<len(文本):#逐码点扫描
        码点=ord(文本[下标])#当前码点
        if 大写起点<=码点<=大写终点:#大写字母
            if 状态==状态_大写:#连续大写
                下一个=ord(文本[下标+1]) if 下标+1<len(文本) else -1#后一码点
                if 小写起点<=下一个<=小写终点:#后接小写
                    输出.append(目标分隔符)#插入分隔
                输出.append(码点+大小写偏移)#改成小写
            else:#非连续大写
                if 状态!=状态_分隔:#前面不是分隔
                    输出.append(目标分隔符)#插入分隔
                输出.append(码点+大小写偏移)#改成小写
            状态=状态_大写#进入大写态
        elif 小写起点<=码点<=小写终点:#小写字母
            输出.append(码点)#保留小写
            状态=状态_小写#进入小写态
        elif 码点 in 清理分隔符:#源分隔符
            if 状态!=状态_分隔:#前面不是分隔
                输出.append(目标分隔符)#插入目标分隔
            状态=状态_分隔#进入分隔态
        else:#其它字符
            输出.append(码点)#其它字符原样
        下标+=1#前进一步
    return ''.join(chr(码) for 码 in 输出)#拼成字符串

def 统一为短横分隔(文本:str):#短横形式
    "把文本改成短横分隔。"
    return 统一分隔格式(文本,[连字符码,下划线码],连字符码)#短横形式

#============================== 类型 / 二进制 / 克隆 ==============================
未传参=object()#未传第二参的哨兵

def 类型是(类型名:str,值=未传参):#构造名检测
    """用构造名检测值；只传类型名则返回判断。"""
    类型名=类型名.lower()#小写类型名
    if 值 is 未传参:#未传值
        def 类型检测器(待测):#柯里化判断
            """柯里化后检测单个值。"""
            return 类型是(类型名,待测)#复用双参
        return 类型检测器#返回判断
    类型表={
        'date':datetime.datetime,#日期
        'regexp':re.Pattern,#正则
        'arraybuffer':(bytes,bytearray),#缓冲
        'sharedarraybuffer':memoryview,#共享缓冲近似
        'array':list,#数组
    }#构造名表
    目标=类型表.get(类型名)#取出类型
    if 目标 is not None and isinstance(值,目标):#实例命中
        return True#实例命中
    return type(值).__name__==类型名#按类名回退

def 是类数组缓冲(值)->bool:
    "值为类数组缓冲时为真"
    return 类型是('ArrayBuffer',值) or 类型是('SharedArrayBuffer',值)#两类缓冲

def 是数组缓冲源(值)->bool:
    "值为缓冲或缓冲视图时为真"
    return 是类数组缓冲(值) or isinstance(值,memoryview)#源检测

class 二进制:
    是=staticmethod(是类数组缓冲)#类数组缓冲检测
    是源=staticmethod(是数组缓冲源)#源检测

    @staticmethod
    def 从字节源(字节源:bytes|bytearray|memoryview)->bytes|bytearray:
        "从字节相关对象转换"
        if isinstance(字节源,memoryview):#视图
            return 字节源.tobytes()#拷出字节
        elif isinstance(字节源,(bytes,bytearray)):#字节
            return 字节源#字节
        else:
            return bytes(字节源)#尝试转换为字节

    @staticmethod
    def 转base64(字节源:bytes|bytearray|memoryview)->str:#编码 base64
        "把二进制数据编码成base64"
        字节=二进制.从字节源(字节源)#底层缓冲
        return base64.b64encode(字节).decode('ascii')#base64 文本

    @staticmethod
    def 从base64(base64文本:str)->bytes:
        "把 base64 解码成二进制。"
        return base64.b64decode(base64文本)#字节缓冲

    @staticmethod
    def 转十六进制(字节源:bytes|bytearray|memoryview)->str:#编码十六进制
        "把二进制编码成十六进制。"
        字节=二进制.从字节源(字节源)#底层缓冲
        return bytes(字节).hex()#十六进制文本

    @staticmethod
    def 从十六进制(十六进制文本:str)->bytes:
        "把十六进制解码成二进制。"
        对齐=十六进制文本 if len(十六进制文本)%2==0 else 十六进制文本[:-1]#对齐长度
        return bytes.fromhex(对齐)#字节缓冲

def 克隆(源,引用表=None):
    "深克隆常见值并保留环状引用"
    #已创建对象缓存
    if 引用表 is None:
        引用表={}
    #不用处理引用的
    if 源 is None or isinstance(源,(int,float,str,bool,complex,type)):
        return 源
    #函数、方法与可调用对象按引用共享
    if callable(源):
        return 源
    if 类型是('Date',源):#日期
        return 源.replace()#克隆日期
    if 类型是('RegExp',源):#正则
        return re.compile(源.pattern,源.flags)#克隆正则
    if 是类数组缓冲(源):#缓冲
        return bytes(memoryview(源))#拷贝缓冲
    if isinstance(源,memoryview):#视图
        return 源.tobytes()#视图收成字节
    #解决对象内部环状引用
    缓存=引用表.get(id(源))
    if 缓存 is not None:#已克隆
        return 缓存
    #列表克隆
    if isinstance(源,list):
        结果=[]
        引用表[id(源)]=结果
        for 值 in 源:
            #克隆内部元素
            结果.append(克隆(值,引用表))
        return 结果
    #字典克隆
    if isinstance(源,dict):
        结果={}
        引用表[id(源)]=结果
        for 键 in 源:
            结果[键]=克隆(源[键],引用表)
        return 结果
    #元组与集合不可增量填充,只能先克隆元素再整体建
    if isinstance(源,tuple):
        return type(源)(克隆(值,引用表) for 值 in 源)
    if isinstance(源,(set,frozenset)):
        return type(源)(克隆(值,引用表) for 值 in 源)
    #其他对象克隆
    结果=type(源).__new__(type(源))#按原类型新建,不会执行init
    引用表[id(源)]=结果#登记
    字段=getattr(源,'__dict__',None)#实例数据
    if 字段 is not None:#有实例字典
        for 键 in 字段:#逐属性克隆
            setattr(结果,键,克隆(字段[键],引用表))
    return 结果#克隆对象

def 是数值(值)->bool:
    "值为数字时为真,布尔按JS的惯例不算数字"
    return isinstance(值,(int,float)) and not isinstance(值,bool)#布尔单独比较

def 深入比较(甲,乙,*,严格比较=False):
    """深度比较列表(数组)、日期、正则、缓冲与普通对象字段
    严格模式是js下的null/undefined比较,python弃用,仅保留参数进行兼容"""
    #数字只看数值,1与1.0相等,NaN与自己不相等
    if 是数值(甲) and 是数值(乙):
        return 甲==乙
    #同一引用
    if 甲 is 乙:
        return True
    #一侧为空
    if (甲 is None) or (乙 is None):
        return False
    #不同类型
    if type(甲) is not type(乙):
        #字节留后面比较
        if isinstance(甲,(bytes,bytearray,memoryview)) and isinstance(乙,(bytes,bytearray,memoryview)):#缓冲可交叉
            pass
        else:#其它类型不同
            return False
    #相等
    if 甲==乙:
        #非容器类型时,==为True说明值相等
        if not isinstance(甲,(dict,list)) and not isinstance(乙,(dict,list)):
            return True
    #特定对象的自定义检查(到此处同类还不==)
    #常见值
    if isinstance(甲,(str,bool,int,float,complex)):
        return False
    #列表与元组
    elif isinstance(甲,(list,tuple)):
        return len(甲)==len(乙) and all(
            深入比较(甲[下标],乙[下标])
            for 下标 in range(len(甲))
            )#逐项
    #!不支持集合!
    elif isinstance(甲,(set,frozenset)):
        return False
    #时间
    elif isinstance(甲,datetime.datetime):
        return 甲.timestamp()==乙.timestamp()
    #re
    elif isinstance(甲,re.Pattern):
        return 甲.pattern==乙.pattern and 甲.flags==乙.flags
    #字节
    elif isinstance(甲,(bytes,bytearray,memoryview)):
        return bytes(甲)==bytes(乙)

    else:
        #其他对象比实例字典
        if not isinstance(甲,dict):
            甲字段=getattr(甲,'__dict__',None)
            乙字段=getattr(乙,'__dict__',None)
            #没有实例字典就没有可比的字段,前面的==已经判过值相等
            if 甲字段 is None or 乙字段 is None:
                return False
            甲=甲字段
            乙=乙字段
        键集=set(list(甲)+list(乙))#合并两侧键
        #逐键比较字典
        return all(深入比较(
            甲[键] if 键 in 甲 else None,
            乙[键] if 键 in 乙 else None,
            ) for 键 in 键集)

#============================== 时间 ==============================
class 时间:#时间命名空间
    """被使用的时间常量与格式化。"""
    毫秒=1#一毫秒
    秒=1000#一千毫秒
    分=秒*60#一分钟
    时=分*60#一小时
    日=时*24#一天
    周=日*7#一周

    @staticmethod
    def 左补零(原时间,目标长度=2):
        "左边补零,把数字补成固定宽度"
        return str(原时间).rjust(目标长度,'0')

    @staticmethod
    def 格式化(毫秒数:int)->str:#最短单位
        "把毫秒转换成简短的时间描述(n 天/时/...)"
        绝对=abs(毫秒数)#绝对值
        if 绝对>=时间.日-时间.时/2:#按天
            return str(int(math.floor(毫秒数/时间.日+0.5)))+'d'
        elif 绝对>=时间.时-时间.分/2:#按时
            return str(int(math.floor(毫秒数/时间.时+0.5)))+'h'
        elif 绝对>=时间.分-时间.秒/2:#按分
            return str(int(math.floor(毫秒数/时间.分+0.5)))+'m'
        elif 绝对>=时间.秒:#按秒
            return str(int(math.floor(毫秒数/时间.秒+0.5)))+'s'
        return str(毫秒数)+'ms'

    @staticmethod
    def 格式化时间(模板:str,时刻:datetime.datetime=None)->str:#模板格式化
        "按模板格式化日期"
        if 时刻 is None:#默认现在
            时刻=datetime.datetime.now()#当前时间
        年=str(时刻.year)#年份
        文本=模板#待替换模板
        文本=文本.replace('yyyy',年,1)#四位年
        文本=文本.replace('yy',年[2:],1)#两位年
        文本=文本.replace('MM',时间.左补零(时刻.month),1)#月
        文本=文本.replace('dd',时间.左补零(时刻.day),1)#日
        文本=文本.replace('hh',时间.左补零(时刻.hour),1)#时
        文本=文本.replace('mm',时间.左补零(时刻.minute),1)#分
        文本=文本.replace('ss',时间.左补零(时刻.second),1)#秒
        文本=文本.replace('SSS',时间.左补零(时刻.microsecond//1000,3),1)#毫秒
        return 文本#格式化结果





################################ 自由使用.号 ################################
from weakref import WeakKeyDictionary as 弱引用键字典#按对象身份存双下数据，对象回收后自动清
_对象内部数据表=弱引用键字典()#对象到它的双下数据面，不占用对象自身的属性槽
未传参=object()#没有传递该参数,用于区分传了None和默认为None
未命中=object()#沿属性链查找时表示链上没有该键

def 是双下划线字符串(名称)->bool:
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
        "当前仍登记的数量"
        return len(自身.映射)#数量

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
class Proxy:
    '对应js的Proxy'
    __slots__=('__weakref__',)#无实例字典，目标与处理器都放数据面，弱引用槽供数据表按身份存

    def __init__(自身,代理目标,处理器:dict):
        "处理器按 取属性、写属性、有属性、调用 给出要拦截的项，没给的项原样落到目标上"
        if not isinstance(处理器,dict):
            raise TypeError(f'处理器以字典形式提供,不接收: {type(处理器).__name__}')
        设置内部数据(自身,'代理目标',代理目标)#被代理的对象
        设置内部数据(自身,'处理器',处理器)#拦截项

    def __getattr__(自身,属性):
        目标=获取内部数据(自身,'代理目标')#被代理的对象
        拦截=获取内部数据(自身,'处理器').get('取属性')#读拦截
        if 拦截 is None:
            return getattr(目标,属性)#没写拦截就读目标
        return 拦截(目标,属性)#交给拦截

    def __setattr__(自身,属性,值):
        目标=获取内部数据(自身,'代理目标')#被代理的对象
        拦截=获取内部数据(自身,'处理器').get('写属性')#写拦截
        if 拦截 is None:
            setattr(目标,属性,值)#没写拦截就写目标
            return
        拦截(目标,属性,值)#交给拦截

    def __contains__(自身,属性):
        目标=获取内部数据(自身,'代理目标')#被代理的对象
        拦截=获取内部数据(自身,'处理器').get('有属性')#in 拦截
        if 拦截 is None:
            return hasattr(目标,属性)#没写拦截就问目标
        return 拦截(目标,属性)#交给拦截

    def __call__(自身,*位置参数,**关键字参数):
        目标=获取内部数据(自身,'代理目标')#被代理的对象
        拦截=获取内部数据(自身,'处理器').get('调用')#调用拦截
        if 拦截 is None:
            return 目标(*位置参数,**关键字参数)#没写拦截就调目标
        return 拦截(目标,位置参数,关键字参数)#交给拦截

    def __repr__(自身):
        return repr(获取内部数据(自身,'代理目标'))#展示被代理对象

def 套上调用方上下文(上下文,值):
    "值声明了追踪器就套壳，方法里读到的上下文变成调用方的"
    if not 是对象(值):
        return 值#原始值不用套壳
    追踪器=_对象内部数据表.get(值,{}).get('追踪器')#值上声明的追踪器
    if not 追踪器:
        return 值#没有追踪器，或已经是壳
    return 调用方上下文壳(上下文,值,追踪器)#套壳

class 调用方上下文壳(Proxy):
    "读追踪属性换成调用方上下文；关联服务成员转发到上下文"
    def __init__(自身,上下文,值,追踪器):
        def 取属性(目标,属性):
            if 属性.startswith('__') and 属性.endswith('__'):
                raise AttributeError(属性)#协议名不转发，避免 __dict__ 读到原目标
            if 属性==追踪器.get('追踪属性'):
                return 上下文#换成调用方上下文
            关联=追踪器.get('关联服务')#关联服务名
            if 关联 and f'{关联}.{属性}' in 上下文.反射.属性表:
                return getattr(上下文,f'{关联}.{属性}')#转发到上下文
            内层=getattr(目标,属性)#从原目标读
            内层追踪器=_对象内部数据表.get(内层,{}).get('追踪器') if 是对象(内层) else None#嵌套追踪器
            if 内层追踪器:
                return 调用方上下文壳(上下文,内层,内层追踪器)#递归套壳
            if callable(内层) and not isinstance(内层,type):
                if getattr(内层,'__self__',None) is 目标:
                    def 以壳调用(函数,位置参数,关键字参数):
                        return 套上调用方上下文(上下文,函数(自身,*位置参数,**关键字参数))#自身换成壳
                    return Proxy(内层.__func__,{'调用':以壳调用})#绑定方法
                def 套返回值(函数,位置参数,关键字参数):
                    return 套上调用方上下文(上下文,函数(*位置参数,**关键字参数))#调完再套壳
                return Proxy(内层,{'调用':套返回值})#其余可调用：只套返回值
            return 内层#其余原样

        def 写属性(目标,属性,写入值):
            if 属性==追踪器.get('追踪属性'):
                raise AttributeError('不能改写调用方上下文壳的追踪属性')#拒绝改写
            关联=追踪器.get('关联服务')#关联服务名
            if 关联 and f'{关联}.{属性}' in 上下文.反射.属性表:
                setattr(上下文,f'{关联}.{属性}',写入值)#转发到上下文
                return
            setattr(目标,属性,写入值)#写回原目标

        def 调用(目标,位置参数,关键字参数):
            调用体=_对象内部数据表.get(目标,{}).get('调用')#值上声明的调用体
            if 调用体 is None:
                类调用=getattr(type(目标),'__call__',None)#类上的调用协议
                调用体=类调用 if isinstance(类调用,types.FunctionType) else None#只有自定义的才换自身
            if 调用体 is None:
                return 目标(*位置参数,**关键字参数)#函数与内建可调用值没有可换的自身
            未绑定=getattr(调用体,'__func__',调用体)#取出未绑定函数
            return 未绑定(自身,*位置参数,**关键字参数)#自身换成壳

        Proxy.__init__(自身,值,{'取属性':取属性,'写属性':写属性,'调用':调用})#挂拦截

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


#loader
表达式键='__jsExpr'#序列化后的表达式节点上存放源码的键

def 是否表达式节点(值):
    "值是序列化过的加载器表达式节点时为真"
    if isinstance(值,dict):
        return 表达式键 in 值#映射形态
    if 值 is None or isinstance(值,(str,bytes,bool,int,float)):
        return False#原始值不是节点
    return hasattr(值,表达式键)#对象形态

def 取表达式(节点):
    "从表达式节点里取出源码"
    return 节点[表达式键] if isinstance(节点,dict) else getattr(节点,表达式键)#源码

def 求值(上下文,表达式):
    "把上下文的属性当作局部名，求值一段表达式"
    class 上下文作用域(dict):
        "把上下文属性暴露成求值时的局部名"
        def __missing__(自身,键):
            "局部名没命中就去上下文上找同名属性"
            try:
                return getattr(上下文,键)#上下文属性
            except AttributeError:
                raise KeyError(键)#当成未定义名
    return eval(表达式,{'ctx':上下文,'上下文':上下文},上下文作用域())#求值

def 插值(上下文,值):
    "递归把配置里的表达式节点替换成求值结果"
    if 是否表达式节点(值):
        return 求值(上下文,取表达式(值))#换成求值结果
    if 值 is None or isinstance(值,(str,bytes,bool,int,float)):
        return 值#原始值原样返回
    if isinstance(值,list):
        return [插值(上下文,项) for 项 in 值]#逐项插值
    if isinstance(值,dict):
        return 字典值转换(值,lambda 项,键:插值(上下文,项))#逐值插值
    return 值#其它对象原样返回
