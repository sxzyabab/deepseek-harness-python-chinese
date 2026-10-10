import os,json,copy,sys,shutil#路径、JSON、克隆、标准错误、删目录
from ...依赖.include import 应用插件补丁 as 应用条目补丁#补丁应用
from ...工具.主目录路径 import 解析主目录#主目录解析
from .异常 import 启动错误#应用启动粘合层失败

__all__=[#仅中文公开名
    '配置目录名','配置补丁文件名','配置模板','默认组合包','可选组合包',
    '解析配置目录','初始化配置档','愈合模块回退','读配置清单','写配置清单',
    '解析组合包目录','加载配置档','加载配置目录','组合条目','创建配置解析世代',
    '愈合隔离配置模块回退','拆开配置模块回退','组合包补丁路径','报告跳过组合包',
]#公开面结束

配置目录名='profiles'#配置目录名
配置补丁文件名='cordis.patch.yml'#用户补丁文件名
配置模板={#随附模板
    'acp':{'bundles':['@deepseek-ai/dsh-base','@deepseek-ai/dsh-acp-app']},#ACP
    'web':{'bundles':['@deepseek-ai/dsh-base','@deepseek-ai/dsh-web-app']},#Web
    'headless':{'bundles':['@deepseek-ai/dsh-base','@deepseek-ai/dsh-headless']},#无头
    'sdk':{'bundles':['@deepseek-ai/dsh-base','@deepseek-ai/dsh-sdk-app']},#SDK
    'sdk-minimal':{'bundles':['@deepseek-ai/dsh-sdk-minimal']},#最小SDK
}#模板结束
安装拥有元组={#安装拥有元组
    'headless':['@deepseek-ai/dsh-base','@deepseek-ai/dsh-web-app','@deepseek-ai/dsh-headless'],#旧无头
}#元组结束
默认组合包=['@deepseek-ai/dsh-base']#默认组合包
可选组合包=[#安装随附、模板未选中的可选组合包
    '@deepseek-ai/dsh-experimental-session-search',
    '@deepseek-ai/dsh-experimental-ralph-bundle',
    '@deepseek-ai/dsh-experimental-terminal-bundle',
    '@deepseek-ai/dsh-experimental-badge-skill-bundle',
    '@deepseek-ai/dsh-experimental-session-titles-bundle',
    '@deepseek-ai/dsh-experimental-agent-team-profile',
    '@deepseek-ai/dsh-experimental-voice-input-bundle',
    '@deepseek-ai/dsh-experimental-cot-translation-bundle',
    '@deepseek-ai/dsh-experimental-auto-review',
    '@deepseek-ai/dsh-experimental-inspector-profile',
    '@deepseek-ai/dsh-experimental-tool-worktree',
]#可选结束
退役组合包=set([#安装不再携带、加载时从清单去掉
    '@deepseek-ai/dsh-experimental-schedule-bundle',
])#退役结束
配置补丁模板='''# Your patch layer for this dsh profile, applied after every bundle layer:
# a top-level YAML array of loader patch entries (id-targeted config
# overrides, disables, and insert lists; `!!js` expressions allowed).
[]
'''#用户补丁模板
配置工作区='''packages:
  - .

nodeLinker: hoisted
autoInstallPeers: false
'''#pnpm 工作区

def 解析配置目录(名,主目录=None):#解析配置目录
    '在 Harness 主目录下解析一个配置的目录'
    if 主目录 is None:#缺省
        主目录=解析主目录()#主目录
    if 名=='' or '/' in 名 or '\\' in 名 or 名 in ('.','..','node_modules'):#非法名
        raise 启动错误('dsh: 非法配置档名 '+json.dumps(名,ensure_ascii=False))#拒绝
    return os.path.join(主目录,配置目录名,名)#拼目录

