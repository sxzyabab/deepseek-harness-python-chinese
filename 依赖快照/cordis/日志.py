"""日志门面、日志服务、消息、导出器与格式化类型。"""
import json,math,time,weakref
from cosmokit import 定义属性,连字符化#导入属性定义与连字符化
from .工具 import 符号,创建可调用#导入符号与可调用包装

class 日志级别:
    """导出器决定是否发出消息时使用的数字严重级别。"""
    错误=0#错误
    信息=1#信息
    警告=2#警告
    调试=3#调试

LoggerLevel=日志级别#英文别名
日志级别.ERROR=0#英文别名
日志级别.INFO=1#英文别名
日志级别.WARN=2#英文别名
日志级别.DEBUG=3#英文别名

def 默认格式化字符串(值,导出器=None,消息=None):
    """字符串化。"""
    return str(值)#字符串

def 默认格式化整数(值,导出器=None,消息=None):
    """截断为整数。"""
    return math.trunc(float(值))#截断

def 默认格式化浮点(值,导出器=None,消息=None):
    """转成数字。"""
    return float(值)#数字

def 默认格式化对象(值,导出器=None,消息=None):
    """JSON 序列化。"""
    try:
        return json.dumps(值,default=str)#序列化
    except Exception:
        return str(值)#失败则字符串化

def 默认格式化颜色(值,导出器,消息):
    """按日志器名着色。"""
    return 日志器.着色(导出器,日志器.色号(消息.get('name'),导出器.get('colors') if isinstance(导出器,dict) else getattr(导出器,'colors',None)),值)#着色

默认格式化器={
    's':默认格式化字符串,#字符串
    'd':默认格式化整数,#整数
    'i':默认格式化整数,#整数
    'f':默认格式化浮点,#浮点
    'o':默认格式化对象,#对象
    'O':默认格式化对象,#对象
    'c':lambda 值,导出器=None,消息=None:'',#丢弃 CSS
    'C':默认格式化颜色,#按名着色
}#默认格式化器

色板16=[6,2,3,4,5,1]#青绿黄蓝品红红
色板256=[
    20,21,26,27,32,33,38,39,40,41,42,43,44,45,56,57,62,
    63,68,69,74,75,76,77,78,79,80,81,92,93,98,99,112,113,
    129,134,135,148,149,160,161,162,163,164,165,166,167,168,
    169,170,171,172,173,178,179,184,185,196,197,198,199,200,
    201,202,203,204,205,206,207,208,209,214,215,220,221,
]#256 色板

c16=色板16#英文别名
c256=色板256#英文别名
defaultFormatters=默认格式化器#英文别名

def 是否聚合错误(错误):
    """带 errors 数组的 Error 视为聚合错误。"""
    return isinstance(错误,Exception) and isinstance(getattr(错误,'errors',None),list)#聚合

