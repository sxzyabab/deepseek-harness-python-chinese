import json,os,platform,re,shutil,stat,sys,tempfile,threading
from ...依赖.schemastery import 字符串字段
from ...内核.工具 import 定义工具

__all__=['名称','依赖','配置','应用','默认','语法解析主运行时','读主运行时','工作区依赖路径','解析主运行时','安装主运行时']

名称='tool-workspace-dependencies'
依赖=['tools']

配置={
    'source':字符串字段(最小长度=1,可空=False),
    'root':字符串字段(最小长度=1),
}

class 工作区依赖错误(Exception):
    """主运行时载荷无效或不可用。"""

版本形态=re.compile(r'^\d+\.\d+\.\d+(?:[-+][\w.-]+)?$',re.ASCII)
平台表=('win32','darwin','linux')
发行名形态=re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$',re.ASCII)
发行版本形态=re.compile(r'^\d[\w.!+-]*$',re.ASCII)
摘要形态=re.compile(r'^[a-f0-9]{64}$',re.ASCII)

def 是否记录(值):
    """非空 dict。"""
    return isinstance(值,dict)

def 是否版本(值):
    """发行版本串。"""
    return isinstance(值,str) and 版本形态.search(值) is not None

def 是否发行表(值):
    """发行名到版本。"""
    if not 是否记录(值):
        return False
    for 名,版本 in 值.items():
        if 发行名形态.search(名) is None or not isinstance(版本,str) or 发行版本形态.search(版本) is None:
            return False
    return True

def 当前架构():
    """x64 或 arm64。"""
    机=platform.machine().lower()
    if 机 in ('x86_64','amd64'):
        return 'x64'
    if 机 in ('arm64','aarch64'):
        return 'arm64'
    return 机

def 语法解析主运行时(值):
    """校验 runtime.json 并规范化遗留 components。"""
    if not 是否记录(值):
        raise 工作区依赖错误('主运行时: 元数据无效')
    遗留='components' in 值
    版本面=值['components'] if 遗留 else 值
    if not 是否记录(版本面) or (遗留 and any(键 in 值 for 键 in ('python','node','pnpm'))):
        raise 工作区依赖错误('主运行时: 元数据无效')
    桌面版本=值.get('desktopVersion')
    平台名=值.get('platform')
    架构=值.get('arch')
    载荷摘要=值.get('payloadDigest') if 'payloadDigest' in 值 else None
    python=版本面.get('python')
    node=版本面.get('node') if 'node' in 版本面 else None
    pnpm=版本面.get('pnpm') if 'pnpm' in 版本面 else None
    python包=值.get('pythonPackages') if 'pythonPackages' in 值 else ({} if 遗留 else None)
    if (not isinstance(桌面版本,str) or 桌面版本==''
            or not isinstance(平台名,str) or 平台名 not in 平台表
            or not isinstance(架构,str) or 架构 not in ('x64','arm64')
            or not 是否版本(python)
            or (node is not None and not 是否版本(node))
            or (pnpm is not None and (not 是否版本(pnpm) or node is None))
            or (载荷摘要 is not None and (not isinstance(载荷摘要,str) or 摘要形态.search(载荷摘要) is None))
            or not 是否发行表(python包)):
        raise 工作区依赖错误('主运行时: 元数据无效')
    条目=list(python包.items())
    发行={}
    for 名,版本 in 条目:
        规范=re.sub(r'[-_.]+','-',名.lower(),count=0)
        if 规范 in 发行:
            raise 工作区依赖错误('主运行时: 元数据无效')
        发行[规范]=版本
    if len(发行)!=len(条目):
        raise 工作区依赖错误('主运行时: 元数据无效')
    if 遗留:
        for 名 in ('numpy','pandas'):
            if not 是否版本(版本面.get(名)):
                raise 工作区依赖错误('主运行时: 元数据无效')
            版本=发行.get(名)
            if 版本 is not None and 版本!=版本面[名]:
                raise 工作区依赖错误('主运行时: '+名+' 发行版本冲突')
    结果={
        'desktopVersion':桌面版本,
        'platform':平台名,
        'arch':架构,
        'python':python,
        'pythonPackages':python包,
    }
    if 载荷摘要 is not None:
        结果['payloadDigest']=载荷摘要
    if node is not None:
        结果['node']=node
    if pnpm is not None:
        结果['pnpm']=pnpm
    return 结果