def 初始化配置档(目录,组合包列表):#初始化配置
    '初始化一个配置目录'
    os.makedirs(目录,exist_ok=True)#确保目录
    清单路径=os.path.join(目录,'package.json')#清单
    if not os.path.exists(清单路径):#没有清单
        清单={#新清单
            'name':'dsh-profile-'+os.path.basename(目录),#包名
            'private':True,#私有
            'dependencies':{},#空依赖
            'dsh':{'profile':{'bundles':list(组合包列表)}},#组合包列表
        }#清单结束
        文件=open(清单路径,'w',encoding='utf-8')#打开
        try:#写
            文件.write(json.dumps(清单,ensure_ascii=False,indent=2)+'\n')#写
        finally:#关
            文件.close()#关闭
    补丁路径=os.path.join(目录,配置补丁文件名)#用户补丁
    if not os.path.exists(补丁路径):#没有
        文件=open(补丁路径,'w',encoding='utf-8')#打开
        try:#写
            文件.write(配置补丁模板)#写空补丁
        finally:#关
            文件.close()#关闭
    工作区=os.path.join(目录,'pnpm-workspace.yaml')#pnpm
    if not os.path.exists(工作区):#没有
        文件=open(工作区,'w',encoding='utf-8')#打开
        try:#写
            文件.write(配置工作区)#写
        finally:#关
            文件.close()#关闭

def 读配置清单(二进制名,目录):#读配置清单
    '读一个配置的清单'
    路径=os.path.join(目录,'package.json')#清单路径
    try:#读
        文件=open(路径,'r',encoding='utf-8')#打开
        try:#读
            原文=文件.read()#原文
        finally:#关
            文件.close()#关闭
    except OSError as 错误:#读失败
        raise 启动错误(二进制名+': 读取配置档清单失败: '+str(错误))#包装
    解析=json.loads(原文)#解析
    if not isinstance(解析,dict) or 解析 is None:#非对象
        raise 启动错误(二进制名+': 配置档清单必须是 JSON 对象')#拒绝
    return 解析#清单

def 写配置清单(目录,清单):#写配置清单
    '把配置清单写回'
    文件=open(os.path.join(目录,'package.json'),'w',encoding='utf-8')#打开
    try:#写
        文件.write(json.dumps(清单,ensure_ascii=False,indent=2)+'\n')#写
    finally:#关
        文件.close()#关闭

def 同组合包(左,右):#列表是否相同
    '两个组合包列表是否同值同序'
    return len(左)==len(右) and all(左[下标]==右[下标] for 下标 in range(len(左)))#比较

def 组合包补丁文件(组合包):#声明的补丁文件
    '字符串是一个文件，列表则按声明顺序'
    声明=组合包.get('patch') if isinstance(组合包,dict) else None#声明
    文件表=[声明] if isinstance(声明,str) else 声明#统一成列表
    if not isinstance(文件表,list) or not all(isinstance(文件,str) for 文件 in 文件表):#非法
        raise 启动错误('dsh.bundle.patch must be a file path or a list of file paths')
    return 文件表#相对路径

def 组合包补丁路径(包目录,组合包):#绝对补丁路径
    '按声明顺序解析成绝对路径'
    return [os.path.join(包目录,文件) for 文件 in 组合包补丁文件(组合包)]#绝对

def 丢掉退役组合包(目录,清单):#去掉退役组合包
    '清单列了退役组合包才写回'
    组合包=list(((清单.get('dsh') or {}).get('profile') or {}).get('bundles') or [])#当前
    留下=[名 for 名 in 组合包 if 名 not in 退役组合包]#保留
    if len(留下)==len(组合包):#没变
        return 清单#原样
    规范化=dict(清单)#拷贝
    dsh=dict(清单.get('dsh') or {})#dsh
    配置=dict(dsh.get('profile') or {})#profile
    配置['bundles']=留下#写回
    dsh['profile']=配置#写回
    规范化['dsh']=dsh#写回
    写配置清单(目录,规范化)#落盘
    return 规范化#新清单

def 报告跳过组合包(二进制名,配置):#打印跳过
    '加载本身不打印；启动器每次启动调用一次'
    for 项 in 配置.get('skippedBundles') or []:#逐个
        sys.stderr.write(二进制名+': skipping profile bundle '+json.dumps(项['packageName'],ensure_ascii=False)+': '+项['reason']+'\n')

def 规范化随附配置(名,目录,清单):#规范化随附配置
    '把恰好是安装拥有的组合包元组规范化到其随附模板'
    拥有=安装拥有元组.get(名)#安装拥有
    当前=配置模板.get(名)#当前模板
    组合包=((清单.get('dsh') or {}).get('profile') or {}).get('bundles')#当前列表
    if 当前 is None or 组合包 is None:#非随附或无列表
        return 清单#原样
    是退役元组=拥有 is not None and 同组合包(组合包,拥有)#旧安装元组
    if 是退役元组 is False:#无需规范化
        return 清单#原样
    规范化=dict(清单)#拷贝
    dsh=dict(清单.get('dsh') or {})#dsh
    配置=dict(dsh.get('profile') or {})#profile
    配置['bundles']=list(当前['bundles'])#换成模板
    dsh['profile']=配置#写回
    规范化['dsh']=dsh#写回
    写配置清单(目录,规范化)#写回磁盘
    return 规范化#返回

