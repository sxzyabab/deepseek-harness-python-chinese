"""应用二进制共用的启动粘合层。

对齐上游 `@deepseek-ai/dsh-app-boot`。公开面仅中文名。配置键与诊断字面量保持上游。
"""
import os,re,sys,copy,json,threading#路径、环境、流、克隆、JSON、定时
import yaml#YAML
from cordis import 上下文,光纤状态#上下文与光纤状态
from cordis.工具 import 是否thenable#可等待
from include import 包含,应用条目补丁,条目列表加载器,路径转文件url#Include 与补丁
from loader import 组#Group 内建
from home_paths import 主目录路径,解析主目录#主目录
from launch_environment import 创建启动环境快照#启动环境快照
from .配置档 import (#配置档再导出
    组合条目,默认组合包,愈合模块回退,初始化配置档,加载配置档,
    配置补丁文件名,配置模板,配置目录名,读配置清单,解析组合包目录,
    解析配置目录,写配置清单,
)#再导出结束

__all__=[#仅中文公开名
    '解析配置路径','加载环境','加载分层环境','监视用户补丁','加载可选补丁','加载覆盖补丁',
    '渲染配置转储','挂载根包含','安装大声失败','大声失败拆除超时毫秒',
    '断言条目已加载','断言条目已激活','启动','添加源码段落','源码段落名',
    '组合条目','默认组合包','愈合模块回退','初始化配置档','加载配置档',
    '配置补丁文件名','配置模板','配置目录名','读配置清单','解析组合包目录',
    '解析配置目录','写配置清单',
]#公开面结束

源码段落名='harness:source'#源位置段落名
大声失败拆除超时毫秒=2000#拆除超时毫秒
引导名精确=set([#引导专用名
    'PATH','HOME','USERPROFILE','SHELL',
    'NODE_OPTIONS','NODE_PATH','NODE_EXTRA_CA_CERTS',
    'LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT',
    'BASH_ENV','ENV','SHELLOPTS','BASHOPTS',
    'PERL5OPT','PERL5LIB','PYTHONSTARTUP','PYTHONPATH','RUBYOPT','RUBYLIB',
    'JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS','PYTHONHOME',
    'GIT_SSH','GIT_SSH_COMMAND','GIT_EXTERNAL_DIFF','GIT_PAGER','GIT_EDITOR',
    'GIT_ASKPASS','SSH_ASKPASS','GIT_CONFIG_GLOBAL','GIT_CONFIG_SYSTEM','GIT_CONFIG_COUNT',
    'EDITOR','VISUAL','PAGER',
    'DEEPSEEK_BASE_URL','DEEPSEEK_SEARCH_BASE_URL',
    'SSL_CERT_FILE','SSL_CERT_DIR',
    'HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY',
    'REQUESTS_CA_BUNDLE','CURL_CA_BUNDLE','NODE_TLS_REJECT_UNAUTHORIZED',
])#引导名结束
引导名前缀=['DSH_','XDG_','DYLD_','BASH_FUNC_']#引导专用前缀
启动包含表={}#根 Include 条目登记（ctx id → entry）
已组装拒绝={}#已组装激活拒绝计数

光纤等待=光纤状态.等待#等待中
光纤激活=光纤状态.已激活#已激活
光纤失败=光纤状态.失败#已失败

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#映射
    return getattr(对象,键,缺省)#属性

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
        警告=lambda 行:sys.stderr.write(行)#stderr
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
        return True#是
    for 前缀 in 引导名前缀:#前缀
        if 大写.startswith(前缀):#命中
            return True#是
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

def 读环境层(二进制名,目录,警告):#读一层 .env
    """解析某目录的 .env 但不应用，拒绝引导专用名。"""
    路径=os.path.join(目录,'.env')#该层路径
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
            raise Exception(
                二进制名+': '+路径+' sets "'+名+'", which only the launching environment may set'
                +' (it decides how this process starts, where its code and instructions load from, or how it'
                +' reaches the network); export '+名+' instead of putting it in a .env file'
            )#错误
    return {'path':路径,'values':值表}#路径与条目

