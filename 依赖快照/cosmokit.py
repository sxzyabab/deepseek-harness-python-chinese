"""被全仓库使用过的 cosmokit 符号（中文实现）。"""
import base64,datetime,math,re

#============================== 杂项 ==============================
def 是否可空(值):#判空
    """值为 None 时为真。"""
    return 值 is None#空引用

def 是否非空(值):#判非空
    """值不是 None 时为真。"""
    return not 是否可空(值)#非空引用

def 是否普通对象(数据):#普通对象
    """非数组的映射对象为真。"""
    return isinstance(数据,dict)#映射对象

def 过滤键(对象,过滤器):#过滤条目
    """用谓词过滤对象条目并返回新对象。"""
    结果={}#过滤结果
    for 键,值 in 对象.items():#遍历条目
        if 过滤器(键,值):#谓词通过
            结果[键]=值#保留通过项
    return 结果#新映射

def 映射值(对象,变换):#变换值
    """映射对象的值并保留原键集。"""
    结果={}#新映射
    for 键,值 in 对象.items():#遍历条目
        结果[键]=变换(值,键)#写入变换值
    return 结果#新映射

值映射=映射值#映射值别名

def 挑选(源,键集=None,强制=False):#挑选键
    """从对象挑选键，可选包含缺失项。"""
    if 键集 is None:#无键集则浅拷贝
        return dict(源)#全部拷贝
    结果={}#挑选结果
    for 键 in 键集:#按键收集
        if 强制 or 键 in 源:#强制或键存在
            结果[键]=源[键] if 键 in 源 else None#写入选中键
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

def 分词(源,分隔符表,分隔符):#分词改写
    """按大小写与分隔符把文本收成目标分隔形式。"""
    输出=[]#输出码点
    状态=状态_分隔#当前状态
    下标=0#扫描下标
    while 下标<len(源):#逐码点扫描
        码点=ord(源[下标])#当前码点
        if 大写起点<=码点<=大写终点:#大写字母
            if 状态==状态_大写:#连续大写
                下一个=ord(源[下标+1]) if 下标+1<len(源) else -1#后一码点
                if 小写起点<=下一个<=小写终点:#后接小写
                    输出.append(分隔符)#插入分隔
                输出.append(码点+大小写偏移)#改成小写
            else:#非连续大写
                if 状态!=状态_分隔:#前面不是分隔
                    输出.append(分隔符)#插入分隔
                输出.append(码点+大小写偏移)#改成小写
            状态=状态_大写#进入大写态
        elif 小写起点<=码点<=小写终点:#小写字母
            输出.append(码点)#保留小写
            状态=状态_小写#进入小写态
        elif 码点 in 分隔符表:#源分隔符
            if 状态!=状态_分隔:#前面不是分隔
                输出.append(分隔符)#插入目标分隔
            状态=状态_分隔#进入分隔态
        else:#其它字符
            输出.append(码点)#其它字符原样
        下标+=1#前进一步
    return ''.join(chr(码) for 码 in 输出)#拼成字符串

def 短横(源):#短横形式
    """把文本改成短横分隔。"""
    return 分词(源,[连字符码,下划线码],连字符码)#短横形式

连字符化=短横#短横的运行时别名

#============================== 类型 / 二进制 / 克隆 ==============================
缺省=object()#未传第二参的哨兵

def 是(类型名,值=缺省):#构造名检测
    """用构造名检测值；只传类型名则返回谓词。"""
    if 值 is 缺省:#未传值
        def 谓词(待测):#柯里化谓词
            """柯里化后检测单个值。"""
            return 是(类型名,待测)#复用双参
        return 谓词#返回谓词
    类型表={
        'Date':datetime.datetime,#日期
        'RegExp':re.Pattern,#正则
        'ArrayBuffer':(bytes,bytearray),#缓冲
        'SharedArrayBuffer':memoryview,#共享缓冲近似
        'Array':list,#数组
    }#构造名表
    目标=类型表.get(类型名)#取出类型
    if 目标 is not None and isinstance(值,目标):#实例命中
        return True#实例命中
    return type(值).__name__==类型名#按类名回退

def _是否类数组缓冲(值):#类数组缓冲
    """值为类数组缓冲时为真。"""
    return 是('ArrayBuffer',值) or 是('SharedArrayBuffer',值)#两类缓冲

def _是否数组缓冲源(值):#缓冲源
    """值为缓冲或缓冲视图时为真。"""
    return _是否类数组缓冲(值) or isinstance(值,memoryview)#源检测

