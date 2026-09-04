import os,sys,time
from .工具 import 时间
from .schemastery import 复合类型字段,常量字段,数字字段,字典字段,布尔字段,字符串字段,枚举字段#配置字段
from .cordis import 日志器

def 探测终端色深():
    """按环境变量与终端类型探测标准输出支持的色深。"""
    环境变量=os.environ#进程环境
    #启用配置优先于禁用配置
    强制=环境变量.get('FORCE_COLOR') or 环境变量.get('使用色深')#强制指定的色深
    if 强制 is not None:
        return {
            '0':0,
            'false':0,
            '':1,
            'true':1,
            '1':1,
            '2':2,
            '3':3
            }.get(强制.lower(),1)
    if 环境变量.get('禁用色彩') or 环境变量.get('NO_COLOR') or \
        环境变量.get('NODE_禁用色彩') or 环境变量.get('NODE_DISABLE_COLORS') or \
        环境变量.get('终端')=='dumb' or 环境变量.get('TERM')=='dumb':#dumb是非智能终端
        return 0#显式禁用
    #重定向到文件就不着色,但环境配置优先
    if not sys.stdout.isatty():
        return 0
    #CI环境
    if 环境变量.get('CI') and any(
        环境变量.get(键)
        for 键 in (#这些 CI 的日志面板认基本色
            'GITHUB_ACTIONS','GITLAB_CI','TRAVIS','CIRCLECI'
            )):
        return 1
    #真彩终端
    if 环境变量.get('COLORTERM') in ('truecolor','24bit'):
        return 3
    终端=环境变量.get('终端') or 环境变量.get('TERM') or ''#终端类型
    if '256' in 终端 or 终端=='xterm-kitty':
        return 2#256色
    return 1#基本色

_检查样式={
    '数字':('33','39'),
    '布尔':('33','39'),
    '空':('1','22'),
    '字符串':('32','39'),
    '循环':('36','39')
    }#检查器着色

def 展开对象(值,导出器,消息=None):
    "把对象展开成一行带颜色的可读文本，循环引用就地标出"
    着色=bool(getattr(导出器,'色深',None))#是否着色
    路径上的容器=set()#当前递归路径上的容器身份
    def 上色(样式,文本):
        "按检查器样式包一层 ANSI"
        if not 着色:
            return 文本#不着色
        起,止=_检查样式[样式]#起止码
        return f'\x1b[{起}m{文本}\x1b[{止}m'#着色文本
    def 展开(项):
        "递归展开一项"
        if isinstance(项,bool):
            return 上色('布尔',str(项))#布尔要排在数字前面
        if 项 is None:
            return 上色('空','None')#空值
        if isinstance(项,(int,float)):
            return 上色('数字',repr(项))#数字
        if isinstance(项,str):
            return 上色('字符串',repr(项))#字符串
        if not isinstance(项,(dict,list,tuple,set)):
            return repr(项)#其它对象交给它自己的展示
        身份=id(项)#容器身份
        if 身份 in 路径上的容器:
            return 上色('循环','[循环引用]')#回到了路径上的容器
        路径上的容器.add(身份)#进入
        try:
            return _展开容器(项,展开)#展开容器
        finally:
            路径上的容器.discard(身份)#离开
    return 展开(值)#根对象

def _展开容器(项,展开):
    "按容器种类拼出它的字面量文本"
    if isinstance(项,dict):
        return '{'+', '.join(f'{展开(键)}: {展开(子)}' for 键,子 in 项.items())+'}'#映射
    if isinstance(项,list):
        return '['+', '.join(展开(子) for 子 in 项)+']'#列表
    if isinstance(项,tuple):
        if len(项)==1:
            return '('+展开(项[0])+',)'#单元素元组要带逗号
        return '('+', '.join(展开(子) for 子 in 项)+')'#元组
    if not 项:
        return 'set()'#空集合没有字面量写法
    return '{'+', '.join(展开(子) for 子 in 项)+'}'#集合

class 控制台导出器:
    "把日志渲染成一行控制台文本的导出器"
    插件名='logger-console'#插件显示名
    配置模式={
        'colors':复合类型字段(常量字段(False),数字字段()),#色深，False 表示不着色
        'maxLength':数字字段(),#单行长度上限
        'levels':数字字段(),#按日志器名指定的阈值
        'showDiff':布尔字段(默认值=False),#是否显示与上一条的间隔
        'showTime':字符串字段(默认值='yyyy-MM-dd hh:mm:ss '),#时间模板，空串表示不显示
        'label':{
            'width':数字字段(),#名称列宽
            'margin':数字字段(),#名称两侧的空格数
            'align':枚举字段('left','right'),#名称对齐方向
        },#名称标签样式
    }#配置模式

    def __init__(自身,上下文,配置=None):
        "按配置装配渲染参数并把自己登记成日志导出器"
        配置=配置 or {}#空配置
        色深=配置.get('colors')#配置里指定的色深
        自身.色深=探测终端色深() if 色深 is None else (色深 or 0)#False 与 0 都表示不着色
        自身.行长上限=配置.get('maxLength')#单行长度上限
        自身.阈值表=配置.get('levels') or {}#按日志器名指定的阈值
        自身.显示间隔=bool(配置.get('showDiff'))#是否显示与上一条的间隔
        自身.时间模板=配置.get('showTime','yyyy-MM-dd hh:mm:ss ')#时间模板
        自身.标签样式=配置.get('label') or {}#名称标签样式
        自身.格式化器表={'o':展开对象,'O':展开对象}#对象占位符改用检查器展开
        自身.上次时刻=int(time.time()*1000)#上一条消息的时刻
        上下文.日志.登记导出器(自身)#登记导出器

    def 导出(自身,消息):
        "把渲染结果打印到控制台"
        print(自身.渲染(消息))#打印一行

    def 渲染(自身,消息):
        "把一条记录收成整行控制台文本"
        间隔空格=' '*自身.标签样式.get('margin',1)#名称两侧的空格
        缩进=3+len(间隔空格)#续行缩进，先算上级别前缀
        输出=''#行缓冲
        if 自身.时间模板:
            缩进+=len(自身.时间模板)#加上时间列
            输出+=日志器.着色(自身,8,时间.格式化时间(自身.时间模板))#灰色时间
        色号=日志器.色号(消息.名称,自身.色深)#该日志器名的颜色
        名称标签=日志器.着色(自身,色号,消息.名称,'1')#加粗名称
        列宽=自身.标签样式.get('width',0)+len(名称标签)-len(消息.名称)#含 ANSI 转义的列宽
        前缀=f'[{消息.标记}]'#级别前缀
        if 自身.标签样式.get('align')=='right':
            输出+=名称标签.rjust(列宽)+间隔空格+前缀+间隔空格#名称在前且右对齐
            缩进+=自身.标签样式.get('width',0)+len(间隔空格)#加上名称列
        else:
            输出+=前缀+间隔空格+名称标签.ljust(列宽)+间隔空格#级别在前，名称左对齐
        输出+=日志器.格式化(自身,消息).replace('\n','\n'+' '*缩进)#续行对齐到正文列
        if 自身.显示间隔:
            输出+=日志器.着色(自身,色号,' +'+时间.格式化(消息.时刻-自身.上次时刻))#与上一条的间隔
        自身.上次时刻=消息.时刻#记住本条时刻
        return 输出#整行

默认=控制台导出器#模块的默认插件导出