def 加载分层环境(二进制名,工作目录=None,警告=None):#加载分层环境
    """加载继承环境 > 调用目录 .env > Harness 主目录 .env 快照。"""
    if 工作目录 is None:#缺省
        工作目录=os.getcwd()#cwd
    if 警告 is None:#缺省
        警告=lambda 行:sys.stderr.write(行)#stderr
    主目录=解析主目录()#Harness 主目录
    继承=dict(os.environ)#继承环境副本
    项目=读环境层(二进制名,工作目录,警告)#项目层
    用户=None if 主目录==os.path.abspath(工作目录) else 读环境层(二进制名,主目录,警告)#用户层
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
    except Exception as 错误:#解析失败
        raise Exception(二进制名+': failed to parse '+标签+' '+文件+': '+str(错误))#包装
    if not isinstance(解析,list):#不是顶层数组
        raise Exception(二进制名+': '+标签+' '+文件+' must be a top-level YAML array of loader patch entries')#拒绝
    for 下标,条目 in enumerate(解析):#逐条检查
        if not isinstance(条目,dict) or 条目 is None:#不是映射
            raise Exception(二进制名+': '+标签+' entry '+str(下标+1)+' in '+文件+' must be a mapping (a loader patch entry)')#拒绝
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
        raise Exception(二进制名+': failed to read patches '+文件+': '+str(错误))#大声失败
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
        raise Exception(二进制名+': failed to read overlay '+文件+': '+str(错误))#缺失也失败
    return 解析补丁列表(二进制名,文件,内容,'overlay')#按 overlay 标签

def 挂载根包含(上下文对象,绝对配置路径,补丁=None,裸模块基址=None):#挂上根 Include
    """挂上并记住应用启动使用的根 Include 条目。"""
    if 补丁 is None:#缺省
        补丁=[]#空
    if 裸模块基址 is None:#无宿主基址
        上下文对象.loader.builtins['include']=包含#用原 Include
    else:#宿主解析
        class 宿主根包含(包含):#宿主解析根 Include
            def 导入(自身,名称,获取外层栈=None):#改写导入
                """改写导入。"""
                说明符=路径转文件url(名称) if os.path.isabs(名称) else 名称#绝对改 file URL
                if 名称.startswith('.') or 名称.startswith('cordis:'):#相对与内建
                    return super().导入(说明符,获取外层栈)#父类
                内部=getattr(自身.ctx.loader,'internal',None)#内部
                if 内部 is None:#没有
                    return super().导入(说明符,获取外层栈)#回退
                return 内部.import(说明符,裸模块基址,{})#宿主基址
        上下文对象.loader.builtins['include']=宿主根包含#注册
    上下文对象.loader.builtins['group']=组#注册 group 内建
    包含配置={'path':路径转文件url(绝对配置路径)}#根 include 配置
    if len(补丁)>0:#有补丁
        包含配置['patches']=list(补丁)#带上
    根条目={'id':'include','name':'cordis:include','config':包含配置}#根条目
    包含号=解开(上下文对象.loader.创建(根条目))#创建根条目
    加载器=上下文对象.get('loader')#再取 Loader
    if 加载器 is None:#树已拆
        return None#返回
    条目=加载器.解析(包含号)#解析条目
    启动包含表[id(上下文对象)]=条目#登记
    return 条目#返回根条目

