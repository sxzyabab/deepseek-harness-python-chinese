"""`dsh --profile` 启动器家族的配置发现、初始化与补丁层组合。

对齐上游 `app-boot/src/profile.ts`。公开面仅中文名。
"""
import os,json,copy#路径、JSON、克隆
from include import 应用条目补丁#补丁应用
from home_paths import 解析主目录#主目录解析

__all__=[#仅中文公开名
    '配置目录名','配置补丁文件名','配置模板','默认组合包',
    '解析配置目录','初始化配置档','愈合模块回退','读配置清单','写配置清单',
    '解析组合包目录','加载配置档','组合条目',
]#公开面结束

配置目录名='profiles'#配置目录名
配置补丁文件名='cordis.patch.yml'#用户补丁文件名
配置模板={#随附模板
    'web':['@deepseek-ai/dsh-base','@deepseek-ai/dsh-web-app'],#Web
    'headless':['@deepseek-ai/dsh-base','@deepseek-ai/dsh-headless'],#无头
}#模板结束
安装拥有元组={#安装拥有元组
    'headless':['@deepseek-ai/dsh-base','@deepseek-ai/dsh-web-app','@deepseek-ai/dsh-headless'],#旧无头
}#元组结束
默认组合包=['@deepseek-ai/dsh-base']#默认组合包
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
    """在 Harness 主目录下解析一个配置的目录。"""
    if 主目录 is None:#缺省
        主目录=解析主目录()#主目录
    if 名=='' or '/' in 名 or '\\' in 名 or 名 in ('.','..','node_modules'):#非法名
        raise Exception('dsh: invalid profile name '+json.dumps(名))#拒绝
    return os.path.join(主目录,配置目录名,名)#拼目录

