import json,os,re#清单与路径、装饰器检测

__all__=[#公开面
    'typert插件','输出制品',
    '有Typert导出','读清单',
    '包根','工作区根',
]#结束

装饰器语法=re.compile(r'^\s*@[A-Za-z_$][\w$]*',re.M)#检测源码中的标准装饰器

def typert插件(插件选项=None):#创建装饰器降低与 typert 生成插件外壳
    """组装兼容 rolldown 钩子约定的插件字典。

    writeBundle 在需要 discover/generate 时显式失败（硬缺口 analyzer）；
    不静默跳过、不伪造制品。
    """
    if 插件选项 is None:#缺省空选项
        插件选项={}#空映射
    def 转译(代码,标识):#在打包前降低装饰器（可落：跳过判定）
        """非 TypeScript 或无装饰器则跳过；真正降低依赖 TS。"""
        文件=标识.split('?',1)[0] if isinstance(标识,str) else 标识#去掉查询串
        if not re.search(r'\.[cm]?tsx?$',文件) or not 装饰器语法.search(代码):#非 TS 或无装饰器
            return None#跳过
        raise NotImplementedError(#真正降低依赖 TS transpileModule
            'typert插件.转译: 装饰器降低依赖 TypeScript transpileModule，本 Python 叶不实现'
        )#结束
    def 写包(打包选项):#写包后发射 typert 制品
        """工作区或单包 generate 依赖分析器，显式失败。"""
        目录=打包选项['dir'] if isinstance(打包选项,dict) and 'dir' in 打包选项 else getattr(打包选项,'dir',None)#输出目录
        if 目录 is None:#没有输出目录
            return#跳过
        根=工作区根(目录)#向上找到工作区根
        if 'mode' in 插件选项 and 插件选项['mode']=='workspace':#工作区模式
            raise NotImplementedError(#禁止假实现 discover/generate
                'typert插件.写包: 工作区模式 discover/generate 依赖硬缺口 analyzer，不可落'
            )#结束
        包目录=包根(目录,根)#找到正在打包的包根
        if 包目录 is None:#找不到 package.json
            return#跳过
        清单=读清单(包目录)#读清单
        if ('name' not in 清单) or 清单['name'] is None or not 有Typert导出(清单['exports'] if 'exports' in 清单 else None):#无包名或无 typert 导出
            return#跳过
        raise NotImplementedError(#禁止假实现 generate
            'typert插件.写包: 工作区Typert生成器.generate 依赖硬缺口 analyzer，不可落'
        )#结束
    return {#组装插件对象
        'name':'dsh-typert-generator',#rolldown 插件名
        'transform':转译,#转译钩子
        'writeBundle':写包,#写包钩子
    }#结束插件

def 输出制品(包目录,制品列表):#把制品写到包的 lib/
    """对齐上游 emitArtifacts：写 typert.<face> 与可选 remote-client，并清理陈旧 Remote。"""
    输出=os.path.join(包目录,'lib')#输出目录
    os.makedirs(输出,exist_ok=True)#确保目录存在
    是否已写远程=False#是否写过 remote-client 制品
    for 制品 in 制品列表:#逐面制品
        面=制品['face']#面名
        with open(os.path.join(输出,'typert.'+面+'.js'),'w',encoding='utf-8',newline='\n') as 文件:#写 JS
            文件.write(制品['js'])#正文
        with open(os.path.join(输出,'typert.'+面+'.d.ts'),'w',encoding='utf-8',newline='\n') as 文件:#写声明
            文件.write(制品['dts'])#正文
        远程=制品['remote'] if 'remote' in 制品 else None#Host-for-Client Remote
        if 远程 is not None:#有 Remote 制品
            是否已写远程=True#记下已写
            with open(os.path.join(输出,'typert.remote-client.js'),'w',encoding='utf-8',newline='\n') as 文件:#写 Remote JS
                文件.write(远程['js'])#正文
            with open(os.path.join(输出,'typert.remote-client.d.ts'),'w',encoding='utf-8',newline='\n') as 文件:#写 Remote 声明
                文件.write(远程['dts'])#正文
            with open(os.path.join(输出,'typert.remote-client.d.ts.map'),'w',encoding='utf-8',newline='\n') as 文件:#写 Remote map
                文件.write(远程['dtsMap'])#正文
    if not 是否已写远程 and any(制品['face']=='host' for 制品 in 制品列表):#宿主面但无 Remote
        for 名 in ('typert.remote-client.js','typert.remote-client.d.ts','typert.remote-client.d.ts.map'):#陈旧文件
            路径=os.path.join(输出,名)#绝对路径
            if os.path.isfile(路径):#仍存在
                os.remove(路径)#删除

def 读清单(包目录):#读包清单
    """解析 package.json 为字典。"""
    with open(os.path.join(包目录,'package.json'),'r',encoding='utf-8') as 文件:#读清单
        return json.load(文件)#解析

def 有Typert导出(导出字段):#清单是否声明了 typert 相关导出
    """有 ./typert、./client/typert 或 ./remote 之一即真。"""
    if 导出字段 is None or not isinstance(导出字段,dict):#非对象则无
        return False#无
    return './typert' in 导出字段 or './client/typert' in 导出字段 or './remote' in 导出字段#三选一

def 包根(起点,工作区):#从输出目录向上找包根
    """最近含 package.json 且未越过工作区根的目录；否则 None。"""
    当前=os.path.abspath(起点)#从绝对路径开始
    工作区绝对=os.path.abspath(工作区)#工作区绝对路径
    while 当前!=工作区绝对:#尚未走到工作区根
        if os.path.isfile(os.path.join(当前,'package.json')):#找到最近清单
            return 当前#包根
        父=os.path.dirname(当前)#再上一层
        if 父==当前:#已到文件系统根
            break#退出
        当前=父#继续
    return None#走到工作区根仍没有

def 工作区根(起点):#从输出目录向上找工作区根
    """含 tsconfig.host.json 的目录；找不到则抛错。"""
    当前=os.path.abspath(起点)#从绝对路径开始
    while not os.path.isfile(os.path.join(当前,'tsconfig.host.json')):#尚未见到宿主 tsconfig
        父=os.path.dirname(当前)#上一层
        if 父==当前:#到文件系统根仍没有
            raise FileNotFoundError('typert-generator: 在 '+起点+' 之上找不到工作区根')#对齐上游文案
        当前=父#继续向上
    return 当前#含 tsconfig.host.json 的目录
