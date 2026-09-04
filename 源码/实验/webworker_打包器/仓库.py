"""打包器的仓库知识：本树的 workspace、profile 组合与配置树在哪，以及如何报告一次打包。

库半边把这些全部当参数接收。查找留在这里，才能让同一库打另一棵树，并让 `打包` 不假设 pnpm workspace 或 `dsh` CLI。

对齐上游 `webworker-packer/src/repository.ts`。公开面仅中文名。
"""
import json,os,shutil,subprocess,sys,tempfile#子进程、文件系统与临时目录
from ...工具.主目录路径 import 主目录环境键#DSH_HOME环境键

__all__=[#仅中文公开名
    '索引工作区包','组合配置档','配置树列表','预览夹具列表','描述打包',
]#公开面结束

工作区扫描根=['vendor','packages','native/landlock-run/packages','apps']#扫描根

命令行包='apps/cli'#CLI包路径

命令行入口=命令行包+'/src/bin.ts'#CLI入口

预览示例根='packages/experimental/webworker-runtime/tests/fixtures/vfs-example'#示例根

def 索引工作区包(仓库根):#按名索引每一个workspace与vendored包
    """按名索引每一个 workspace 与 vendored 包。

    对齐上游 `indexWorkspacePackages`。
    """
    索引={}#包名到绝对目录
    def 访问(目录):#递归访问目录
        清单=os.path.join(目录,'package.json')#清单路径
        if os.path.exists(清单):#是包根
            名=json.loads(open(清单,'r',encoding='utf-8').read()).get('name')#包名
            if isinstance(名,str):索引[名]=目录#入索引
            #包根拥有其子树；其下（测试夹具、嵌套清单）不是独立workspace包。
            return#包根止步
        for 名字 in os.listdir(目录):#枚举子项
            if 名字=='node_modules' or 名字.startswith('.'):continue#跳过
            绝对=os.path.join(目录,名字)#绝对路径
            if not os.path.isdir(绝对):continue#非目录
            访问(绝对)#递归
    for 扫描根 in 工作区扫描根:#每个扫描根
        绝对=os.path.join(仓库根,扫描根)#绝对扫描根
        if os.path.exists(绝对):访问(绝对)#存在则扫
    return 索引#返回索引

def 组合配置档(仓库根,配置档):#经真实CLI dump路径组合profile
    """经真实 CLI dump 路径组合一个 profile，`!!js` 保持未求值。

    对齐上游 `composeProfile`。
    """
    家=tempfile.mkdtemp(prefix='dsh-pack-home-',dir=tempfile.gettempdir())#临时主目录
    try:#跑CLI dump
        环境=dict(os.environ)#复制环境
        环境[主目录环境键]=家#隔离DSH_HOME
        return subprocess.check_output(#跑CLI dump
            [sys.executable,'--import','tsx/esm',os.path.join(仓库根,命令行入口),'--profile',配置档,'--dump-default-config'],#argv
            cwd=仓库根,encoding='utf-8',env=环境,#选项
        )#返回YAML文本
    finally:#清临时家
        shutil.rmtree(家,ignore_errors=True)#清临时家

def 配置树列表(仓库根):#读CLI包声明的配置树
    """CLI 包为部署镜像声明的配置树（其 package.json 的 `dsh.configTrees`）。

    对齐上游 `configTrees`。
    """
    包目录=os.path.join(仓库根,命令行包)#CLI目录
    清单=json.loads(open(os.path.join(包目录,'package.json'),'r',encoding='utf-8').read())#读清单
    声明=(清单.get('dsh') or {}).get('configTrees')#声明
    if 声明 is None:return []#无则空
    if not isinstance(声明,list):#须数组
        raise Exception('vfs image: '+命令行包+' dsh.configTrees must be an array')#须数组
    挂载们=set()#挂载去重
    结果=[]#输出树
    for 下标,条目 in enumerate(声明):#逐条校验
        树=条目 if isinstance(条目,dict) else None#收窄
        位点=命令行包+' dsh.configTrees['+str(下标)+']'#位点
        if (树 is None#非对象
            or not isinstance(树.get('mount'),str) or 树.get('mount')==''#mount
            or not isinstance(树.get('path'),str) or 树.get('path')==''#path
            or (树.get('scanRoster') is not None and not isinstance(树.get('scanRoster'),bool))):#scanRoster
            raise Exception('vfs image: '+位点+' must declare a string mount, a string path, and an optional boolean scanRoster')#拒绝
        if 树['mount'] in 挂载们:#重复挂载
            raise Exception('vfs image: '+位点+' repeats mount '+json.dumps(树['mount']))#重复挂载
        挂载们.add(树['mount'])#记入
        一项={'mount':树['mount'],'directory':os.path.join(包目录,树['path'])}#绝对源目录
        if 树.get('scanRoster') is not None:一项['scanRoster']=树['scanRoster']#可选扫roster
        结果.append(一项)#追加
    return 结果#带绝对源目录的树