def 解开(值):#等待可等待
    """承诺则等待。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 监视用户补丁(上下文对象,选项):#监视用户补丁层
    """经 Cordis HMR 监视用户补丁层。"""
    二进制名=取字段(选项,'binName')#诊断前缀
    文件名=取字段(选项,'filename')#补丁路径
    组合=取字段(选项,'compose') or (lambda 补丁:补丁)#默认恒等
    热重载=上下文对象.get('hmr')#HMR
    if 热重载 is None:#缺少
        raise Exception(二进制名+': user patch-layer watching requires the Cordis HMR service')#缺少
    条目=启动包含表.get(id(上下文对象))#根 Include
    if 条目 is None:#缺少
        raise Exception(二进制名+': user patch-layer watching requires the root Include entry')#缺少
    def 刷新():#注册精确路径刷新
        """重读用户层并事务更新。"""
        选项配置=取字段(取字段(条目,'options'),'config') or {}#当前配置
        非补丁={键:值 for 键,值 in 选项配置.items() if 键!='patches'}#去掉旧补丁
        用户补丁=加载可选补丁(二进制名,文件名) or []#重读
        补丁=组合(用户补丁)#组合
        解开(条目.更新({'config':{**非补丁,'patches':补丁}}))#事务更新
    try:#注册
        return 解开(热重载.registerConfig(文件名,刷新))#返回拆除器
    except Exception as 错误:#安装失败
        if getattr(错误,'code',None)=='INACTIVE_EFFECT':#树已拆
            return lambda:None#空拆除
        raise#其余失败

def 保留已组装拒绝(原因):#保留一条已组装拒绝
    """计数加一。"""
    已组装拒绝[原因]=已组装拒绝.get(原因,0)+1#计数

def 释放已组装拒绝(原因):#释放一条
    """计数减一。"""
    数=已组装拒绝.get(原因)#当前
    if 数 is None or 数==1:#最后一条
        已组装拒绝.pop(原因,None)#删掉
    else:#还有
        已组装拒绝[原因]=数-1#减一

def 安装大声失败(二进制名,进程=None,拆除=None):#安装大声失败守卫
    """把迟到的未处理插件初始化拒绝变成带标签诊断并 exit(1)。"""
    if 进程 is None:#缺省
        进程=sys#进程
    退出中=False#是否已决定退出
    def 处理器(错误类型,错误,回溯):#未处理异常钩子（Python 用 excepthook 近似）
        """致命失败处理器。"""
        nonlocal 退出中#修改
        if 错误 in 已组装拒绝:#启动审计已计入
            return#忽略
        if 退出中:#已在退出
            return#吞掉
        退出中=True#闩上
        栈=getattr(错误,'__traceback__',None)#回溯
        文本=二进制名+': fatal load failure: '+str(错误)+'\n'#诊断
        写=getattr(取字段(进程,'stderr'),'write',None)#写
        if 写 is not None:#有写
            写(文本)#先写诊断
        if 拆除 is None:#没有拆除
            取字段(进程,'exit')(1) if callable(取字段(进程,'exit')) else os._exit(1)#立刻退出
            return#结束
        def 后台拆除():#后台等拆除
            """等拆除或超时。"""
            完成=threading.Event()#完成事件
            def 跑拆除():#跑拆除
                """跑拆除。"""
                try:#拆除
                    结果=拆除()#跑
                    if 是否thenable(结果):#可等待
                        结果.等待()#等待
                except Exception:#拆除抛错
                    pass#吞掉
                finally:#完成
                    完成.set()#放行
            threading.Thread(target=跑拆除,daemon=True).start()#启动
            完成.wait(大声失败拆除超时毫秒/1000.0)#到时放行
            取字段(进程,'exit')(1) if callable(取字段(进程,'exit')) else os._exit(1)#致命退出
        threading.Thread(target=后台拆除,daemon=True).start()#立即
    # Python 无 unhandledRejection；返回空卸载器，保留 API 形状供启动器接线
    return lambda:None#卸载器

def 断言条目已加载(上下文对象,二进制名):#断言条目已加载
    """树结算之后，拒绝没有 fiber 的启用条目。"""
    失败=[]#失败
    for 条目 in 上下文对象.loader.条目们():#逐条
        if 取字段(条目,'fiber') is None and not 取字段(条目,'disabled'):#未禁用却无 fiber
            失败.append(取字段(取字段(条目,'options'),'name'))#记下名
    if len(失败)>0:#有加载失败
        raise Exception(二进制名+': plugin(s) failed to load: '+', '.join(失败)+'; Cordis startup failed because these plugin(s) could not be resolved (see the error(s) logged above)')#拒绝

def 断言条目已激活(上下文对象,二进制名):#断言条目已激活
    """启用条目失败或仍未激活时拒绝。"""
    断言条目已加载(上下文对象,二进制名)#先检查加载
    失败行=[]#失败行
    拒绝原因=[]#拒绝原因
    for 条目 in 上下文对象.loader.条目们():#逐条
        光纤=取字段(条目,'fiber')#fiber
        if 光纤 is None or 取字段(条目,'disabled'):#无或已禁用
            continue#跳过
        状态=光纤.state#状态
        if 状态==光纤激活:#已激活
            continue#跳过
        名=取字段(取字段(条目,'options'),'name')#插件名
        if 状态==光纤失败:#已失败
            try:#收回原因
                光纤.等待()#等待
            except Exception as 错误:#拿到原因
                拒绝原因.append(错误)#记下
                失败行.append(名+': '+ (错误.__traceback__ and str(错误) or str(错误)))#格式化
            continue#下一条
        if 状态==光纤等待:#仍在等待
            缺失=[服务名 for 服务名 in (取字段(光纤,'inject') or {}) if 光纤.ctx.get(服务名) is None]#缺失服务
            主语='service' if len(缺失)==1 else 'services'#单复数
            失败行.append(名+': pending (waiting for '+主语+': '+(', '.join(缺失) if 缺失 else 'unknown')+')')#挂起
        else:#其他状态
            失败行.append(名+': fiber state '+str(状态))#报告
    if len(失败行)>0:#有未激活
        for 原因 in 拒绝原因:#保留到检查点
            保留已组装拒绝(原因)#保留
        try:#检查点
            pass#Python 无 setImmediate；同步路径已收住原因
        finally:#释放
            for 原因 in 拒绝原因:#释放
                释放已组装拒绝(原因)#释放
        名词='entry' if len(失败行)==1 else 'entries'#单复数
        raise Exception(二进制名+': '+str(len(失败行))+' '+名词+' did not activate\n'+'\n'.join(失败行))#拒绝

def 启动(二进制名,绝对配置路径,补丁=None,准备=None,裸模块基址=None):#启动 Loader 树
    """对着绝对配置路径启动 Loader，整棵树结算后才返回。"""
    上下文对象=上下文()#根上下文
    阶段='host preparation failed'#当前阶段标签
    try:#安装并挂树
        上下文对象.baseUrl=路径转文件url(os.path.dirname(绝对配置路径))#配置目录基址
        if not 上下文对象.baseUrl.endswith('/'):#尾斜杠
            上下文对象.baseUrl=上下文对象.baseUrl+'/'#补上
        from loader import 加载器 as 加载器类#Loader
        上下文对象.provide('dshHomePath',主目录路径)#提供主目录解析
        解开(上下文对象.plugin(加载器类))#安装 Loader
        if 准备 is not None:#可选宿主准备
            解开(准备(上下文对象))#准备
        阶段='plugin tree failed to load'#此后归插件树
        挂载根包含(上下文对象,绝对配置路径,补丁,裸模块基址)#挂根 Include
        加载器=上下文对象.get('loader')#Loader
        if 加载器 is not None:#仍在
            解开(加载器.等待())#等待结算
        if 上下文对象.get('loader') is None:#树已拆
            return 上下文对象#返回
        断言条目已激活(上下文对象,二进制名)#审计激活
        return 上下文对象#返回根上下文
    except Exception as 原因:#启动失败
        解开(上下文对象.fiber.dispose())#拆除部分树
        细节=str(原因)#外层细节
        最深=原因#向 cause 链下走
        while isinstance(最深,Exception) and 最深.__cause__ is not None:#找最深
            最深=最深.__cause__#下一层
        栈='' if 最深 is 原因 or not isinstance(最深,Exception) else '\n'+str(最深)#深层栈
        raise Exception(二进制名+': '+阶段+': '+细节+栈) from 原因#带阶段标签

def 添加源码段落(上下文对象,源码根):#添加源位置段落
    """加一段全局提示词，点名磁盘上的 harness 源码检出。"""
    系统提示词=上下文对象.get('systemPrompt')#系统提示词服务
    if 系统提示词 is None:#没有该服务
        return None#空操作
    return 系统提示词.段落({#登记段落
        'name':源码段落名,#段落名
        'order':-99,#紧挨身份开场之后
        'text':'The DeepSeek Harness implementation checkout is at '+源码根+'. The checkout location and current working directory are separate values and may differ; never infer the working directory from this path. Use pwd to determine the current working directory. Use this checkout only to inspect or extend DSH itself.',#字面量
    })#section 结束

def 渲染配置转储(二进制名,绝对配置路径,各层,警告=None):#渲染有效配置转储
    """按 boot 会挂上的方式组合有效条目列表并渲染。"""
    if 警告 is None:#缺省
        警告=lambda 行:sys.stderr.write(行+'\n')#stderr
    try:#读基配置
        打开=open(绝对配置路径,'r',encoding='utf-8')#打开
        try:#读
            内容=打开.read()#文本
        finally:#关
            打开.close()#关闭
    except OSError as 错误:#读失败
        raise Exception(二进制名+': failed to read config '+绝对配置路径+': '+str(错误))#包装
    try:#解析
        解析=yaml.load(内容,Loader=条目列表加载器)#方言
    except Exception as 错误:#解析失败
        raise Exception(二进制名+': failed to parse config '+绝对配置路径+': '+str(错误))#包装
    if not isinstance(解析,list):#不是数组
        raise Exception(二进制名+': config '+绝对配置路径+' must be a top-level YAML array of entries')#拒绝
    基标签=os.path.basename(绝对配置路径)#基文件标签
    基=解析#基条目列表
    def 快照(计数,警告们):#前缀快照
        """应用到前缀层。"""
        展平=copy.deepcopy([补丁 for 层 in 各层[:计数] for 补丁 in 取字段(层,'patches') or []])#克隆展平
        def 记警告(消息,*参数):#警告
            """展开 %C。"""
            下标=[0]#游标
            def 替(_):#替换
                """取下一参数。"""
                值=参数[下标[0]] if 下标[0]<len(参数) else None#参数
                下标[0]=下标[0]+1#推进
                return json.dumps(值,ensure_ascii=False)#JSON
            警告们.append(re.sub(r'%C',替,消息))#展开
        return 应用条目补丁(基,展平,记警告)#应用
    上一=基#上一快照
    上一警告=[]#上一警告
    出处=[{'origin':基标签,'patchedBy':[]} for _ in 基]#每行出处
    已组合=基#当前组合
    for 计数 in range(1,len(各层)+1):#逐层
        层=各层[计数-1]#本层
        警告们=[]#本快照警告
        已组合=快照(计数,警告们)#应用到本前缀
        for 行 in 警告们[len(上一警告):]:#新尾巴
            警告(二进制名+': ['+取字段(层,'label')+'] '+行)#带层标签
        之前=[json.dumps(条,ensure_ascii=False,sort_keys=True) for 条 in 上一]#上一序列化
        for 下标 in range(len(已组合)):#按位置差分
            if 下标>=len(之前):#追加行
                出处.append({'origin':取字段(层,'label'),'patchedBy':[]})#归本层
            elif json.dumps(已组合[下标],ensure_ascii=False,sort_keys=True)!=之前[下标]:#改写
                出处[下标]['patchedBy'].append(取字段(层,'label'))#记补丁
        上一=已组合#推进
        上一警告=警告们#推进
    return 分组转储(已组合,出处)#按出处分组

def 分组转储(已组合,出处):#按出处分组转储
    """把已组合行按连续段分组。"""
    行们=[]#输出行
    当前标签=None#当前段标签
    组=[]#当前段行
    def 冲掉():#冲掉当前段
        """冲掉当前段。"""
        nonlocal 组,当前标签#修改
        if 当前标签 is None or len(组)==0:#没有
            return#无
        行们.append('# == '+当前标签)#段注释
        行们.append(yaml.dump(组,allow_unicode=True,sort_keys=False).rstrip())#段 YAML
        组=[]#清空
    for 下标 in range(len(已组合)):#逐行
        记录=出处[下标]#出处
        标签=取字段(记录,'origin') if len(取字段(记录,'patchedBy') or [])==0 else (取字段(记录,'origin')+', patched by '+', '.join(取字段(记录,'patchedBy')))#标签
        if 标签!=当前标签:#新段
            冲掉()#冲掉上一段
            当前标签=标签#切换
        组.append(已组合[下标])#收入
    冲掉()#冲掉末段
    return '\n'.join(行们)+'\n'#拼成文档
