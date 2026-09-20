import os,re,sys,copy,json,threading#路径、环境、流、克隆、JSON、定时
from ...依赖 import cordis,include,loader
import yaml#外部依赖胶水（含 PyYAML）
上下文=cordis.上下文#上下文
纤程状态=cordis.纤程状态#纤程/纤程状态
包含=include.包含#Include
应用条目补丁=include.应用插件补丁#补丁应用
条目列表加载器=include.插件列表读取器#YAML 条目列表方言
路径转文件url=include.路径转文件url#路径转 url
组=loader.组#Group 内建
from ...工具.主目录路径 import 主目录路径,解析主目录#主目录
from ...工具.启动环境 import 创建启动环境快照#启动环境快照
from .配置档 import (#配置档再导出
    组合条目,默认组合包,愈合模块回退,初始化配置档,加载配置档,加载配置目录,
    配置补丁文件名,配置模板,配置目录名,读配置清单,解析组合包目录,
    解析配置目录,写配置清单,创建配置解析世代,可选组合包,
    愈合隔离配置模块回退,拆开配置模块回退,
)#再导出结束
from .配置解析.服务 import 插件包表#配置解析服务
from .配置档上下文 import 读配置档补丁,解析遥测补丁#配置档上下文
from .配置档插件 import 读配置插件,写配置组合包,对账配置插件#配置档插件
from .配置档清洗 import 清洗配置档#清洗

__all__=[#仅中文公开名
    '解析配置路径','加载环境','加载分层环境','加载可选补丁','加载覆盖补丁',
    '渲染配置转储','挂载根包含','安装大声失败','大声失败拆除超时毫秒',
    '断言条目已加载','断言条目已激活','启动','添加源码段落','源码段落名',
    '组合条目','默认组合包','可选组合包','愈合模块回退','初始化配置档','加载配置档','加载配置目录',
    '配置补丁文件名','配置模板','配置目录名','读配置清单','解析组合包目录',
    '解析配置目录','写配置清单','创建配置解析世代','插件包表','审计启动条目',
    '读配置档补丁','解析遥测补丁','读配置插件','写配置组合包','对账配置插件','清洗配置档',
    '愈合隔离配置模块回退','拆开配置模块回退','协调配置档补丁','启动错误',
]#公开面结束

#常量
源码段落名='harness:source'#源位置段落名
大声失败拆除超时毫秒=2000#拆除超时毫秒
纤程拆除=纤程状态.已拆除 if hasattr(纤程状态,'已拆除') else 4#已拆除
引导名精确=set([#引导专用名
    'PATH','HOME','USERPROFILE','SHELL',
    'NODE_OPTIONS','NODE_PATH','NODE_EXTRA_CA_CERTS',
    'LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT',
    'BASH_ENV','ENV','SHELLOPTS','BASHOPTS',
    'PERL5OPT','PERL5LIB','PYTHONSTARTUP','PYTHONPATH','RUBYOPT','RUBYLIB',
    'JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS','PYTHONHOME',
    'GIT_SSH','GIT_SSH_COMMAND','GIT_EXTERNAL_DIFF','GIT_PAGER','GIT_EDITOR',
    'GIT_ASKPASS','SSH_ASKPASS','GIT_CONFIG_GLOBAL','GIT_CONFIG_SYSTEM','GIT_CONFIG_COUNT',
    'EDITOR','VISUAL','PAGER','BROWSER',
    'DEEPSEEK_BASE_URL','DEEPSEEK_SEARCH_BASE_URL',
    'SSL_CERT_FILE','SSL_CERT_DIR',
    'HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY',
    'REQUESTS_CA_BUNDLE','CURL_CA_BUNDLE','NODE_TLS_REJECT_UNAUTHORIZED',
])#引导名结束
引导名前缀=['DSH_','XDG_','DYLD_','BASH_FUNC_']#引导专用前缀
主目录层代理名=set(['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY'])#主目录 .env 可设的代理名
启动包含表={}#根 Include 条目登记（ctx id → entry）
已组装拒绝={}#已组装激活拒绝计数

纤程等待=纤程状态.等待#等待中
纤程激活=纤程状态.已激活#已激活
纤程失败=纤程状态.失败#已失败

class 启动错误(Exception):
    """应用启动粘合层失败；可附带未激活条目元数据。"""

    def __init__(自身,消息,条目表=None):
        """记下消息与可选条目；失败 outcome 挂为 cause。"""
        条目表=条目表 if 条目表 is not None else []#条目
        失败值=[]#原失败
        for 项 in 条目表:#逐条
            结果=项.get('outcome') if isinstance(项,dict) else None#结果
            if isinstance(结果,dict) and 结果.get('kind')=='failed':#失败
                错=结果.get('error')#错误值
                if isinstance(错,BaseException):#异常
                    失败值.append(错)#收下
        if len(失败值)>0:#有原失败
            super().__init__(消息)#基类
            if len(失败值)==1:#单失败
                自身.__cause__=失败值[0]#挂上
            else:#多失败
                自身.__cause__=ExceptionGroup('Plugin activation failures',失败值)#聚合
        else:#无原失败
            super().__init__(消息)#基类
        自身.entries=条目表#条目
        自身.startup=None#启动日志切片