def 从锚点解析包目录(锚点,包名):#从锚点解析包目录
    '探测 node_modules 查找顺序'
    当前=os.path.dirname(锚点)#从锚点目录起
    while True:#向上
        候选=os.path.join(当前,'node_modules',包名)#候选
        if os.path.exists(os.path.join(候选,'package.json')):#有清单
            return 候选#命中
        父=os.path.dirname(当前)#上一级
        if 父==当前:#到根
            break#停
        当前=父#继续
    return None#未解析到

def 解析组合包目录(二进制名,包名,安装锚点,配置目录):#解析组合包目录
    '安装锚点优先，然后是配置目录'
    for 锚点 in (安装锚点,os.path.join(配置目录,'package.json')):#两个锚点
        目录=从锚点解析包目录(锚点,包名)#尝试
        if 目录 is not None:#命中
            return 目录#返回
    raise 启动错误(
        二进制名+': 无法解析配置档组合包 '+json.dumps(包名,ensure_ascii=False)
        +"；若依赖未安装，请运行 'dsh plugin --profile "+os.path.basename(配置目录)+" install'"
    )#错误

def 加载配置档(二进制名,名,安装锚点,主目录=None,选项=None):#加载配置
    '加载一个配置：解析每个组合包层并解析用户补丁'
    if 主目录 is None:#缺省
        主目录=解析主目录()#主目录
    if 选项 is None:#缺省
        选项={}#空
    from . import 加载覆盖补丁 as 加载覆盖#延迟导入避免环
    目录=解析配置目录(名,主目录)#解析目录
    if not os.path.exists(os.path.join(目录,'package.json')):#还不存在
        if 名 not in 配置模板:#没有模板
            raise 启动错误(二进制名+': 配置档 '+json.dumps(名,ensure_ascii=False)+" 不存在；请用 'dsh plugin --profile "+名+" add <package>' 创建")#未知
        模板=配置模板[名]#随附模板
        初始化配置档(目录,模板['bundles'])#首次初始化
    拆开配置模块回退(目录)#拆掉旧链接投影
    规范化随附配置(名,目录,读配置清单(二进制名,目录))#规范化随附元组
    已加载=加载配置目录(二进制名,目录,安装锚点,选项)#读层
    已加载['name']=名#配置名
    return 已加载#已加载配置

def 组合条目(各层,警告=None):#组合条目
    '在空根上把补丁层组合成有效条目列表'
    if 警告 is None:#缺省
        警告=lambda 消息:None#静默
    def 记警告(消息,*参数):#警告
        '展开 %C'
        import re,json as 杰#正则与 JSON
        下标=[0]#游标
        def 替(_):#替换
            '取下一参数'
            值=参数[下标[0]] if 下标[0]<len(参数) else None#参数
            下标[0]=下标[0]+1#推进
            return 杰.dumps(值,ensure_ascii=False)#JSON
        警告(re.sub(r'%C',替,消息))#展开
    展平=copy.deepcopy([补丁 for 层 in 各层 for 补丁 in 层])#展平克隆
    return 应用条目补丁([],展平,记警告)#应用