class 二进制:#二进制命名空间
    """二进制源检测与 base64/hex 转换。"""
    是=staticmethod(_是否类数组缓冲)#类数组缓冲检测
    是源=staticmethod(_是否数组缓冲源)#源检测

    @staticmethod
    def 从源(源):#收成缓冲
        """把视图收成底层缓冲。"""
        if isinstance(源,memoryview):#视图
            return 源.tobytes()#拷出字节
        return 源#已是缓冲

    @staticmethod
    def 转base64(源):#编码 base64
        """把二进制编码成 base64。"""
        源=二进制.从源(源)#底层缓冲
        return base64.b64encode(bytes(源)).decode('ascii')#base64 文本

    @staticmethod
    def 从base64(源):#解码 base64
        """把 base64 解码成二进制。"""
        return base64.b64decode(源)#字节缓冲

    @staticmethod
    def 转十六进制(源):#编码十六进制
        """把二进制编码成十六进制。"""
        源=二进制.从源(源)#底层缓冲
        return bytes(源).hex()#十六进制文本

    @staticmethod
    def 从十六进制(源):#解码十六进制
        """把十六进制解码成二进制。"""
        十六=源 if len(源)%2==0 else 源[:-1]#对齐长度
        return bytes.fromhex(十六)#字节缓冲

二进制.is=二进制.是#英文别名
二进制.isSource=二进制.是源#英文别名
二进制.fromSource=二进制.从源#英文别名
二进制.toBase64=二进制.转base64#英文别名
二进制.fromBase64=二进制.从base64#英文别名
二进制.toHex=二进制.转十六进制#英文别名
二进制.fromHex=二进制.从十六进制#英文别名

def 克隆(源,引用表=None):#深克隆
    """深克隆常见值并保留环。"""
    if 引用表 is None:#未传入引用表
        引用表={}#环引用表
    if 源 is None or isinstance(源,(int,float,str,bool,complex,type)):#非对象
        return 源#非对象
    if 是('Date',源):#日期
        return 源.replace()#克隆日期
    if 是('RegExp',源):#正则
        return re.compile(源.pattern,源.flags)#克隆正则
    if _是否类数组缓冲(源):#缓冲
        return bytes(memoryview(源))#拷贝缓冲
    if isinstance(源,memoryview):#视图
        return 源.tobytes()#视图收成字节
    缓存=引用表.get(id(源))#环引用缓存
    if 缓存 is not None:#已克隆
        return 缓存#返回已克隆对象
    if isinstance(源,list):#数组
        结果=[]#新列表
        引用表[id(源)]=结果#登记
        for 值 in 源:#逐项克隆
            结果.append(克隆(值,引用表))#克隆元素
        return 结果#克隆列表
    if isinstance(源,dict):#映射
        结果={}#新映射
        引用表[id(源)]=结果#登记
        for 键 in 源:#逐字段克隆
            结果[键]=克隆(源[键],引用表)#克隆字段
        return 结果#克隆映射
    结果=type(源).__new__(type(源))#按原型新建
    引用表[id(源)]=结果#登记
    字段=getattr(源,'__dict__',None)#自有字段
    if 字段 is not None:#有实例字典
        for 键 in 字段:#逐属性克隆
            setattr(结果,键,克隆(字段[键],引用表))#克隆属性
    return 结果#克隆对象