def 协调配置档补丁(上下文,补丁,二进制名,必需标识=None):
    """应用一整代补丁并等待 Loader 激活诊断。"""
    if 必需标识 is None:#缺省
        必需标识=[]#空
    键=id(上下文)#上下文身份
    if 键 not in 启动包含表:#缺少根 Include
        raise 启动错误(二进制名+': profile reload requires the root Include entry')#缺少
    条目=启动包含表[键]#根 Include
    先前失败=[dict(项,diagnostic=未激活诊断(项),fiber=项['entry'].纤程,options=json.dumps(项['entry'].选项,ensure_ascii=False,sort_keys=True,separators=(',',':'))) for 项 in 未激活条目(上下文)]#先前失败
    先前纤程=[]#先前纤程
    for 行 in 上下文.加载器.列出插件配置():#逐条
        if 行.纤程 is None:#无纤程
            continue#跳过
        先前纤程.append({'fiber':行.纤程,'failed':行.纤程.状态==纤程失败 or 行.纤程.状态==纤程拆除})#记下
    选项配置=条目.选项['config'] if 'config' in 条目.选项 else {}#当前配置
    非补丁={键名:值 for 键名,值 in 选项配置.items() if 键名!='patches'}#去掉旧补丁
    条目.更新({'config':{**非补丁,'patches':list(补丁)}})#事务更新
    for 项 in 先前纤程:#等旧纤程
        try:#等待
            项['fiber'].等待()#结算
        except Exception:#旧失败可忽略
            pass#吞掉既有失败
    加载器=上下文.获取服务('加载器',False)#Loader
    if 加载器 is not None:#仍在
        加载器.等待()#等结算
    失败=未激活条目(上下文)#新失败
    def 是否引入(项):
        """是否新的或已变失败。"""
        if 项['entry'].选项.get('id') in 必需标识:#显式必需
            return True#引入
        for 先前 in 先前失败:#比对
            if (先前['entry'] is 项['entry'] and 先前.get('fiber') is 项['entry'].纤程
                and 先前.get('options')==json.dumps(项['entry'].选项,ensure_ascii=False,sort_keys=True,separators=(',',':'))
                and 先前.get('diagnostic')==未激活诊断(项)):#未变
                return False#不是引入
        return True#引入
    引入=[项 for 项 in 失败 if 是否引入(项)]#新失败
    if len(引入)>0:#有引入
        raise 启动错误(激活诊断(二进制名,引入).rstrip())#拒绝
    return [未激活诊断(项) for 项 in 失败]#诊断文本

def 解析配置路径(配置路径,快照模式,工作目录=None):#解析启动配置路径
    """解析要启动的配置；回放时换基名为 cordis.snapshot.yml。"""
    if 工作目录 is None:#缺省
        工作目录=os.getcwd()#cwd
    绝对=os.path.abspath(os.path.join(工作目录,配置路径))#绝对路径
    if 快照模式!='replay':#非回放
        return 绝对#原样
    目录=os.path.dirname(绝对)#所在目录
    基名=os.path.basename(绝对)#基名
    回放名=re.sub(r'cordis\.ya?ml$','cordis.snapshot.yml',基名)#换成快照基名
    return os.path.join(目录,回放名)#回放配置

def 加载环境(二进制名,目录=None,警告=None):#加载单层 .env
    """从 dir 加载可选的 .env。"""
    if 目录 is None:#缺省
        目录=os.getcwd()#cwd
    if 警告 is None:#缺省
        def 写警告(行):
            """写标准错误。"""
            sys.stderr.write(行)#stderr
        警告=写警告#缺省警告
    路径=os.path.join(目录,'.env')#路径
    try:#读并应用
        应用环境文件(路径)#加载
    except FileNotFoundError:#缺失
        return#依赖已有环境
    except OSError as 错误:#其它读失败
        警告(二进制名+': failed to load .env: '+str(错误)+'\n')#报告

def 是否仅引导(名):#是否引导专用
    """变量是否只能来自继承的进程环境。"""
    大写=名.upper()#大写名
    if 大写 in 引导名精确:#精确名
        return True
    for 前缀 in 引导名前缀:#前缀
        if 大写.startswith(前缀):#命中
            return True
    return False#否