def 愈合模块回退(安装锚点,主目录=None,物化=True):#愈合模块回退
    '维护扁平模块回退 $DSH_HOME/profiles/node_modules。物化为 False 时只计算世代'
    if 主目录 is None:#缺省
        主目录=解析主目录()#主目录
    配置根=os.path.join(主目录,配置目录名)#配置根
    模块目录=os.path.join(配置根,'node_modules')#扁平回退
    if 物化:#写盘
        os.makedirs(模块目录,exist_ok=True)#确保
    应用清单=json.loads(open(安装锚点,encoding='utf-8').read())#应用清单
    链接={}#包名到真实目录
    声明者={}#包名到声明清单路径
    版本表={}#包名到版本
    if 应用清单.get('name') is not None:#有名
        链接[应用清单['name']]=os.path.dirname(安装锚点)#链应用自己
        声明者[应用清单['name']]=安装锚点#声明者
        版本表[应用清单['name']]=应用清单.get('version')#版本
    队列=[{'anchor':安装锚点,'manifest':应用清单}]#BFS
    while 队列:#出队
        当前=队列.pop(0)#出队
        依赖=list((当前['manifest'].get('dependencies') or {}).keys())+list((当前['manifest'].get('peerDependencies') or {}).keys())#依赖
        for 依赖名 in 依赖:#每个依赖
            if 依赖名 in 链接:#已访问
                continue#跳过
            目录=从锚点解析包目录(当前['anchor'],依赖名)#解析
            if 目录 is None:#未安装
                continue#跳过
            链接[依赖名]=目录#记下
            声明者[依赖名]=当前['anchor']#声明者
            清单路径=os.path.join(目录,'package.json')#依赖清单
            依赖清单=json.loads(open(清单路径,encoding='utf-8').read())#读
            版本表[依赖名]=依赖清单.get('version')#版本
            队列.append({'anchor':清单路径,'manifest':依赖清单})#入队
    if 物化:#写链接
        for 包名,目标 in 链接.items():#每条链接
            链接路径=os.path.join(模块目录,包名)#扁平链接
            os.makedirs(os.path.dirname(链接路径),exist_ok=True)#作用域包父目录
            确保符号链接(链接路径,目标)#确保链接
    条目=[]#世代条目
    for 包名,目录 in 链接.items():#安装级
        条目.append({#条目
            'name':包名,
            'packageDir':目录,
            'version':版本表.get(包名),
            'declarer':声明者[包名],
            'scope':'installation',
        })#结束
    return {#世代
        'profilesDir':配置根,
        'profileDir':None,
        'localPackageNames':[],
        'entries':条目,
    }#结束

def 确保符号链接(链接,目标):#确保符号链接
    '确保 link 是指向 target 的符号链接'
    if os.path.lexists(链接):#已存在
        if not os.path.islink(链接):#不是符号链接
            raise 启动错误('dsh: 目标已存在且不是符号链接；请删掉后让 dsh 管理安装回退')#拒绝
        if os.readlink(链接)==目标:#已正确
            return#成功
        os.unlink(链接)#拆掉错误链接
    try:#创建
        os.symlink(目标,链接,target_is_directory=True)#写链接
    except FileExistsError:#竞态
        if not (os.path.islink(链接) and os.readlink(链接)==目标):#不对
            raise#失败

def 已装配置包名(配置):
    '配置清单里已在 node_modules 落地的直接依赖名'
    清单路径=os.path.join(配置['dir'],'package.json')#清单
    if not os.path.exists(清单路径):#没有
        return []#空
    清单=json.loads(open(清单路径,encoding='utf-8').read())#读
    名表=list((清单.get('dependencies') or {}).keys())+list((清单.get('peerDependencies') or {}).keys())#依赖
    return [名 for 名 in 名表 if os.path.exists(os.path.join(配置['dir'],'node_modules',名,'package.json'))]#已装

def 依赖闭包(锚点列表,保留):
    '从锚点做依赖与 peer 闭包；保留集里的名字不再展开'
    链接={}#名到目录
    声明者={}#名到声明清单
    版本表={}#名到版本
    已访=set(保留)#已访问
    for 锚点 in 锚点列表:#每个锚点
        清单=json.loads(open(锚点,encoding='utf-8').read())#清单
        名=清单.get('name')#包名
        if not isinstance(名,str):#无名
            continue#跳过
        if 名 not in 已访:#新包
            已访.add(名)#记下
            链接[名]=os.path.dirname(锚点)#目录
            声明者[名]=锚点#声明者
            版本表[名]=清单.get('version')#版本
        队列=[{'anchor':锚点,'manifest':清单}]#BFS
        while 队列:#出队
            当前=队列.pop(0)#出队
            依赖=list((当前['manifest'].get('dependencies') or {}).keys())+list((当前['manifest'].get('peerDependencies') or {}).keys())#依赖
            for 依赖名 in 依赖:#每个依赖
                if 依赖名 in 已访:#已访问
                    continue#跳过
                目录=从锚点解析包目录(当前['anchor'],依赖名)#解析
                if 目录 is None:#未安装
                    continue#跳过
                已访.add(依赖名)#记下
                链接[依赖名]=目录#目录
                清单路径=os.path.join(目录,'package.json')#依赖清单
                依赖清单=json.loads(open(清单路径,encoding='utf-8').read())#读
                声明者[依赖名]=当前['anchor']#声明者
                版本表[依赖名]=依赖清单.get('version')#版本
                队列.append({'anchor':清单路径,'manifest':依赖清单})#入队
    return 链接,声明者,版本表#闭包

