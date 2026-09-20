"""程序求值、输出捕获，以及进程通道上的宿主绑定代理。"""
from .输出json import json字符串字节上限,json值字节上限,截断json字符串字节#字节计量
from .json线 import 快照ptcjson值,编码ptcjson线,解码ptcjson线#线格式
from .协议 import 节点ptc错误#本包异常
from .通道 import 任务#绑定调用结算

__all__=['日志缓冲','制作控制台垫片','捕获流写入','准备完成','准备异常','制作绑定错误类表','接线回复','制作命名空间','运行程序']#仅中文公开名

捕获错误=节点ptc错误#引导闭包捕获的错误构造器
捕获对象创建=dict#模块捕获的 dict
捕获定义属性=setattr#模块捕获的 setattr

控制台级别=('log','info','warn','error','debug')#垫片五个级别

class 日志缓冲:#合计外层 JSON 字节预算下的有序文本捕获
    """合计外层 JSON 字节预算下的有序文本捕获；每条落地即交给接收方。"""
    def __init__(自身,最大字节,接收,触顶=None):#记下预算与回调
        """记下硬顶、接收方与触顶回调。空日志数组 JSON 为 [] 占 2 字节。"""
        自身._最大字节=最大字节#硬顶
        自身._接收=接收#每条文本
        自身._触顶=触顶 if 触顶 is not None else (lambda:None)#触顶一次
        自身._字节=2#[]
        自身._条数=0#已接纳
        自身._已截=False#是否已触顶

    def 压入(自身,文本):#接纳一条
        """把文本计入预算并交给接收方；触顶后丢弃并只报告一次。"""
        if 自身._已截:#已触顶
            return#丢弃
        分隔=1 if 自身._条数>0 else 0#逗号
        可用=自身._最大字节-自身._字节-分隔#本条预算
        串字节=json字符串字节上限(文本,可用)#整条？
        if 串字节 is None:#越界
            自身._已截=True#标记
            前缀=截断json字符串字节(文本,可用)#前缀
            if len(前缀)>0:#有前缀
                前缀字节=json字符串字节上限(前缀,可用)#前缀字节
                if 前缀字节 is None:#截断保证可放入
                    raise 捕获错误('program output ledger produced an oversized log prefix')#自相矛盾
                自身._字节+=前缀字节+分隔#入账
                自身._条数+=1#加一条
                自身._接收(前缀)#交付前缀
            自身._触顶()#报告一次
            return
        自身._字节+=串字节+分隔#入账
        自身._条数+=1#加一条
        自身._接收(文本)#交付

    def 剩余输出字节(自身):#完成值或失败消息预算
        """捕获日志之后剩给完成值或失败消息的精确 JSON 字节。"""
        return 自身._最大字节-自身._字节#剩余

class 控制台垫片:#五个级别的小控制台
    """程序拿到的五个级别方法，用 repr 渲染非字符串参数。"""
    def __init__(自身,缓冲):#绑到日志缓冲
        """记下缓冲。"""
        自身._缓冲=缓冲#日志缓冲
    def _渲染(自身,*参数):#拼一行
        """字符串原样，其余 repr，空格拼接。"""
        段列表=[]#各段
        for 项 in 参数:#逐参
            段列表.append(项 if type(项) is str else repr(项))#渲染
        return ' '.join(段列表)#一行
    def log(自身,*参数):#log
        """写入 log 级。"""
        自身._缓冲.压入(自身._渲染(*参数))#压入
    def info(自身,*参数):#info
        """写入 info 级。"""
        自身._缓冲.压入(自身._渲染(*参数))#压入
    def warn(自身,*参数):#warn
        """写入 warn 级。"""
        自身._缓冲.压入(自身._渲染(*参数))#压入
    def error(自身,*参数):#error
        """写入 error 级。"""
        自身._缓冲.压入(自身._渲染(*参数))#压入
    def debug(自身,*参数):#debug
        """写入 debug 级。"""
        自身._缓冲.压入(自身._渲染(*参数))#压入

def 制作控制台垫片(缓冲):#五个级别
    """构造只有五个级别方法的控制台垫片。"""
    return 控制台垫片(缓冲)#垫片

def 捕获流写入(缓冲,流):#把 write 改接到缓冲
    """把流的 write 改接到日志缓冲；可选回调在接纳后调用。返回恢复函数。"""
    原始=流.write#原槽
    def 写入(块,*其余):#替换 write
        """接纳一块并可选回调。"""
        文本=块 if type(块) is str else (块.decode('utf-8') if type(块) is bytes else str(块))#文本
        缓冲.压入(文本)#压入
        回调=None#可选回调
        for 项 in 其余[:2]:#后两个位置
            if callable(项):#函数即回调
                回调=项#记下
                break#找到
        if 回调 is not None:#有回调
            回调(None)#接纳后调用
        return True#Node 合同：返回真
    流.write=写入#换槽
    def 恢复():#还原
        """还原原来的 write。"""
        流.write=原始#还原
    return 恢复#恢复函数