def 解析环境文本(内容):#解析 .env 文本
    """把 .env 文本解析成名→值映射（对齐 Node parseEnv 子集）。"""
    值表={}#条目
    for 行 in 内容.splitlines():#逐行
        修剪=行.strip()#修剪
        if 修剪=='' or 修剪.startswith('#'):#空或注释
            continue#跳过
        if 修剪.startswith('export '):#export 前缀
            修剪=修剪[7:].strip()#去掉
        if '=' not in 修剪:#无等号
            continue#跳过
        名,值=修剪.split('=',1)#拆开
        名=名.strip()#名
        值=值.strip()#值
        if (值.startswith('"') and 值.endswith('"')) or (值.startswith("'") and 值.endswith("'")):#引号
            值=值[1:-1]#去引号
        值表[名]=值#记下
    return 值表#条目

def 应用环境文件(路径):#把 .env 写入进程环境
    """读取路径上的 .env 并写入尚未继承的名字。"""
    文件=open(路径,'r',encoding='utf-8')#打开
    try:#读
        内容=文件.read()#文本
    finally:#关
        文件.close()#关闭
    for 名,值 in 解析环境文本(内容).items():#逐条目
        if 名 not in os.environ:#未继承
            os.environ[名]=值#写入

def 读环境层(二进制名,目录,警告,主目录):#读一层 .env
    """解析某目录的 .env 但不应用，拒绝引导专用名。主目录层可设代理名。"""
    路径=os.path.join(目录,'.env')#该层路径
    是主目录=os.path.abspath(目录)==主目录#是否主目录层
    try:#读文件
        文件=open(路径,'r',encoding='utf-8')#打开
        try:#读
            内容=文件.read()#文本
        finally:#关
            文件.close()#关闭
    except FileNotFoundError:#缺失
        return None#没有这一层
    except OSError as 错误:#其它
        警告(二进制名+': failed to load .env: '+str(错误)+'\n')#报告
        return None#不可读
    值表=解析环境文本(内容)#解析
    for 名 in 值表:#逐名检查
        if 是否仅引导(名):#引导名
            代理名=名.upper() in 主目录层代理名#是否代理
            if 是主目录 and 代理名:#主目录层放过代理
                continue#接受
            补救=('export '+名+', or put it in '+os.path.join(主目录,'.env')+', which does not travel with a repository'
                if 代理名 else 'export '+名+' instead of putting it in a .env file')#补救
            raise 启动错误(
                二进制名+': '+路径+' sets "'+名+'", which only the launching environment may set'
                +' (it decides how this process starts, where its code and instructions load from, or how it'
                +' reaches the network); '+补救
            )#错误
    return {'path':路径,'values':值表}#路径与条目

def 加载分层环境(二进制名,工作目录=None,警告=None):#加载分层环境
    """加载继承环境 > 调用目录 .env > Harness 主目录 .env 快照。"""
    if 工作目录 is None:#缺省
        工作目录=os.getcwd()#cwd
    if 警告 is None:#缺省
        def 写警告(行):
            """写标准错误。"""
            sys.stderr.write(行)#stderr
        警告=写警告#缺省警告
    主目录=解析主目录()#Harness 主目录
    继承=dict(os.environ)#继承环境副本
    项目=读环境层(二进制名,工作目录,警告,主目录)#项目层
    用户=None if 主目录==os.path.abspath(工作目录) else 读环境层(二进制名,主目录,警告,主目录)#用户层
    for 层 in (项目,用户):#按层应用
        if 层 is None:#缺失
            continue#跳过
        for 名,值 in 层['values'].items():#逐条目
            if 名 not in os.environ:#未继承
                os.environ[名]=值#写入
    各层=[{'source':'process','values':继承}]#继承层
    if 项目 is not None:#项目层
        各层.append({'source':'project-env','path':项目['path'],'values':项目['values']})#项目
    if 用户 is not None:#用户层
        各层.append({'source':'user-env','path':用户['path'],'values':用户['values']})#用户
    return 创建启动环境快照(各层)#冻结快照

def 解析补丁列表(二进制名,文件,内容,标签):#解析补丁列表
    """解析一份 loader 补丁列表。"""
    try:#解析 YAML
        解析=yaml.load(内容,Loader=条目列表加载器)#用 include 方言
    except yaml.YAMLError as 错误:#解析失败
        raise 启动错误(二进制名+': failed to parse '+标签+' '+文件+': '+str(错误))#包装
    if not isinstance(解析,list):#不是顶层数组
        raise 启动错误(二进制名+': '+标签+' '+文件+' must be a top-level YAML array of loader patch entries')#拒绝
    for 下标,条目 in enumerate(解析):#逐条检查
        if not isinstance(条目,dict) or 条目 is None:#不是映射
            raise 启动错误(二进制名+': '+标签+' entry '+str(下标+1)+' in '+文件+' must be a mapping (a loader patch entry)')#拒绝
    基=os.path.dirname(os.path.abspath(文件))#补丁目录
    def 访问(条目):
        """把插入条目里的文件系统路径改成 file URL。"""
        名=条目['name'] if 'name' in 条目 else None#插件名
        if isinstance(名,str) and (os.path.isabs(名) or 名.startswith('./') or 名.startswith('../')):#路径形
            条目['name']=路径转文件url(os.path.abspath(os.path.join(基,名)))#改 file URL
        if ('group' in 条目 and 条目['group']) and isinstance(条目['config'] if 'config' in 条目 else None,list):#组内条目
            for 子 in 条目['config']:#递归
                访问(子)#访问
    for 补丁 in 解析:#每条补丁
        if 'insert' in 补丁 and 补丁['insert'] is not None:#有插入
            for 条目 in 补丁['insert']:#逐条
                访问(条目)#改写
    return 解析#补丁列表