def 链接配置根(配置,配置根):
    '活动配置 node_modules 里指向配置树与活动配置之外的目录链接'
    模块目录=os.path.join(配置['dir'],'node_modules')#模块目录
    链接=模块符号链接(模块目录)#符号链接
    if len(链接)==0:#没有
        return []#空
    try:#配置树真实路径
        树=os.path.realpath(配置根)+os.sep#前缀
    except OSError as 错误:#尚未物化
        if getattr(错误,'errno',None)!=2:#不是缺失
            raise#失败
        树=os.path.abspath(配置根)+os.sep#字面前缀
    排除=[树,os.path.realpath(配置['dir'])+os.sep]#排除树
    根表=[]#结果
    for 链接路径 in 链接:#逐条
        try:#真实目录
            真实=os.path.realpath(链接路径)#真实
        except OSError as 错误:#断链
            if getattr(错误,'errno',None)==2:#缺失
                continue#不是可加载包
            raise#失败
        if any(真实+os.sep==前缀 or 真实.startswith(前缀) for 前缀 in 排除) or not os.path.isdir(真实):#在排除树内或不是目录
            continue#跳过
        相对=os.path.relpath(链接路径,模块目录).replace(os.sep,'/')#包名
        根表.append({'name':相对,'realPath':真实})#收下
    根表.sort(key=lambda 项:项['name'])#按名
    return 根表#列表

def 创建配置解析世代(选项):
    '不写模块解析文件，计算一代配置解析表。选项为 dict'
    主目录=选项['home'] if 'home' in 选项 else None#可选主目录
    配置=选项.get('profile')#可选已加载配置
    安装=愈合模块回退(选项['installAnchor'],主目录,False)#安装条目
    安装名=set(条['name'] for 条 in 安装['entries'])#安装包名
    本地=[]#本地包名
    链接根=[]#外部链接根
    配置条目=[]#配置级条目
    if isinstance(配置,dict):#有配置
        本地=已装配置包名(配置)#已装直接依赖
        锚点=[]#组合包锚点
        for 层 in 配置.get('layers') or []:#组合包层
            if 层['packageName'] not in 安装名:#安装未供给
                锚点.append(os.path.join(层['packageDir'],'package.json'))#锚点
        链接,声明者,版本表=依赖闭包(锚点,安装名)#闭包
        for 层 in 配置.get('layers') or []:#去掉组合包自己
            链接.pop(层['packageName'],None)#删除
        for 名,目录 in 链接.items():#配置级
            配置条目.append({#条目
                'name':名,
                'packageDir':目录,
                'version':版本表.get(名),
                'declarer':声明者[名],
                'scope':'profile',
            })#结束
        链接根=链接配置根(配置,安装['profilesDir'])#外部链接
    安装['localPackageNames']=本地#本地包
    安装['linkedRoots']=链接根#链接根
    安装['entries']=list(安装['entries'])+配置条目#合并
    安装['profileDir']=配置['dir'] if isinstance(配置,dict) else None#活动配置
    安装['_source']={'installAnchor':选项['installAnchor'],'home':主目录,'profileDir':安装['profileDir']}#重算输入
    return 安装#世代

def 愈合隔离配置模块回退(选项):
    '应用自有配置：从安装与所选组合包供给文件系统包，不写共享主目录。选项为 dict'
    安装世代=愈合模块回退(选项['installAnchor'],None,False)#安装条目
    安装链接={条['name']:条['packageDir'] for 条 in 安装世代['entries']}#名→目录
    安装名=set(安装链接.keys())#安装包名
    配置=选项['profile']#已加载配置
    配置模块=os.path.join(配置['dir'],'node_modules')#配置 node_modules
    拥有模块=os.path.join(配置['dir'],'.dsh-module-fallback','node_modules')#拥有目录
    os.makedirs(配置模块,exist_ok=True)#配置 node_modules
    os.makedirs(拥有模块,exist_ok=True)#拥有目录
    链接=dict(安装链接)#合并安装链接
    for 层 in 配置.get('layers') or []:#组合包层
        包名=层['packageName']#包名
        if 包名 in 安装名:#安装已覆盖
            continue#跳过
        链接[包名]=层['packageDir']#组合包目录
    for 包名,目标 in 链接.items():#逐条物化
        拥有链接=os.path.join(拥有模块,包名)#托管链接
        os.makedirs(os.path.dirname(拥有链接),exist_ok=True)#作用域父目录
        确保符号链接(拥有链接,目标)#写托管
        投影=os.path.join(配置模块,包名)#投影
        os.makedirs(os.path.dirname(投影),exist_ok=True)#作用域
        if not os.path.lexists(投影):#不替换 pnpm
            确保符号链接(投影,拥有链接)#投影