def 读主运行时(根):
    """读并规范化构建元数据，不改源文件。"""
    文件=open(os.path.join(根,'runtime.json'),'r',encoding='utf-8')
    try:
        文本=文件.read()
    finally:
        文件.close()
    return 语法解析主运行时(json.loads(文本))

def 工作区依赖路径(根,清单):
    """按平台解析解释器与库位置。"""
    依赖=os.path.join(根,'dependencies')
    视窗=清单['platform']=='win32'
    结果={
        'python':os.path.join(依赖,'python','python.exe') if 视窗 else os.path.join(依赖,'python','bin','python3'),
        'pythonPackages':os.path.join(依赖,'python','Lib','site-packages') if 视窗 else os.path.join(
            依赖,'python','lib','python'+'.'.join(清单['python'].split('.')[0:2]),'site-packages',
        ),
        'pythonDistributions':清单['pythonPackages'],
    }
    if 'node' in 清单:
        结果['node']=os.path.join(依赖,'node','bin','node.exe' if 视窗 else 'node')
        结果['nodePackages']=os.path.join(依赖,'node','node_modules')
    if 'pnpm' in 清单:
        结果['pnpm']=os.path.join(依赖,'pnpm','bin','pnpm.mjs')
    return 结果

def 校验载荷条目(路径表):
    """确认文件与目录存在且类型正确。"""
    项表=[
        (路径表.get('python'),'file'),
        (路径表.get('node'),'file'),
        (路径表.get('pnpm'),'file'),
        (路径表.get('pythonPackages'),'directory'),
        (路径表.get('nodePackages'),'directory'),
    ]
    for 路径,种类 in 项表:
        if 路径 is None:
            continue
        信息=os.stat(路径)
        是文件=stat.S_ISREG(信息.st_mode)
        是目录=stat.S_ISDIR(信息.st_mode)
        if 种类=='file' and not 是文件:
            raise 工作区依赖错误('主运行时: 期望文件条目')
        if 种类=='directory' and not 是目录:
            raise 工作区依赖错误('主运行时: 期望目录条目')

def 存在路径(路径):
    """路径存在且不是符号链接。"""
    try:
        信息=os.lstat(路径)
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(信息.st_mode):
        raise 工作区依赖错误('主运行时: 安装路径是文件系统链接')
    return True

def 兼容清单(来源):
    """读清单并核对本机。"""
    清单=读主运行时(来源)
    本平台='win32' if sys.platform=='win32' else sys.platform
    if 清单['platform']!=本平台 or 清单['arch']!=当前架构():
        raise 工作区依赖错误('主运行时: 平台或架构不兼容')
    return 清单

def 解析主运行时(来源):
    """就地使用载荷，不拷贝。"""
    路径表=工作区依赖路径(来源,兼容清单(来源))
    校验载荷条目(路径表)
    return 路径表