def 加载可选补丁(二进制名,文件):#加载可选补丁
    """文件缺失表示没有这一层；不可读或非法则抛。"""
    try:#读文件
        打开=open(文件,'r',encoding='utf-8')#打开
        try:#读
            内容=打开.read()#文本
        finally:#关
            打开.close()#关闭
    except FileNotFoundError:#缺失
        return None#没有这一层
    except OSError as 错误:#其它
        raise 启动错误(二进制名+': failed to read patches '+文件+': '+str(错误))#大声失败
    return 解析补丁列表(二进制名,文件,内容,'patches')#按 patches 标签

def 加载覆盖补丁(二进制名,文件):#加载必需覆盖补丁
    """文件缺失也失败。"""
    try:#读文件
        打开=open(文件,'r',encoding='utf-8')#打开
        try:#读
            内容=打开.read()#文本
        finally:#关
            打开.close()#关闭
    except OSError as 错误:#读失败
        raise 启动错误(二进制名+': failed to read overlay '+文件+': '+str(错误))#缺失也失败
    return 解析补丁列表(二进制名,文件,内容,'overlay')#按 overlay 标签

def 挂载根包含(上下文,绝对配置路径,补丁=None,裸模块基址=None):
    """挂上并记住应用启动使用的根 Include 条目。"""
    if 补丁 is None:#缺省
        补丁=[]#空
    if 裸模块基址 is None:#无宿主基址
        上下文.加载器.内建表['include']=包含#用原 Include
    else:#宿主解析
        class 宿主根包含(包含):
            """宿主解析根 Include。"""
            def 导入(自身,名称,获取外层栈=None):
                """改写导入。"""
                说明符=路径转文件url(名称) if os.path.isabs(名称) else 名称#绝对改 file URL
                if 名称.startswith('.') or 名称.startswith('cordis:'):#相对与内建
                    return super().导入(说明符,获取外层栈)#父类
                内部=自身.所属上下文.加载器.内部加载器#内部加载器
                if 内部 is None:#没有
                    return super().导入(说明符,获取外层栈)#父类
                return 内部.import_(说明符,裸模块基址,{})#宿主基址
        上下文.加载器.内建表['include']=宿主根包含#注册
    上下文.加载器.内建表['group']=组#注册 group 内建
    包含配置={'path':路径转文件url(绝对配置路径)}#根 include 配置
    if len(补丁)>0:#有补丁
        包含配置['patches']=list(补丁)#带上
    根条目={'id':'include','name':'cordis:include','config':包含配置}#根条目
    包含号=上下文.加载器.创建(根条目)#创建根条目，同步
    加载器=上下文.获取服务('加载器',False)#再取 Loader
    if 加载器 is None:#树已拆
        return None#返回
    条目=加载器.解析(包含号)#解析条目
    启动包含表[id(上下文)]=条目#登记
    return 条目#返回根条目

def 保留已组装拒绝(原因):
    """计数加一。"""
    if 原因 not in 已组装拒绝:#首条
        已组装拒绝[原因]=1#计数
    else:#已有
        已组装拒绝[原因]=已组装拒绝[原因]+1#加一

def 释放已组装拒绝(原因):
    """计数减一。"""
    if 原因 not in 已组装拒绝:#没有
        return#空
    数=已组装拒绝[原因]#当前
    if 数==1:#最后一条
        del 已组装拒绝[原因]#删掉
    else:#还有
        已组装拒绝[原因]=数-1#减一