def 模块符号链接(模块目录):
    'node_modules 顶层与作用域下的符号链接'
    链接=[]#结果
    if not os.path.exists(模块目录):#无目录
        return 链接#空
    for 名 in os.listdir(模块目录):#顶层
        路径=os.path.join(模块目录,名)#完整路径
        if os.path.islink(路径):#符号链接
            链接.append(路径)#收下
        elif 名.startswith('@') and os.path.isdir(路径) and not os.path.islink(路径):#作用域目录
            for 子 in os.listdir(路径):#作用域内
                子路径=os.path.join(路径,子)#子路径
                if os.path.islink(子路径):#符号链接
                    链接.append(子路径)#收下
    return 链接#列表

def 指向内部(链接,根):
    '符号链接目标目录是否为根或落在根下'
    try:#解析目标
        目标=os.path.normpath(os.path.join(os.path.dirname(链接),os.readlink(链接)))#目标
        父=os.path.realpath(os.path.dirname(目标))#目标父目录
        根路径=os.path.realpath(根)#根
        return 父==根路径 or 父.startswith(根路径+os.sep)#在根内
    except OSError as 错误:#目标父目录已不在
        if getattr(错误,'errno',None)==2:#缺失
            return False#不是本启动拥有的投影
        raise#其余失败

def 拆开配置模块回退(配置目录):
    '拆掉配置 node_modules 里指向 .dsh-module-fallback 的投影，再删掉该目录'
    拥有=os.path.join(配置目录,'.dsh-module-fallback')#投影目录
    if not os.path.exists(拥有):#没有
        return#不动
    拥有模块=os.path.join(拥有,'node_modules')#托管模块
    for 链接 in 模块符号链接(os.path.join(配置目录,'node_modules')):#配置链接
        if 指向内部(链接,拥有模块):#指向托管
            os.unlink(链接)#拆掉
    shutil.rmtree(拥有,ignore_errors=True)#删投影目录

def 加载配置目录(二进制名,目录,安装锚点,选项=None):
    '加载已经初始化的配置目录，不经共享主目录解析。不可读组合包记入 skippedBundles'
    if 选项 is None:#缺省
        选项={}#空
    from . import 加载覆盖补丁 as 加载覆盖#延迟导入避免环
    清单=丢掉退役组合包(目录,读配置清单(二进制名,目录))#去掉退役组合包
    配置段=((清单.get('dsh') or {}).get('profile') or {})#profile
    组合包列表=配置段.get('bundles') or []#组合包列表
    层列表=[]#层
    跳过=[]#跳过的组合包
    for 包名 in 组合包列表:#每层
        try:#一层失败不中断
            包目录=解析组合包目录(二进制名,包名,安装锚点,目录)#解析包目录
            包清单=json.loads(open(os.path.join(包目录,'package.json'),encoding='utf-8').read())#读组合包清单
            组合包=((包清单.get('dsh') or {}).get('bundle'))#声明
            if not isinstance(组合包,dict):#没有
                raise 启动错误(二进制名+': 配置档组合包 '+json.dumps(包名,ensure_ascii=False)+' 的 package.json 未声明 dsh.bundle')#错误配置
            补丁路径表=组合包补丁路径(包目录,组合包)#全部补丁
            补丁=[]#合并补丁
            for 补丁路径 in 补丁路径表:#逐文件
                补丁.extend(加载覆盖(二进制名,补丁路径))#追加
            层列表.append({'packageName':包名,'packageDir':包目录,'patchPath':补丁路径表[0] if 补丁路径表 else None,'patchPaths':补丁路径表,'patches':补丁})#已解析层
        except Exception as 错误:#跳过
            跳过.append({'packageName':包名,'reason':str(错误)})#记下
    补丁路径=os.path.join(目录,配置补丁文件名)#用户补丁
    用户层=选项.get('userLayer',True)#是否读用户层
    补丁=加载覆盖(二进制名,补丁路径) if 用户层 and os.path.exists(补丁路径) else []#用户补丁
    return {'name':os.path.basename(目录),'dir':目录,'layers':层列表,'patchPath':补丁路径,'patches':补丁,'skippedBundles':跳过}#已加载配置