class 日志器:
    """某一具名子系统的日志门面。"""
    @staticmethod
    def 着色(导出器,码,值,装饰=''):
        """导出器启用颜色时，用 ANSI 序列包裹 value。"""
        色深=导出器.get('colors') if isinstance(导出器,dict) else getattr(导出器,'colors',None)#色深
        if not 色深:
            return ''+str(值)#未启用颜色
        前=str(码) if 码<8 else '8;5;'+str(码)#16 色或 256 色
        装饰段=装饰 if (色深 if isinstance(色深,int) else 0)>=2 else ''#额外 SGR
        return '\u001b[3'+前+装饰段+'m'+str(值)+'\u001b[0m'#着色

    @staticmethod
    def 色号(名称,级别=None):
        """把 name 散列成稳定的调色板下标。"""
        散列=0#累加器
        for 字符 in 名称:
            散列=((散列<<3)-散列)+ord(字符)+13#多项式散列
            散列=散列 & 0xffffffff#截成 32 位
            if 散列>=0x80000000:
                散列-=0x100000000#有符号
        if not 级别:
            色板=[]#无色
        elif 级别>=2:
            色板=色板256#256 色
        else:
            色板=色板16#16 色
        if not 色板:
            return None#空调色板
        return 色板[abs(散列)%len(色板)]#映射下标

    @staticmethod
    def 格式化(导出器,消息):
        """用 printf 占位符格式化记录，再追加剩余参数。"""
        参数=list(消息.get('args') if isinstance(消息,dict) else 消息.args)#拷贝参数
        if 参数 and isinstance(参数[0],Exception):
            原错=参数[0]#原错误
            import traceback as 追踪#格式化异常栈
            参数[0]=''.join(追踪.format_exception(type(原错),原错,原错.__traceback__)) if 原错.__traceback__ else str(原错)#栈或消息
            参数.insert(0,'%s')#按字符串占位符
        elif not 参数 or not isinstance(参数[0],str):
            参数.insert(0,'%o')#按对象占位符
        格式=参数.pop(0)#取出格式串
        自定义=导出器.get('formatters') if isinstance(导出器,dict) else getattr(导出器,'formatters',None)#自定义
        import re as 正则#占位符替换
        def 替换(匹配):
            """替换一个占位符。"""
            全文=匹配.group(0)#全文
            字符=匹配.group(1)#字符
            if 全文=='%%':
                return '%'#转义百分号
            格式化=None#格式化器
            if 自定义 and 字符 in 自定义:
                格式化=自定义[字符]#自定义优先
            else:
                格式化=默认格式化器.get(字符)#内建
            if callable(格式化):
                值=参数.pop(0) if 参数 else None#消耗一个参数
                return str(格式化(值,导出器,消息))#输出片段
            return 全文#不认识则原样保留
        格式=正则.sub(r'%([a-zA-Z%])',替换,格式)#占位符替换
        对象格式化=(自定义 or {}).get('o') if 自定义 else 默认格式化器['o']#剩余对象
        if not 对象格式化:
            对象格式化=默认格式化器['o']#内建
        for 项 in 参数:
            if 项 is not None and isinstance(项,(dict,list)):
                项=对象格式化(项,导出器,消息)#序列化
            格式+=' '+str(项)#空格拼接
        上限=导出器.get('maxLength') if isinstance(导出器,dict) else getattr(导出器,'maxLength',None)#行长
        if 上限 is None:
            上限=10240#默认
        行表=[]#截断后的行
        for 行 in 格式.splitlines():
            if len(行)>上限:
                行表.append(行[:上限]+'...')#截断
            else:
                行表.append(行)#原行
        return '\n'.join(行表)#按原换行拼回

    def __init__(自身,选项,服务):
        """把本门面绑到 service，并安装四个严重级别方法。"""
        自身.name=选项.get('name')#名称
        自身.meta=选项.get('meta')#继承元数据
        自身.level=选项.get('level')#默认阈值
        自身._服务=服务#日志服务
        自身.error=自身._方法('error',日志级别.错误)#error
        自身.info=自身._方法('info',日志级别.信息)#info
        自身.warn=自身._方法('warn',日志级别.警告)#warn
        自身.debug=自身._方法('debug',日志级别.调试)#debug

    def _方法(自身,类型名,级别):
        """构造一个严重级别方法。"""
        def 方法(*位置参数):
            """展开单错误后发给每一个导出器。"""
            参数=list(位置参数)#拷贝
            if len(参数)==1 and isinstance(参数[0],Exception):
                原因=getattr(参数[0],'__cause__',None)#cause
                if 原因 is not None:
                    方法(原因)#先记原因
                elif 是否聚合错误(参数[0]):
                    for 子 in 参数[0].errors:
                        方法(子)#逐条递归
                    return#不再输出聚合本身
            自身._服务._消息序号+=1#分配序号
            序号=自身._服务._消息序号#消息序号
            时刻=int(time.time()*1000)#纪元毫秒
            for 导出器 in 自身._服务.exporters.values():
                阈值表=getattr(导出器,'levels',None) or (导出器.get('levels') if isinstance(导出器,dict) else None)#阈值表
                目标=None#本条阈值
                if 阈值表:
                    目标=阈值表.get(自身.name)#名阈值
                    if 目标 is None:
                        目标=阈值表.get('default')#默认阈值
                if 目标 is None:
                    目标=自身.level#门面阈值
                if 目标 is None:
                    目标=日志级别.信息#INFO
                if 目标<级别:
                    continue#跳过
                消息={'sn':序号,'ts':时刻,'type':类型名,'level':级别,'name':自身.name,'args':参数}#记录
                if 自身.meta:
                    消息.update(自身.meta)#合并固定字段
                if isinstance(导出器,dict):
                    导出器['export'](消息)#字典导出器
                else:
                    导出器.export(消息)#对象导出器
        return 方法#级别方法

    color=着色#英文别名
    code=色号#英文别名
    format=格式化#英文别名