def 安装大声失败(二进制名,进程=None,拆除=None):
    """把迟到的未处理插件初始化拒绝变成带标签诊断并 exit(1)。进程是 sys 模块。"""
    if 进程 is None:#缺省
        进程=sys#进程
    退出中=False#是否已决定退出
    def 处理器(错误类型,错误,回溯):
        """致命失败处理器。"""
        nonlocal 退出中#修改
        if 错误 in 已组装拒绝:#启动审计已计入
            return#忽略
        if 退出中:#已在退出
            return#吞掉
        退出中=True#闩上
        文本=二进制名+': fatal load failure: '+str(错误)+'\n'#诊断
        进程.stderr.write(文本)#先写诊断
        if 拆除 is None:#没有拆除
            进程.exit(1)#立刻退出
            return
        def 后台拆除():
            """等拆除或超时。"""
            完成=threading.Event()#完成事件
            def 执行拆除():
                """执行拆除。"""
                try:#拆除
                    拆除()#同步
                except Exception:#拆除抛错形态未钉死
                    pass#吞掉
                finally:#完成
                    完成.set()#放行
            threading.Thread(target=执行拆除,daemon=True).start()#启动
            完成.wait(大声失败拆除超时毫秒/1000.0)#到时放行
            进程.exit(1)#致命退出
        threading.Thread(target=后台拆除,daemon=True).start()#立即
    def 空卸载():
        """Python 无 unhandledRejection；保留 API 形状。"""
        return#空
    return 空卸载#卸载器

必需启动条目标识=set([#定义可用 DSH 应用的条目 id
    'agent-loop','webserver','modules','connection','headless-runner','acp','sdk-jsonrpc-server',
])#标识结束

def 格式化激活错误(错误):
    """展开插件栈、嵌套原因与聚合成员一次。"""
    细节=[]#行
    已见=set()#去环
    def 访问(值):
        """递归展开。"""
        if not isinstance(值,Exception):#非异常
            细节.append(str(值))#字符串
            return
        if 值 in 已见:#环
            return#停
        已见.add(值)#记下
        细节.append(str(值))#消息
        if 值.__cause__ is not None:#原因
            访问(值.__cause__)#下一层
        if hasattr(值,'exceptions'):#聚合
            for 成员 in 值.exceptions:#成员
                访问(成员)#展开
    访问(错误)#开始
    return '\n'.join(细节)#拼

def 未激活条目(上下文):
    """收集加载失败与禁用表达式错误。"""
    失败=[]#失败
    拒绝原因=[]#拒绝原因
    for 条目 in 上下文.加载器.列出插件配置():#逐条
        try:#读禁用
            if 条目.已禁用:#已禁用
                continue#跳过
        except Exception as 错误:#禁用表达式失败
            失败.append({'entry':条目,'outcome':{'kind':'failed','error':错误,'phase':'disabled expression failed'}})#记下
            continue#下一条
        纤程=条目.纤程#fiber
        if 纤程 is None:#无纤程
            失败.append({'entry':条目,'outcome':{'kind':'failed','error':'failed to import'}})#导入失败
            continue#下一条
        状态=纤程.状态#状态
        if 状态==纤程激活:#已激活
            continue#跳过
        if 状态==纤程失败:#已失败
            try:#收回原因
                纤程.等待()#等待
            except Exception as 错误:#插件启动失败
                拒绝原因.append(错误)#记下
                失败.append({'entry':条目,'outcome':{'kind':'failed','error':错误}})#格式化
            continue#下一条
        if 状态==纤程等待:#仍在等待
            缺失=[]#缺失服务
            for 服务名 in 纤程.依赖表:#依赖表
                if 纤程.所属上下文.获取服务(服务名,False) is None:#仍缺
                    缺失.append(服务名)#记下
            失败.append({'entry':条目,'outcome':{'kind':'pending','missing':缺失}})#挂起
        else:#其他状态
            失败.append({'entry':条目,'outcome':{'kind':'failed','error':'fiber state '+str(状态)}})#报告
    if len(拒绝原因)>0:#有拒绝
        for 原因 in 拒绝原因:#保留到检查点
            保留已组装拒绝(原因)#保留
        try:#检查点
            pass#同步路径已收住原因
        finally:#释放
            for 原因 in 拒绝原因:#释放
                释放已组装拒绝(原因)#释放
    return 失败#失败列表

def 失败细节(结果):
    """渲染一条失败插件的原错误与激活阶段。"""
    阶段=结果['phase'] if 'phase' in 结果 else None#阶段
    前缀='' if 阶段 is None else 阶段+': '#阶段前缀
    return 前缀+格式化激活错误(结果['error'])#细节

def 未激活诊断(项):
    """重载比较与可选警告用的稳定按条目文本。"""
    条目=项['entry']#条目
    结果=项['outcome']#结果
    if 结果['kind']=='failed':#失败
        细节=失败细节(结果)#细节
    else:#挂起
        缺失=结果['missing']#缺失
        主语='service' if len(缺失)==1 else 'services'#单复数
        列出=', '.join(缺失) if len(缺失)>0 else 'unknown'#名单
        细节='pending (waiting for '+主语+': '+列出+')'#挂起行
    选项=条目.选项#选项
    return str(选项['id'] if 'id' in 选项 else None)+' ('+str(选项['name'] if 'name' in 选项 else None)+'): '+细节#诊断

