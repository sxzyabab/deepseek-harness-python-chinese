"""Node 控制台日志导出器，用检查器格式化对象。"""
import os,sys,time
from cosmokit import 时间#时间模板与差值
from schemastery import 模式#配置模式
from cordis import 日志器#日志着色与格式化

def 取标准出色深():
    """按 supports-color 规则检测 stdout 色深。"""
    环境=os.environ#进程环境
    强制=环境.get('FORCE_COLOR')#强制色深
    if 强制 in ('0','false'):
        return 0#关闭
    if 环境.get('NO_COLOR') or 环境.get('NODE_DISABLE_COLORS') or 环境.get('TERM')=='dumb':
        if 强制 is None:
            return 0#禁用
    if 强制 is not None:
        if 强制 in ('','true','1'):
            return 1#基本色
        if 强制=='2':
            return 2#256 色
        if 强制=='3':
            return 3#真彩
        return 1#其它强制值当基本色
    if 环境.get('CI') and (环境.get('GITHUB_ACTIONS') or 环境.get('GITLAB_CI') or 环境.get('TRAVIS') or 环境.get('CIRCLECI')):
        return 1#CI 基本色
    if not sys.stdout.isatty():
        return 0#非 TTY
    if 环境.get('COLORTERM') in ('truecolor','24bit'):
        return 3#真彩
    终端=环境.get('TERM') or ''#终端类型
    if '256' in 终端 or 终端=='xterm-kitty':
        return 2#256 色
    return 1#基本色

def 检查格式化(值,目标,消息=None):
    """按 Node util.inspect 的紧凑无限深度选项格式化对象。"""
    色深=目标.get('colors') if isinstance(目标,dict) else getattr(目标,'colors',None)#色深
    启用=bool(色深)#是否着色
    已见=set()#循环检测
    def 上色(样式,文本):
        """按 Node inspect 样式包裹 ANSI。"""
        if not 启用:
            return 文本#无色
        表={'数字':('33','39'),'布尔':('33','39'),'空':('1','22'),'字符串':('32','39'),'无':('90','39'),'特殊':('36','39')}#样式码
        起,止=表[样式]#起止码
        return '\x1b['+起+'m'+文本+'\x1b['+止+'m'#着色文本
    def 走(项):
        """递归检查一项。"""
        标识=id(项)#对象身份
        if isinstance(项,(dict,list,tuple,set)):
            if 标识 in 已见:
                return 上色('特殊','[Circular]')#循环引用
            已见.add(标识)#进入
        if isinstance(项,bool):
            结果=上色('布尔',str(项))#布尔
        elif 项 is None:
            结果=上色('空','None')#空值
        elif isinstance(项,(int,float)):
            结果=上色('数字',repr(项))#数字
        elif isinstance(项,str):
            结果=上色('字符串',repr(项))#字符串
        elif isinstance(项,dict):
            片段=[]#字段
            for 键,子 in 项.items():
                片段.append(走(键)+': '+走(子))#键值
            结果='{'+', '.join(片段)+'}'#对象
        elif isinstance(项,list):
            结果='['+', '.join(走(子) for 子 in 项)+']'#数组
        elif isinstance(项,tuple):
            if len(项)==1:
                结果='('+走(项[0])+',)'#单元素元组
            else:
                结果='('+', '.join(走(子) for 子 in 项)+')'#元组
        elif isinstance(项,set):
            if not 项:
                结果='set()'#空集合
            else:
                结果='{'+', '.join(走(子) for 子 in 项)+'}'#集合
        else:
            结果=repr(项)#其它
        if isinstance(项,(dict,list,tuple,set)):
            已见.discard(标识)#离开
        return 结果#片段
    return 走(值)#根对象

class 控制台导出器:
    """带检查器对象格式化的 Node 控制台导出器。"""
    name='logger-console'#插件名
    Config=模式.对象({
        'colors':模式.联合([模式.常量(False),模式.数字()]),#色深
        'maxLength':模式.数字(),#行长
        'levels':模式.字典(模式.数字()),#阈值表
        'showDiff':模式.布尔().默认(False),#显示间隔
        'showTime':模式.字符串().默认('yyyy-MM-dd hh:mm:ss '),#时间模板
        'label':模式.对象({
            'width':模式.数字(),#列宽
            'margin':模式.数字(),#边距
            'align':模式.联合(['left','right']),#对齐
        }),#名称标签
    })#配置模式

    def __init__(自身,ctx,配置=None):
        """把默认项与配置写到实例上，登记检查器并挂到日志服务。"""
        自身.formatters={'o':检查格式化,'O':检查格式化}#对象占位符
        if 配置 is None:
            配置={}#空配置
        合并=dict(自身.取默认())#默认项
        合并.update(配置)#配置覆盖
        for 键,值 in 合并.items():
            setattr(自身,键,值)#写入字段
        自身.timestamp=int(time.time()*1000)#当前毫秒
        ctx.logger.exporter(自身)#登记导出器

    def 取默认(自身):
        """带终端色深的默认配置。"""
        return {
            'colors':取标准出色深(),#stdout 色深
            'showTime':'yyyy-MM-dd hh:mm:ss ',#时间模板
            'showDiff':False,#不显示间隔
        }#默认配置

    def 导出(自身,消息):
        """把渲染结果打印到控制台。"""
        print(自身.渲染(消息))#打印一行

    def 渲染(自身,消息):
        """把记录收成控制台文本。"""
        前缀='['+消息['type'][0].upper()+']'#级别前缀
        标签=getattr(自身,'label',None) or {}#标签样式
        边距=标签.get('margin')#标签边距
        if 边距 is None:
            边距=1#默认边距
        空格=' '*边距#间隔空格
        缩进=3+len(空格)#续行缩进
        输出=''#行缓冲
        if 自身.showTime:
            缩进+=len(自身.showTime)#加上时间宽度
            输出+=日志器.着色(自身,8,时间.模板(自身.showTime))#着色时间
        色号=日志器.色号(消息['name'],自身.colors)#名称色号
        名称标签=日志器.着色(自身,色号,消息['name'],'1')#加粗名称
        宽度=标签.get('width')#标签列宽
        if 宽度 is None:
            宽度=0#缺省列宽
        填充=宽度+len(名称标签)-len(消息['name'])#含转义的填充
        if 标签.get('align')=='right':
            输出+=名称标签.rjust(填充)+空格+前缀+空格#右对齐名称
            缩进+=宽度+len(空格)#加上标签列
        else:
            输出+=前缀+空格+名称标签.ljust(填充)+空格#左对齐名称
        输出+=日志器.格式化(自身,消息).replace('\n','\n'+' '*缩进)#续行缩进
        if 自身.showDiff and 自身.timestamp:
            间隔=消息['ts']-自身.timestamp#间隔毫秒
            输出+=日志器.着色(自身,色号,' +'+时间.格式化(间隔))#着色间隔
        自身.timestamp=消息['ts']#记住时刻
        return 输出#整行