Logger=日志器#英文别名

class 日志服务:
    """内建日志服务。调用 ctx.logger() 创建具名日志器。"""
    def __init__(自身,ctx):
        """安装带环形缓冲导出器的可调用日志服务。"""
        自身.ctx=ctx#所属上下文
        自身._追踪器={'property':'ctx','noShadow':True}#追踪器
        自身.bufferSize=1000#默认缓冲容量
        自身.buffer=[]#环形缓冲
        自身._消息序号=0#消息序号
        自身._导出器序号=0#导出器序号
        自身.exporters={}#序号到导出器
        自身._snMessage=自身._消息序号#英文别名字段同步
        def 导出(消息):
            """追加最新记录并截断。"""
            自身.buffer.append(消息)#追加
            if len(自身.buffer)>自身.bufferSize:
                自身.buffer=自身.buffer[-自身.bufferSize:]#只保留末尾
        自身.exporter({'colors':3,'export':导出})#内建缓冲导出器

    def __call__(自身,名称=None):
        """创建具名日志门面。"""
        return 自身._调用(名称)#调用体

    def exporter(自身,导出器):
        """登记导出器，并随当前光纤释放。"""
        def 执行体():
            """分配序号并登记。"""
            自身._导出器序号+=1#分配
            序号=自身._导出器序号#本序号
            自身.exporters[序号]=导出器#登记
            def 释放():
                """按当前序号删除。"""
                自身.exporters.pop(序号,None)#删除
            return 释放#释放器
        return 自身.ctx.effect(执行体,'ctx.logger.exporter()')#副作用

    def _解析配置(自身):
        """从当前拦截表上溯合并 logger 配置。"""
        拦截=自身.ctx.__dict__.get(符号.拦截) or {}#拦截表
        配置列表=[]#从根到叶
        if 'logger' in 拦截:
            配置列表.append(拦截['logger'])#本层
        结果={}#浅合并
        for 项 in 配置列表:
            if isinstance(项,dict):
                结果.update(项)#合并
        return 结果#拦截配置

    def _调用(自身,名称=None):
        """创建具名日志门面。"""
        配置=自身._解析配置()#合并拦截配置
        上下文对象=自身.ctx#当前上下文
        阴影=上下文对象.__dict__.get(符号.阴影)#来源阴影
        光纤对象=(阴影 if 阴影 is not None else 上下文对象).fiber#优先用来源光纤
        if 名称 is None:
            名称=配置.get('name')#拦截默认名
        if 名称 is None:
            名称=连字符化(光纤对象.名称)#光纤显示名
        return 日志器({'name':名称,'level':配置.get('level'),'meta':{'fiber':weakref.ref(光纤对象)}},自身)#绑到本服务

    def error(自身,*位置参数):
        """委托给具名门面的 error。"""
        return 自身().error(*位置参数)#先调用服务

    def info(自身,*位置参数):
        """委托给具名门面的 info。"""
        return 自身().info(*位置参数)#先调用服务

    def warn(自身,*位置参数):
        """委托给具名门面的 warn。"""
        return 自身().warn(*位置参数)#先调用服务

    def debug(自身,*位置参数):
        """委托给具名门面的 debug。"""
        return 自身().debug(*位置参数)#先调用服务

LoggerService=日志服务#英文别名