def 激活诊断(二进制名,失败列表):
    """渲染仅可选警告。"""
    名词='entry' if len(失败列表)==1 else 'entries'#单复数
    return 二进制名+': warning: '+str(len(失败列表))+' '+名词+' did not activate\n'+'\n'.join(未激活诊断(项) for 项 in 失败列表)+'\n'#诊断

def 启动诊断(二进制名,失败列表,必需集合):
    """分组启动失败与待服务，并标出每条必需条目。"""
    行=[二进制名+': startup failed: '+str(len(必需集合))+' required '+('plugin' if len(必需集合)==1 else 'plugins')+' did not activate']#首行
    已失败=[{'entry':项['entry'],'outcome':项['outcome']} for 项 in 失败列表 if 项['outcome']['kind']=='failed']#失败
    挂起=[{'entry':项['entry'],'outcome':项['outcome']} for 项 in 失败列表 if 项['outcome']['kind']=='pending']#挂起
    挂起.sort(key=lambda 项:0 if 项['entry'] in 必需集合 else 1)#必需在前
    def 标签(条目):
        """带必需标记的标签。"""
        选项=条目.选项#选项
        标识=str(选项['id'] if 'id' in 选项 else None)#id
        return 标识+(' (required)' if 条目 in 必需集合 else '')#标签
    if len(已失败)>0:#有失败
        行.append('')#空行
        行.append('Failed plugins ('+str(len(已失败))+'):')#标题
        for 项 in 已失败:#逐条
            条目=项['entry']#条目
            选项=条目.选项#选项
            行.append('  '+标签(条目))#标签
            行.append('    Package: '+str(选项['name'] if 'name' in 选项 else None))#包名
            for 细行 in 失败细节(项['outcome']).split('\n'):#细节
                行.append('    '+细行)#缩进
    if len(挂起)>0:#有挂起
        宽=max([len('Plugin')]+[len(标签(项['entry'])) for 项 in 挂起])+2#列宽
        行.append('')#空行
        行.append('Plugins waiting for services ('+str(len(挂起))+'):')#标题
        行.append('  '+'Plugin'.ljust(宽)+'Missing services')#表头
        for 项 in 挂起:#逐条
            缺失=项['outcome']['missing']#缺失
            列出=', '.join(缺失) if len(缺失)>0 else 'unknown'#名单
            行.append('  '+标签(项['entry']).ljust(宽)+列出)#行
    return '\n'.join(行)#诊断

def 审计启动条目(上下文,二进制名,警告=None):
    """对已结算 Loader 树应用 DSH 启动政策。"""
    if 警告 is None:#缺省
        def 写警告(行):
            """写标准错误。"""
            sys.stderr.write(行)#stderr
        警告=写警告#缺省
    失败=未激活条目(上下文)#收集
    根包含=启动包含表.get(id(上下文))#引导 Include
    必需集合=set()#必需条目
    for 项 in 失败:#收集必需
        条目=项['entry']#条目
        选项=条目.选项#选项
        标识=选项['id'] if 'id' in 选项 else None#id
        if 条目 is 根包含 or 标识 in 必需启动条目标识:#必需
            必需集合.add(条目)#收下
    if len(必需集合)>0:#有必需失败
        条目表=[]#诊断条目
        for 项 in 失败:#逐条
            条目=项['entry']#条目
            选项=条目.选项#选项
            条目表.append({#元数据
                'id':选项['id'] if 'id' in 选项 else None,
                'module':选项['name'] if 'name' in 选项 else None,
                'required':条目 in 必需集合,
                'fiberState':条目.纤程.状态 if 条目.纤程 is not None else None,
                'outcome':项['outcome'],
            })#结束
        raise 启动错误(启动诊断(二进制名,失败,必需集合),条目表)#拒绝
    if len(失败)>0:#可选失败
        警告(激活诊断(二进制名,失败))#警告

def 断言条目已加载(上下文,二进制名):
    """树结算之后，拒绝没有 fiber 的启用条目。"""
    失败=[]#失败
    for 条目 in 上下文.加载器.列出插件配置():#逐条
        if 条目.纤程 is None and not 条目.已禁用:#未禁用却无 fiber
            选项=条目.选项#选项 dict
            失败.append(选项['name'] if 'name' in 选项 else None)#记下名
    if len(失败)>0:#有加载失败
        raise 启动错误(二进制名+': plugin(s) failed to load: '+', '.join(str(名) for 名 in 失败)+'; Cordis startup failed because these plugin(s) could not be resolved (see the error(s) logged above)')#拒绝