def 预览夹具列表(仓库根):#仓库预览提供的内置文件系统夹具
    """仓库预览提供的内置文件系统 fixture。

    对齐上游 `previewFixtures`。
    """
    根=os.path.join(仓库根,预览示例根)#示例根
    return [{#具名选择器条目
        'id':'vfs-example',#标识
        'label':'Built-in showcase',#标签
        'description':'Sample workspace, tool cards, subagents, and paged history.',#描述
        'trees':[{'mount':挂载,'directory':os.path.join(根,挂载)} for 挂载 in ['home','workspace']],#overlay树
    }]#列表结束

def 描述打包(结果,仓库根,输出文件):#把一次打包渲染成构建日志行
    """把一次打包渲染成构建日志应携带的行。

    对齐上游 `describePack`。
    """
    def 前缀大小(前缀):#前缀下字节和
        return sum(len(字节) for 名,字节 in 结果['files'].items() if 名.startswith(前缀))#字节和
    def 兆字节(字节数):#MB文案
        return f'{字节数/1024/1024:.2f} MB'#MB文案
    工作区数=结果['workspacePackages']#workspace数
    def 按字节(项):#排序键
        return 项['bytes']#字节数
    最重=sorted(#最重包
        [{'name':名,'count':计数,'bytes':前缀大小('node_modules/'+名+'/')} for 名,计数 in 结果['packages'].items()],#条目
        key=按字节,#按字节
        reverse=True,#降序
    )[:12]#最重12个
    行们=[#报告行
        'vfs image: '+os.path.relpath(输出文件,仓库根),#输出相对路径
        '  roster entries      '+str(len(结果['roster'])),#名册条数
        '  packages            '+str(len(结果['packages']))+' ('+str(工作区数)+' workspace)',#包数
        '  files               '+str(len(结果['files'])),#文件数
        '  raw                 '+兆字节(sum(len(字节) for 字节 in 结果['files'].values())),#原始
        '  compressed          '+兆字节(len(结果['image'])),#压缩
        '  config + presets    '+兆字节(前缀大小('config/')),#配置
        '  javascript entries  '+str(结果['javascriptEntries'])+' (dropped '+str(len(结果['executables']))+' executable scripts, '+str(len(结果['pageBundles']))+' page bundles verbatim)',#JS
        '  wrapper contract    '+结果['contract'],#契约
        '  transform           '+str(结果['transform']['rewritten'])+' of '+str(结果['transform']['visited'])+' reached entries rewritten, '+str(结果['droppedJavascriptEntries'])+' unreachable dropped',#变换
        '  unresolved          '+str(len(结果['unresolvedExternalRequests']))+' third-party request(s) left to fail loud at require time',#未解析
        '  heaviest packages:',#最重标题
    ]#行们前半
    行们+=['    '+str(项['bytes']).rjust(9)+' B  '+项['name']+' ('+str(项['count'])+' files)' for 项 in 最重]#最重行
    if len(结果['missing'])>0:#有缺失
        行们+=['  unresolved dependencies:']+[('    '+项) for 项 in 结果['missing']]#缺失行
    行们.append('')#尾空行
    return 行们#要打印的行
