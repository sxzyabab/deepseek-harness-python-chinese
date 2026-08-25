"""被全仓库使用过的 cosmokit 符号（中文实现）。"""
import base64,datetime,math,re

def 字典键过滤(字典:dict,过滤器):#过滤条目
    "字典版过滤器"
    结果={}#过滤结果
    for 键,值 in 字典.items():#遍历条目
        if 过滤器(键,值):#谓词通过
            结果[键]=值#保留通过项
    return 结果#新字典

def 字典值转换(字典:dict,转换器):#变换值
    "批量处理字典的值"
    结果={}#新字典
    for 键,值 in 字典.items():#遍历条目
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
    """用构造名检测值；只传类型名则返回谓词。"""
    类型名=类型名.lower()#小写类型名
    if 值 is 未传参:#未传值
        def 类型检测器(待测):#柯里化谓词
            """柯里化后检测单个值。"""
            return 类型是(类型名,待测)#复用双参
        return 类型检测器#返回谓词
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