def 断言条目已激活(上下文,二进制名):
    """启用条目失败或仍未激活时拒绝。"""
    断言条目已加载(上下文,二进制名)#先检查加载
    失败行=[]#失败行
    拒绝原因=[]#拒绝原因
    for 条目 in 上下文.加载器.列出插件配置():#逐条
        纤程=条目.纤程#fiber
        if 纤程 is None or 条目.已禁用:#无或已禁用
            continue#跳过
        状态=纤程.状态#状态
        if 状态==纤程激活:#已激活
            continue#跳过
        选项=条目.选项#选项 dict
        名=选项['name'] if 'name' in 选项 else None#插件名
        if 状态==纤程失败:#已失败
            try:#收回原因
                纤程.等待()#等待
            except Exception as 错误:#插件启动失败形态未钉死
                拒绝原因.append(错误)#记下
                失败行.append(str(名)+': '+str(错误))#格式化
            continue#下一条
        if 状态==纤程等待:#仍在等待
            缺失=[]#缺失服务
            for 服务名 in 纤程.依赖表:#依赖表
                if 纤程.所属上下文.获取服务(服务名,False) is None:#仍缺
                    缺失.append(服务名)#记下
            主语='service' if len(缺失)==1 else 'services'#单复数
            列出=', '.join(缺失) if len(缺失)>0 else 'unknown'#名单
            失败行.append(str(名)+': pending (waiting for '+主语+': '+列出+')')#挂起
        else:#其他状态
            失败行.append(str(名)+': fiber state '+str(状态))#报告
    if len(失败行)>0:#有未激活
        for 原因 in 拒绝原因:#保留到检查点
            保留已组装拒绝(原因)#保留
        try:#检查点
            pass#Python 无 setImmediate；同步路径已收住原因
        finally:#释放
            for 原因 in 拒绝原因:#释放
                释放已组装拒绝(原因)#释放
        名词='entry' if len(失败行)==1 else 'entries'#单复数
        raise 启动错误(二进制名+': '+str(len(失败行))+' '+名词+' did not activate\n'+'\n'.join(失败行))#拒绝

def 启动(二进制名,绝对配置路径,补丁=None,准备=None,裸模块基址=None):
    """对着绝对配置路径启动 Loader，整棵树结算后才返回。"""
    上下文=上下文()#根上下文
    启动日志=[]#启动日志切片
    阶段='宿主准备失败'#当前阶段标签
    try:#安装并挂树
        基址=路径转文件url(os.path.dirname(绝对配置路径))#配置目录基址
        if not 基址.endswith('/'):#尾斜杠
            基址=基址+'/'#补上
        上下文.基准网址=基址#写入
        加载器类=loader.加载器#Loader
        上下文.提供服务('dshHomePath',主目录路径)#提供主目录解析
        def 更新观察(_配置,_不保存,下一步):
            """Fiber.update 丢掉重启承诺；在瀑布返回前观察。"""
            try:#观察
                下一步()#同步
            except Exception as 错误:#激活失败
                上下文.日志.错误(错误)#记日志
                启动日志.append({'ts':0,'name':'internal/update','type':'error','args':(错误,)})#记入切片
        上下文.监听('internal/update',更新观察,{'全局':True,'前置':True})#前置观察
        上下文.启动插件(加载器类).等待()#安装 Loader 并抛出启动失败
        if 准备 is not None:#可选宿主准备
            准备(上下文)#准备，同步
        阶段='插件树加载失败'#此后归插件树
        挂载根包含(上下文,绝对配置路径,补丁,裸模块基址)#挂根 Include
        加载器=上下文.获取服务('加载器',False)#Loader
        if 加载器 is not None:#仍在
            加载器.等待()#等待结算，抛出插件启动失败
        if 上下文.获取服务('加载器',False) is None:#树已拆
            return 上下文#返回
        审计启动条目(上下文,二进制名)#审计激活
        return 上下文#返回根上下文
    except Exception as 原因:#启动失败形态含插件树与配置错误
        上下文.纤程.拆除()#拆除部分树
        if isinstance(原因,启动错误):#启动审计错误
            原因.startup={'configurationPath':绝对配置路径,'messages':启动日志}#附上切片
            raise 原因#原样抛出
        细节=str(原因)#外层细节
        最深=原因#向 cause 链下走
        while isinstance(最深,Exception) and 最深.__cause__ is not None:#找最深
            最深=最深.__cause__#下一层
        栈='' if 最深 is 原因 or not isinstance(最深,Exception) else '\n'+str(最深)#深层栈
        raise 启动错误(二进制名+': '+阶段+': '+细节+栈) from 原因#带阶段标签

def 添加源码段落(上下文,源码根):
    """加一段全局提示词，点名磁盘上的 harness 源码检出。"""
    系统提示词=上下文.获取服务('systemPrompt',False)#系统提示词服务
    if 系统提示词 is None:#没有该服务
        return None#空操作
    return 系统提示词.段落({#登记段落
        'name':源码段落名,#段落名
        'order':系统提示词.取段落序号('HARNESS_SOURCE'),#共享放置
        'text':'The DeepSeek Harness implementation checkout is at '+源码根+'. The checkout location and current working directory are separate values and may differ; never infer the working directory from this path. Use pwd to determine the current working directory. Use this checkout only to inspect or extend DSH itself.',#字面量
    })#section 结束