def 输出上限片段(最大输出字节):#固定溢出片段
    """构造不携带被拒可变字节的固定溢出片段。"""
    return {'error':{'kind':'output-limit','message':'outer output exceeded '+str(最大输出字节)+' bytes'}}#固定诊断

def 准备失败(种类,消息,剩余输出字节,最大输出字节):#有界失败或改报溢出
    """接纳一条有界失败消息，放不下则改成固定溢出诊断。"""
    if json字符串字节上限(消息,剩余输出字节) is None:#放不下
        return 输出上限片段(最大输出字节)#溢出
    return {'error':{'kind':种类,'message':消息}}#失败片段

def 准备完成(值,剩余输出字节,最大输出字节=None):#完成值进 done
    """只让无损 JSON 过线；放不下则报 output-limit。值为程序完成值。"""
    if 最大输出字节 is None:#缺省用剩余
        最大输出字节=剩余输出字节#同值
    if 值 is None:#Python 无 undefined；None 当缺席完成
        return {}#空片段
    try:#快照
        快照=快照ptcjson值(值)#分离
    except (节点ptc错误,TypeError,ValueError):#快照失败
        快照=None#非法
    if 快照 is None:#有损
        return 准备失败('invalid-output','program completion must be lossless JSON',剩余输出字节,最大输出字节)#有损
    if json值字节上限(快照,剩余输出字节) is None:#放不下
        return 输出上限片段(最大输出字节)#溢出
    return {'value':编码ptcjson线(快照)}#完成值

def 准备异常(错误,剩余输出字节,最大输出字节=None):#抛出值进 done
    """把程序抛出值收成有界 exception，不传无界栈。"""
    if 最大输出字节 is None:#缺省
        最大输出字节=剩余输出字节#同值
    try:#渲染
        if isinstance(错误,BaseException):#异常
            细节=错误#原样 str 含类型与消息
            消息=str(细节) if type(细节) is not str else 细节#字符串
        else:#非异常
            消息=错误 if type(错误) is str else str(错误)#强制转
    except (节点ptc错误,TypeError,ValueError):#不可渲染
        消息='program threw an unrenderable value'#固定标签
    return 准备失败('exception',消息,剩余输出字节,最大输出字节)#失败片段

def 定义绑定错误字段(错误,键,值):#一个公开字段
    """不咨询可变全局地写下绑定错误的一个公开字段。"""
    捕获定义属性(错误,键,值)#写下

def 制作绑定错误类(描述):#一个命名空间的拒绝类
    """物化命名空间声明的错误构造器。描述含 name 与 memberNameProperty。"""
    类名=描述['name']#程序可见类名
    成员属性=描述['memberNameProperty']#成员名属性
    class 绑定调用错误(捕获错误):#该类
        """一次绑定调用的拒绝。"""
        def __init__(自身,成员名,消息):#记下
            """用英文消息与成员名构造。"""
            捕获错误.__init__(自身,消息)#消息
            定义绑定错误字段(自身,'name',类名)#错误名
            定义绑定错误字段(自身,成员属性,成员名)#成员
    绑定调用错误.__name__=类名#类名
    return 绑定调用错误#构造器

def 绑定失败(错误类,成员名,消息):#一次失败
    """按命名空间构造拒绝；无类则普通错误。"""
    if 错误类 is not None:#有类
        return 错误类(成员名,消息)#专用
    return 捕获错误(消息)#普通

def 制作绑定错误类表(数据):#每个声明一次
    """按命名空间全局键控构造器，调用与 instanceof 共用身份。"""
    类表={}#全局到构造器
    for 命名空间 in 数据['namespaces']:#逐个
        if 'errorClass' not in 命名空间 or 命名空间['errorClass'] is None:#无类
            continue#跳过
        类表[命名空间['global']]=制作绑定错误类(命名空间['errorClass'])#记下
    return 类表#表

def 接线回复(端口,未决):#把回复接到未决表
    """每个回复最多结算一次调用；未知 id 忽略。未决是 id 到任务。"""
    def 收到(消息):#一条回复
        """结算对应调用。"""
        if 'id' not in 消息:#无 id
            return#忽略
        项=未决.pop(消息['id'],None)#取出
        if 项 is None:#未知或重复
            return#忽略
        if 消息['ok'] is True:#成功
            值=解码ptcjson线(消息['value'])#重建
            if 值 is None:#有损
                项.拒绝(捕获错误('binding resolution must be lossless JSON'))#拒绝
            else:#无损
                项.兑现(值)#兑现
        else:#失败
            项.拒绝(捕获错误(消息['message']))#拒绝
    端口.监听('message',收到)#挂上