def 深度相等(甲,乙,严格=False):#深比较
    """深度比较数组、日期、正则、缓冲与普通对象字段。"""
    if 甲 is 乙:#同一引用
        return True#同一引用
    if 甲==乙:#值相等
        if isinstance(甲,bool) or isinstance(乙,bool):#布尔参与
            return type(甲) is type(乙)#类型也要相同
        if not isinstance(甲,(dict,list)) and not isinstance(乙,(dict,list)):#非容器
            return True#原始值相等
    if not 严格 and 是否可空(甲) and 是否可空(乙):#空值相等
        return True#空值相等
    if type(甲) is not type(乙):#类型不同
        if isinstance(甲,(bytes,bytearray,memoryview)) and isinstance(乙,(bytes,bytearray,memoryview)):#缓冲可交叉
            pass#缓冲可交叉
        else:#其它类型不同
            return False#类型不同
    if not isinstance(甲,(dict,list,datetime.datetime,re.Pattern,bytes,bytearray,memoryview)):#非对象
        return False#非对象且未在上面判等
    if 是否可空(甲) or 是否可空(乙):#一侧为空
        return False#一侧为空
    def 检查(谓词,然后):#两侧同类检查
        """两侧同属一类则比较。"""
        甲命中=谓词(甲)#左侧
        乙命中=谓词(乙)#右侧
        if 甲命中:#左侧命中
            return 然后(甲,乙) if 乙命中 else False#同类比较
        if 乙命中:#仅右侧命中
            return False#仅右侧命中
        return None#都未命中
    def 是否列表(值):#列表谓词
        """值为列表时为真。"""
        return isinstance(值,list)#列表
    def 比较列表(左,右):#比较列表
        """逐项深度比较列表。"""
        return len(左)==len(右) and all(深度相等(左[下标],右[下标],严格) for 下标 in range(len(左)))#逐项
    def 比较日期(左,右):#比较日期
        """按时间戳比较日期。"""
        return 左.timestamp()==右.timestamp()#时间戳
    def 比较正则(左,右):#比较正则
        """按模式与标志比较正则。"""
        return 左.pattern==右.pattern and 左.flags==右.flags#模式与标志
    def 比较缓冲(左,右):#比较缓冲
        """按字节内容比较缓冲。"""
        return bytes(左)==bytes(右)#字节相等
    数组结果=检查(是否列表,比较列表)#数组比较
    if 数组结果 is not None:#数组结论
        return 数组结果#数组结论
    日期结果=检查(是('Date'),比较日期)#日期比较
    if 日期结果 is not None:#日期结论
        return 日期结果#日期结论
    正则结果=检查(是('RegExp'),比较正则)#正则比较
    if 正则结果 is not None:#正则结论
        return 正则结果#正则结论
    缓冲结果=检查(_是否类数组缓冲,比较缓冲)#缓冲比较
    if 缓冲结果 is not None:#缓冲结论
        return 缓冲结果#缓冲结论
    def 取字段(值):#取字段映射
        """取出可比较的字段映射。"""
        if isinstance(值,dict):#映射
            return 值#映射本身
        字段=getattr(值,'__dict__',None)#自有字段
        if 字段 is not None:#有实例字典
            return 字段#对象字段
        return {}#无字段
    甲字段=取字段(甲)#左侧字段
    乙字段=取字段(乙)#右侧字段
    键集=[]#合并键
    for 键 in list(甲字段)+list(乙字段):#合并两侧键
        if 键 not in 键集:#尚未收录
            键集.append(键)#保留首次
    return all(深度相等(甲字段[键] if 键 in 甲字段 else None,乙字段[键] if 键 in 乙字段 else None,严格) for 键 in 键集)#字段比较

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
    def 补位(源,长度=2):#补零
        """把数字补成固定宽度。"""
        return str(源).rjust(长度,'0')#补零

    @staticmethod
    def 格式化(毫秒数):#最短单位
        """把毫秒收成最短单位字符串。"""
        绝对=abs(毫秒数)#绝对值
        if 绝对>=时间.日-时间.时/2:#按天
            return str(int(math.floor(毫秒数/时间.日+0.5)))+'d'#天
        elif 绝对>=时间.时-时间.分/2:#按时
            return str(int(math.floor(毫秒数/时间.时+0.5)))+'h'#小时
        elif 绝对>=时间.分-时间.秒/2:#按分
            return str(int(math.floor(毫秒数/时间.分+0.5)))+'m'#分钟
        elif 绝对>=时间.秒:#按秒
            return str(int(math.floor(毫秒数/时间.秒+0.5)))+'s'#秒
        return str(毫秒数)+'ms'#毫秒

    @staticmethod
    def 模板(模板,时刻=None):#模板格式化
        """按模板格式化日期，每次只替换首次出现。"""
        if 时刻 is None:#默认现在
            时刻=datetime.datetime.now()#当前时间
        年=str(时刻.year)#年份
        文本=模板#待替换模板
        文本=文本.replace('yyyy',年,1)#四位年
        文本=文本.replace('yy',年[2:],1)#两位年
        文本=文本.replace('MM',时间.补位(时刻.month),1)#月
        文本=文本.replace('dd',时间.补位(时刻.day),1)#日
        文本=文本.replace('hh',时间.补位(时刻.hour),1)#时
        文本=文本.replace('mm',时间.补位(时刻.minute),1)#分
        文本=文本.replace('ss',时间.补位(时刻.second),1)#秒
        文本=文本.replace('SSS',时间.补位(时刻.microsecond//1000,3),1)#毫秒
        return 文本#格式化结果

时间.millisecond=时间.毫秒#英文别名
时间.second=时间.秒#英文别名
时间.minute=时间.分#英文别名
时间.hour=时间.时#英文别名
时间.day=时间.日#英文别名
时间.week=时间.周#英文别名
时间.toDigits=时间.补位#英文别名
时间.format=时间.格式化#英文别名
时间.template=时间.模板#英文别名
Time=时间#英文别名

#============================== 英文别名 ==============================
defineProperty=定义属性#英文别名
isNullable=是否可空#英文别名
isNonNullable=是否非空#英文别名
isPlainObject=是否普通对象#英文别名
filterKeys=过滤键#英文别名
mapValues=映射值#英文别名
valueMap=值映射#英文别名
pick=挑选#英文别名
hyphenate=连字符化#英文别名
paramCase=短横#英文别名
Binary=二进制#英文别名
clone=克隆#英文别名
deepEqual=深度相等#英文别名

__all__=[
    '是否可空','是否非空','是否普通对象','过滤键','映射值','值映射','挑选','定义属性',#杂项
    '短横','连字符化',#字符串
    '是','二进制','克隆','深度相等',#类型
    '时间','Time',#时间
    'isNullable','isNonNullable','isPlainObject','filterKeys','mapValues','valueMap','pick','defineProperty',#杂项英文
    'paramCase','hyphenate','Binary','clone','deepEqual',#类型英文
]#公开导出