def 渲染配置转储(二进制名,绝对配置路径,各层,警告=None):
    """按 boot 会挂上的方式组合有效条目列表并渲染。各层条目是 dict。"""
    if 警告 is None:#缺省
        def 写警告(行):
            """写标准错误并换行。"""
            sys.stderr.write(行+'\n')#stderr
        警告=写警告#缺省警告
    try:#读基配置
        打开=open(绝对配置路径,'r',encoding='utf-8')#打开
        try:#读
            内容=打开.read()#文本
        finally:#关
            打开.close()#关闭
    except OSError as 错误:#读失败
        raise 启动错误(二进制名+': failed to read config '+绝对配置路径+': '+str(错误))#包装
    try:#解析
        解析=yaml.load(内容,Loader=条目列表加载器)#方言
    except yaml.YAMLError as 错误:#解析失败
        raise 启动错误(二进制名+': failed to parse config '+绝对配置路径+': '+str(错误))#包装
    if not isinstance(解析,list):#不是数组
        raise 启动错误(二进制名+': config '+绝对配置路径+' must be a top-level YAML array of entries')#拒绝
    基标签=os.path.basename(绝对配置路径)#基文件标签
    基=解析#基条目列表
    def 层补丁(层):
        """取出一层补丁列表。"""
        if 'patches' not in 层 or 层['patches'] is None:#省略
            return []#空
        return 层['patches']#补丁
    def 层标签(层):
        """一层标签。"""
        return 层['label']#标签
    def 快照(计数,警告列表):
        """应用到前缀层。"""
        展平=copy.deepcopy([补丁 for 层 in 各层[:计数] for 补丁 in 层补丁(层)])#克隆展平
        def 记警告(消息,*参数):
            """展开 %C。"""
            下标=[0]#游标
            def 替(匹配):
                """取下一参数。"""
                值=参数[下标[0]] if 下标[0]<len(参数) else None#参数
                下标[0]=下标[0]+1#推进
                return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#JSON
            警告列表.append(re.sub(r'%C',替,消息))#展开
        return 应用条目补丁(基,展平,记警告)#应用
    上一=基#上一快照
    上一警告=[]#上一警告
    出处=[{'origin':基标签,'patchedBy':[]} for _ in 基]#每行出处
    已组合=基#当前组合
    for 计数 in range(1,len(各层)+1):#逐层
        层=各层[计数-1]#本层
        警告列表=[]#本快照警告
        已组合=快照(计数,警告列表)#应用到本前缀
        for 行 in 警告列表[len(上一警告):]:#新尾巴
            警告(二进制名+': ['+层标签(层)+'] '+行)#带层标签
        之前=[json.dumps(条,ensure_ascii=False,separators=(',',':'),allow_nan=False,sort_keys=True) for 条 in 上一]#上一序列化
        for 下标 in range(len(已组合)):#按位置差分
            if 下标>=len(之前):#追加行
                出处.append({'origin':层标签(层),'patchedBy':[]})#归本层
            elif json.dumps(已组合[下标],ensure_ascii=False,separators=(',',':'),allow_nan=False,sort_keys=True)!=之前[下标]:#改写
                出处[下标]['patchedBy'].append(层标签(层))#记补丁
        上一=已组合#推进
        上一警告=警告列表#推进
    return 分组转储(已组合,出处)#按出处分组

def 分组转储(已组合,出处):
    """把已组合行按连续段分组。出处条目是 dict。"""
    行列表=[]#输出行
    当前标签=None#当前段标签
    组=[]#当前段行
    def 冲掉():
        """冲掉当前段。"""
        nonlocal 组,当前标签#修改
        if 当前标签 is None or len(组)==0:#没有
            return#无
        行列表.append('# == '+当前标签)#段注释
        行列表.append(yaml.dump(组,allow_unicode=True,sort_keys=False).rstrip())#段 YAML
        组=[]#清空
    for 下标 in range(len(已组合)):#逐行
        记录=出处[下标]#出处
        补丁方=记录['patchedBy'] if 'patchedBy' in 记录 else []#补丁方
        if len(补丁方)==0:#无补丁
            标签=记录['origin']#原层
        else:#有补丁
            标签=记录['origin']+', patched by '+', '.join(补丁方)#标签
        if 标签!=当前标签:#新段
            冲掉()#冲掉上一段
            当前标签=标签#切换
        组.append(已组合[下标])#收入
    冲掉()#冲掉末段
    return '\n'.join(行列表)+'\n'#拼成文档