def 初始化配置档(目录,组合包们):#初始化配置
    """初始化一个配置目录。"""
    os.makedirs(目录,exist_ok=True)#确保目录
    清单路径=os.path.join(目录,'package.json')#清单
    if not os.path.exists(清单路径):#没有清单
        清单={#新清单
            'name':'dsh-profile-'+os.path.basename(目录),#包名
            'private':True,#私有
            'dependencies':{},#空依赖
            'dsh':{'profile':{'bundles':list(组合包们)}},#组合包列表
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
    """读一个配置的清单。"""
    路径=os.path.join(目录,'package.json')#清单路径
    try:#读
        文件=open(路径,'r',encoding='utf-8')#打开
        try:#读
            原文=文件.read()#原文
        finally:#关
            文件.close()#关闭
    except OSError as 错误:#读失败
        raise Exception(二进制名+': failed to read profile manifest '+路径+': '+str(错误))#包装
    解析=json.loads(原文)#解析
    if not isinstance(解析,dict) or 解析 is None:#非对象
        raise Exception(二进制名+': profile manifest '+路径+' must hold a JSON object')#拒绝
    return 解析#清单

def 写配置清单(目录,清单):#写配置清单
    """把配置清单写回。"""
    文件=open(os.path.join(目录,'package.json'),'w',encoding='utf-8')#打开
    try:#写
        文件.write(json.dumps(清单,ensure_ascii=False,indent=2)+'\n')#写
    finally:#关
        文件.close()#关闭

def 同组合包(左,右):#列表是否相同
    """两个组合包列表是否同值同序。"""
    return len(左)==len(右) and all(左[下标]==右[下标] for 下标 in range(len(左)))#比较

def 规范化随附配置(名,目录,清单):#规范化随附配置
    """把恰好是安装拥有的组合包元组规范化到其随附模板。"""
    拥有=安装拥有元组.get(名)#安装拥有
    当前=配置模板.get(名)#当前模板
    组合包=((清单.get('dsh') or {}).get('profile') or {}).get('bundles')#当前列表
    if 拥有 is None or 当前 is None or 组合包 is None or not 同组合包(组合包,拥有):#不是
        return 清单#原样
    规范化=dict(清单)#拷贝
    dsh=dict(清单.get('dsh') or {})#dsh
    配置=dict(dsh.get('profile') or {})#profile
    配置['bundles']=list(当前)#换成模板
    dsh['profile']=配置#写回
    规范化['dsh']=dsh#写回
    写配置清单(目录,规范化)#写回磁盘
    return 规范化#返回

def 从锚点解析包目录(锚点,包名):#从锚点解析包目录
    """探测 node_modules 查找顺序。"""
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
    """安装锚点优先，然后是配置目录。"""
    for 锚点 in (安装锚点,os.path.join(配置目录,'package.json')):#两个锚点
        目录=从锚点解析包目录(锚点,包名)#尝试
        if 目录 is not None:#命中
            return 目录#返回
    raise Exception(
        二进制名+': cannot resolve profile bundle '+json.dumps(包名)+' from the dsh installation or '+配置目录+'; '
        +"run 'dsh plugin --profile "+os.path.basename(配置目录)+" install' if its dependency is not installed"
    )#错误

def 加载配置档(二进制名,名,安装锚点,主目录=None,选项=None):#加载配置
    """加载一个配置：解析每个组合包层并解析用户补丁。"""
    if 主目录 is None:#缺省
        主目录=解析主目录()#主目录
    if 选项 is None:#缺省
        选项={}#空
    from . import 加载覆盖补丁 as 加载覆盖#延迟导入避免环
    目录=解析配置目录(名,主目录)#解析目录
    if not os.path.exists(os.path.join(目录,'package.json')):#还不存在
        模板=配置模板.get(名)#随附模板
        if 模板 is None:#没有模板
            raise Exception(二进制名+': profile '+json.dumps(名)+" does not exist; create it with 'dsh plugin --profile "+名+" add <package>'")#未知
        初始化配置档(目录,模板)#首次初始化
    清单=规范化随附配置(名,目录,读配置清单(二进制名,目录))#读并规范化
    组合包们=((清单.get('dsh') or {}).get('profile') or {}).get('bundles') or []#组合包列表
    层们=[]#层
    for 包名 in 组合包们:#每层
        包目录=解析组合包目录(二进制名,包名,安装锚点,目录)#解析包目录
        包清单=json.loads(open(os.path.join(包目录,'package.json'),encoding='utf-8').read())#读组合包清单
        声明=((包清单.get('dsh') or {}).get('bundle') or {}).get('patch')#声明的补丁
        if 声明 is None:#没有
            raise Exception(二进制名+': profile bundle '+json.dumps(包名)+' declares no dsh.bundle in its package.json')#错误配置
        补丁路径=os.path.join(包目录,声明)#绝对补丁
        层们.append({'packageName':包名,'packageDir':包目录,'patchPath':补丁路径,'patches':加载覆盖(二进制名,补丁路径)})#已解析层
    补丁路径=os.path.join(目录,配置补丁文件名)#用户补丁
    用户层=选项.get('userLayer',True)#是否读用户层
    补丁=加载覆盖(二进制名,补丁路径) if 用户层 and os.path.exists(补丁路径) else []#用户补丁
    return {'name':名,'dir':目录,'layers':层们,'patchPath':补丁路径,'patches':补丁}#已加载配置

def 组合条目(各层,警告=None):#组合条目
    """在空根上把补丁层组合成有效条目列表。"""
    if 警告 is None:#缺省
        警告=lambda 消息:None#静默
    def 记警告(消息,*参数):#警告
        """展开 %C。"""
        import re,json as 杰#正则与 JSON
        下标=[0]#游标
        def 替(_):#替换
            """取下一参数。"""
            值=参数[下标[0]] if 下标[0]<len(参数) else None#参数
            下标[0]=下标[0]+1#推进
            return 杰.dumps(值,ensure_ascii=False)#JSON
        警告(re.sub(r'%C',替,消息))#展开
    展平=copy.deepcopy([补丁 for 层 in 各层 for 补丁 in 层])#展平克隆
    return 应用条目补丁([],展平,记警告)#应用

def 愈合模块回退(安装锚点,主目录=None):#愈合模块回退
    """维护扁平模块回退 $DSH_HOME/profiles/node_modules。"""
    if 主目录 is None:#缺省
        主目录=解析主目录()#主目录
    配置根=os.path.join(主目录,配置目录名)#配置根
    模块目录=os.path.join(配置根,'node_modules')#扁平回退
    os.makedirs(模块目录,exist_ok=True)#确保
    应用清单=json.loads(open(安装锚点,encoding='utf-8').read())#应用清单
    链接={}#包名到真实目录
    if 应用清单.get('name') is not None:#有名
        链接[应用清单['name']]=os.path.dirname(安装锚点)#链应用自己
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
            清单路径=os.path.join(目录,'package.json')#依赖清单
            队列.append({'anchor':清单路径,'manifest':json.loads(open(清单路径,encoding='utf-8').read())})#入队
    for 包名,目标 in 链接.items():#每条链接
        链接路径=os.path.join(模块目录,包名)#扁平链接
        os.makedirs(os.path.dirname(链接路径),exist_ok=True)#作用域包父目录
        确保符号链接(链接路径,目标)#确保链接

def 确保符号链接(链接,目标):#确保符号链接
    """确保 link 是指向 target 的符号链接。"""
    if os.path.lexists(链接):#已存在
        if not os.path.islink(链接):#不是符号链接
            raise Exception('dsh: '+链接+' exists and is not a symlink; remove it so dsh can manage the installation fallback')#拒绝
        if os.readlink(链接)==目标:#已正确
            return#成功
        os.unlink(链接)#拆掉错误链接
    try:#创建
        os.symlink(目标,链接,target_is_directory=True)#写链接
    except FileExistsError:#竞态
        if not (os.path.islink(链接) and os.readlink(链接)==目标):#不对
            raise#失败