def 制作命名空间(数据,端口,未决,下一标识,错误类表=None):#程序可见绑定
    """每个声明一个空原型全局；每个名字是自有可枚举函数，经端口桥接。"""
    if 错误类表 is None:#缺省
        错误类表=制作绑定错误类表(数据)#建造
    结果=[]#按声明顺序
    for 命名空间 in 数据['namespaces']:#逐个
        错误类=错误类表[命名空间['global']] if 命名空间['global'] in 错误类表 else None#该类
        对象=捕获对象创建()#空对象
        全局名=命名空间['global']#全局
        for 名字 in 命名空间['names']:#每个绑定名
            def 调用(参数,绑定名=名字,所属全局=全局名,所属错误类=错误类):#一次调用
                """有损参数在发送前拒绝；宿主失败只拒绝本次。"""
                try:#快照参数
                    分离=快照ptcjson值(参数)#分离
                except (节点ptc错误,TypeError,ValueError):#失败
                    分离=None#非法
                if 分离 is None:#有损
                    raise 绑定失败(所属错误类,绑定名,'binding arguments must be lossless JSON')#拒绝
                完成=任务()#本次
                标识=下一标识['value']#当前 id
                下一标识['value']=标识+1#推进
                未决[标识]=完成#登记
                try:#发调用
                    端口.发消息({'type':'call','id':标识,'global':所属全局,'name':绑定名,'args':编码ptcjson线(分离)})#调用帧
                except (节点ptc错误,OSError,ValueError,TypeError) as 错误:#发送失败
                    未决.pop(标识,None)#摘掉
                    文案='binding arguments must be structured-cloneable: '+(错误.args[0] if isinstance(错误,捕获错误) and len(错误.args)>0 else str(错误))#文案
                    raise 绑定失败(所属错误类,绑定名,文案)#拒绝
                try:#等回复
                    return 完成.等待()#宿主值
                except 捕获错误 as 错误:#宿主失败
                    raise 绑定失败(所属错误类,绑定名,str(错误))#包装
            对象[名字]=调用#挂上
        结果.append(对象)#收下
    return 结果#各命名空间

def 运行程序(端口,数据,流):#跑一个程序体并恰好发一条 done
    """跑一段程序体，顶层可有返回；恰好发送一条终态完成帧。流含 stdout 与 stderr。"""
    缓冲=日志缓冲(数据['maxOutputBytes'],lambda 文本:端口.发消息({'type':'log','text':文本}),lambda:端口.发消息({'type':'output-limit'}))#日志
    捕获流写入(缓冲,流['stdout'])#标准输出
    捕获流写入(缓冲,流['stderr'])#标准错误
    未决={}#调用 id 表
    接线回复(端口,未决)#回复
    下一标识={'value':1}#从 1 起
    错误类表=制作绑定错误类表(数据)#错误类
    空间列表=制作命名空间(数据,端口,未决,下一标识,错误类表)#绑定
    错误类参数=[]#注入类名
    错误类值=[]#注入构造器
    for 命名空间 in 数据['namespaces']:#逐个
        if 'errorClass' not in 命名空间 or 命名空间['errorClass'] is None:#无类
            continue#跳过
        错误类参数.append(命名空间['errorClass']['name'])#类名
        全局名=命名空间['global']#全局
        if 全局名 not in 错误类表:#缺失
            raise 捕获错误('missing binding error class for '+全局名)#自相矛盾
        错误类值.append(错误类表[全局名])#构造器
    控制台=制作控制台垫片(缓冲)#垫片
    参数名=[]#形参
    for 命名空间 in 数据['namespaces']:#全局形参
        参数名.append(命名空间['global'])#名字
    参数名.extend(错误类参数)#错误类
    参数名.append('console')#控制台
    实参=[]#实参
    实参.extend(空间列表)#命名空间
    实参.extend(错误类值)#错误类
    实参.append(控制台)#控制台
    try:#求值
        源='def 程序('+','.join(参数名)+'):\n'#函数头
        体=数据['code']#程序体
        if 体=='':#空体
            源+='    return None\n'#空返回
        else:#有体
            for 行 in 体.split('\n'):#逐行缩进
                源+='    '+行+'\n'#函数体
        盒={}#局部
        exec(源,{'__builtins__':__builtins__},盒)#编译
        值=盒['程序'](*实参)#执行
        完成={'type':'done'}#终态
        完成.update(准备完成(值,缓冲.剩余输出字节(),数据['maxOutputBytes']))#完成值
    except BaseException as 错误:#程序失败
        完成={'type':'done'}#终态
        完成.update(准备异常(错误,缓冲.剩余输出字节(),数据['maxOutputBytes']))#异常
    端口.发消息(完成)#恰好一条
