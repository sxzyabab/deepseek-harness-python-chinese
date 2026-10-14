import json,os,re
from .工作区 import 工作区Typert生成器
from .异常 import Typert代码输出错误

__all__=[
    'typert插件','输出制品',
    '有Typert导出','读清单',
    '包根','工作区根',
]

装饰器语法=re.compile(r'^\s*@[A-Za-z_$][0-9A-Za-z_$]*',re.M|re.ASCII)
脚本后缀=re.compile(r'\.[cm]?tsx?$',re.ASCII)

def typert插件(插件选项=None):
    '组装打包钩子。装饰器降低和制品生成都走工作区生成器'
    if 插件选项 is None:
        插件选项={}
    按根制品={}
    已输出工作区=set()

    def 转译(代码,标识):
        '非脚本或没有装饰器则跳过。有装饰器时需要 TypeScript 转译'
        文件=标识.split('?',1)[0] if isinstance(标识,str) else 标识
        if not isinstance(文件,str) or 脚本后缀.search(文件) is None or 装饰器语法.search(代码) is None:
            return None
        raise Typert代码输出错误('typert-generator: 装饰器降低需要 TypeScript 转译')

    def 输出工作区(根,面列表):
        '先发现声明了 typert 导出的包，再只生成这些包'
        生成器=工作区Typert生成器(根,{'检查诊断':False})
        包列表=[]
        for 候选 in 生成器.discover(面列表):
            清单=读清单(os.path.join(根,候选['root']))
            if 有Typert导出(清单['exports'] if 'exports' in 清单 else None):
                包列表.append(候选['package'])
        if len(包列表)==0:
            return
        for 制品 in 生成器.generate(包列表,面列表):
            输出制品(os.path.join(根,制品['packageRoot']),[制品])

    def 写包(打包选项):
        '写包后按包或按工作区输出制品。同一工作区根只输出一次'
        目录=打包选项['dir'] if isinstance(打包选项,dict) and 'dir' in 打包选项 else None
        if 目录 is None:
            return
        根=工作区根(目录)
        if 根 in 已输出工作区:
            return
        面列表=插件选项['faces'] if 'faces' in 插件选项 else None
        if 插件选项.get('mode')=='workspace':
            输出工作区(根,面列表)
            已输出工作区.add(根)
            return
        包目录=包根(目录,根)
        if 包目录 is None:
            return
        清单=读清单(包目录)
        if 'name' not in 清单 or 清单['name'] is None or not 有Typert导出(清单['exports'] if 'exports' in 清单 else None):
            return
        制品列表=按根制品.get(根)
        if 制品列表 is None:
            生成器=工作区Typert生成器(根,{'检查诊断':False})
            制品列表=生成器.generate(None,面列表)
            按根制品[根]=制品列表
        输出制品(包目录,[制品 for 制品 in 制品列表 if 制品['package']==清单['name']])

    return {
        'name':'dsh-typert-generator',
        'transform':转译,
        'writeBundle':写包,
    }

def 输出制品(包目录,制品列表):
    '写 typert.<face> 与可选 remote-client。宿主面没有 Remote 时删掉陈旧文件'
    输出=os.path.join(包目录,'lib')
    os.makedirs(输出,exist_ok=True)
    是否已写远程=False
    for 制品 in 制品列表:
        面=制品['face']
        写文本(os.path.join(输出,'typert.'+面+'.js'),制品['js'])
        写文本(os.path.join(输出,'typert.'+面+'.d.ts'),制品['dts'])
        远程=制品['remote'] if 'remote' in 制品 else None
        if 远程 is not None:
            是否已写远程=True
            写文本(os.path.join(输出,'typert.remote-client.js'),远程['js'])
            写文本(os.path.join(输出,'typert.remote-client.d.ts'),远程['dts'])
            写文本(os.path.join(输出,'typert.remote-client.d.ts.map'),远程['dtsMap'])
    if not 是否已写远程 and any(制品['face']=='host' for 制品 in 制品列表):
        for 名 in ('typert.remote-client.js','typert.remote-client.d.ts','typert.remote-client.d.ts.map'):
            路径=os.path.join(输出,名)
            if os.path.isfile(路径):
                os.remove(路径)

def 写文本(路径,正文):
    '以换行结尾的 UTF-8 文本写入，不把路径写进异常说明'
    try:
        文件=open(路径,'w',encoding='utf-8',newline='\n')
    except OSError:
        raise OSError('typert-generator: 文本写不进去') from None
    try:
        try:
            文件.write(正文)
        except OSError:
            raise OSError('typert-generator: 文本写不进去') from None
    finally:
        文件.close()

def 读清单(包目录):
    '解析 package.json 为字典。读不到时说明里不带路径'
    try:
        文件=open(os.path.join(包目录,'package.json'),'r',encoding='utf-8')
    except OSError:
        raise OSError('typert-generator: 清单读不到') from None
    try:
        return json.load(文件)
    finally:
        文件.close()

def 有Typert导出(导出字段):
    '有 ./typert、./client/typert 或 ./remote 之一即真。空对象为假'
    if not isinstance(导出字段,dict):
        return False
    return './typert' in 导出字段 or './client/typert' in 导出字段 or './remote' in 导出字段

def 包根(起点,工作区):
    '最近含 package.json 且未越过工作区根的目录。走到工作区根仍没有则返回 None'
    当前=os.path.abspath(起点)
    工作区绝对=os.path.abspath(工作区)
    while 当前!=工作区绝对:
        if os.path.isfile(os.path.join(当前,'package.json')):
            return 当前
        父=os.path.dirname(当前)
        if 父==当前:
            break
        当前=父
    return None

def 工作区根(起点):
    '含 tsconfig.host.json 的目录。找不到时说明里不带起点路径'
    当前=os.path.abspath(起点)
    while not os.path.isfile(os.path.join(当前,'tsconfig.host.json')):
        父=os.path.dirname(当前)
        if 父==当前:
            raise FileNotFoundError('typert-generator: 找不到工作区根')
        当前=父
    return 当前