def 安装主运行时(来源,根):
    """拷贝到本地安装目录；失败时保留完整旧树。"""
    清单=兼容清单(来源)
    os.makedirs(os.path.dirname(根),exist_ok=True)
    先前=根+'.previous'
    先前在=存在路径(先前)
    根在=存在路径(根)
    if not 根在 and 先前在:
        os.rename(先前,根)
    if 存在路径(os.path.join(根,'runtime.json')) and json.dumps(读主运行时(根),ensure_ascii=False,separators=(',',':'),allow_nan=False)==json.dumps(清单,ensure_ascii=False,separators=(',',':'),allow_nan=False):
        路径表=工作区依赖路径(根,清单)
        校验载荷条目(路径表)
        return 路径表
    暂存=tempfile.mkdtemp(prefix='.primary-runtime-',dir=os.path.dirname(根))
    try:
        shutil.copytree(来源,暂存,dirs_exist_ok=True,symlinks=False)
        路径表=工作区依赖路径(暂存,清单)
        校验载荷条目(路径表)
        shutil.rmtree(先前,ignore_errors=True)
        替换中=存在路径(根)
        if 替换中:
            os.rename(根,先前)
        try:
            os.rename(暂存,根)
        except OSError:
            if 替换中:
                os.rename(先前,根)
            raise
        shutil.rmtree(先前,ignore_errors=True)
    finally:
        shutil.rmtree(暂存,ignore_errors=True)
    return 工作区依赖路径(根,清单)

def 应用(上下文,配置值=None):
    """登记只读路径查询；首次调用准备载荷。"""
    if 配置值 is None:
        配置值={}
    来源=配置值['source']
    根=配置值['root'] if 'root' in 配置值 else None
    if not os.path.isabs(来源) or (根 is not None and not os.path.isabs(根)):
        raise 工作区依赖错误('工作区依赖: source 与 root 必须是绝对路径')
    准备=[None]
    锁=threading.Lock()
    def 拆除效果():
        """只等文件系统工作结束。"""
        def 清理():
            """忽略准备失败。"""
            with 锁:
                任务=准备[0]
            if 任务 is None:
                return
            try:
                任务.等待()
            except BaseException:
                pass
        return 清理
    上下文.副作用(拆除效果)
    def 渲染(参数,值):
        """缩进 JSON。"""
        return [{'type':'text','text':json.dumps(值,ensure_ascii=False,indent=2,allow_nan=False)}]
    def 执行(参数,执行上下文):
        """首次调用准备载荷。"""
        from ...内核.作用域 import 操作任务 as 任务类
        with 锁:
            if 准备[0] is None:
                任务=任务类()
                准备[0]=任务
                def 跑():
                    """准备或校验。"""
                    try:
                        if 根 is None:
                            值=解析主运行时(来源)
                        else:
                            值=安装主运行时(来源,根)
                        任务.兑现(值)
                    except BaseException as 错误:
                        with 锁:
                            准备[0]=None
                        任务.拒绝(错误)
                threading.Thread(target=跑,daemon=True).start()
            当前=准备[0]
        return 当前.等待()
    def 呈现调用(参数):
        """通用读卡片。"""
        return {'card':'generic','title':'Load workspace dependencies','kind':'read'}
    上下文.tools.登记(定义工具({
        'name':'load_workspace_dependencies',
        'description':'Get absolute paths to bundled Python and library directories, plus bundled Python distribution versions. Node.js and pnpm paths are included when the payload provides them. Python includes numpy, pandas, python-docx, python-pptx, openpyxl, Pillow, lxml, and XlsxWriter. Use these libraries for Office files unless the user or workspace instructions select another environment. When Node.js and pnpm paths are returned, run pnpm with that Node executable and pnpm script path. This does not change PATH or package-manager settings.',
        'parameters':{},
        'output':{
            'schema':{
                'type':'object','additionalProperties':False,
                'properties':{
                    'python':{'type':'string','required':True},
                    'node':{'type':'string','description':'Absent when the payload ships no Node.js.'},
                    'pnpm':{'type':'string','description':'Absent when the payload ships no pnpm.'},
                    'pythonPackages':{'type':'string','required':True},
                    'nodePackages':{'type':'string','description':'Absent when the payload ships no Node.js.'},
                    'pythonDistributions':{'type':'object','additionalProperties':True,'required':True,'description':'Bundled distribution names and versions recorded in runtime.json; excludes user-installed additions.'},
                },
            },
            'render':渲染,
        },
        'execute':执行,
        'presentCall':呈现调用,
    }))

name=名称
inject=依赖
Config=配置
apply=应用
default=应用
默认=应用
