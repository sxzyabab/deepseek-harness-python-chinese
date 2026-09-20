import json,os#读 package.json
from .分析器 import Typert分析错误#分析错误类型
from .代码输出 import 面模型代码输出器#按面模型输出

__all__=[#公开面
    'Typert分析错误','相同导出','校验制品导出','工作区Typert生成器',
]#结束

def 相同导出(实际,期望):#比较 types/default 是否逐字相同
    """非普通对象则不同；两项都相等才通过。"""
    if not isinstance(实际,dict) or isinstance(实际,list):#非普通对象
        return False#不同
    if 'types' not in 实际 or 'default' not in 实际:#缺键
        return False#不同
    return 实际['types']==期望['types'] and 实际['default']==期望['default']#两项相等

def 校验制品导出(工作区根,制品):#核对该包 exports 与 files
    """核对该包 exports 与 files。"""
    清单路径=os.path.join(工作区根,制品['packageRoot'],'package.json')#清单绝对路径
    with open(清单路径,'r',encoding='utf-8') as 文件:#读清单
        清单=json.load(文件)#解析
    子路径='./typert' if 制品['face']=='host' else './client/typert'#宿主/客户端子路径
    期望={#该面约定的 types/default
        'types':'./lib/typert.'+制品['face']+'.d.ts',#声明
        'default':'./lib/typert.'+制品['face']+'.js',#运行时
    }#结束
    导出面=清单['exports'] if 'exports' in 清单 else None#exports
    实际=导出面[子路径] if isinstance(导出面,dict) and 子路径 in 导出面 else None#该子路径
    if not 相同导出(实际,期望):#不一致
        raise Typert分析错误('typert('+制品['face']+'): '+制品['package']+' must export '+子路径+' as '+json.dumps(期望,ensure_ascii=False,separators=(',',':'),allow_nan=False))#错误
    文件列表=清单['files'] if 'files' in 清单 and isinstance(清单['files'],list) else []#files
    for 文件 in ('lib/typert.'+制品['face']+'.js','lib/typert.'+制品['face']+'.d.ts'):#逐项
        if 文件 not in 文件列表:#漏了
            raise Typert分析错误('typert('+制品['face']+'): '+制品['package']+' package files must include '+文件)#错误
    if 制品['face']!='host':#非宿主面
        return
    远程期望={'types':'./lib/typert.remote-client.d.ts','default':'./lib/typert.remote-client.js'}#Remote 约定
    远程实际=导出面['./remote'] if isinstance(导出面,dict) and './remote' in 导出面 else None#./remote
    远程文件列表=['lib/typert.remote-client.js','lib/typert.remote-client.d.ts']#必须列入
    if 'remote' not in 制品 or 制品['remote'] is None:#无 Remote 方法
        if 远程实际 is not None or any(文件 in 文件列表 for 文件 in 远程文件列表):#却发布了
            raise Typert分析错误('typert(host): '+制品['package']+' publishes Remote artifacts but has no Remote methods')#错误
        return
    if not 相同导出(远程实际,远程期望):#不一致
        raise Typert分析错误('typert(host): '+制品['package']+' must export ./remote as '+json.dumps(远程期望,ensure_ascii=False,separators=(',',':'),allow_nan=False))#错误
    for 文件 in 远程文件列表:#逐项
        if 文件 not in 文件列表:#漏了
            raise Typert分析错误('typert(host): '+制品['package']+' package files must include '+文件)#错误

class 工作区Typert生成器:#工作区级发现、分析与代码输出
    """发现/分析依赖硬缺口 analyzer；已有模型可直接发射。"""
    def __init__(自身,根):#绑定工作区根
        """含各面聚合 tsconfig 的目录。"""
        自身.根=根#工作区根

    def discover(自身,faces=None):#发现公开包面
        """发现公开包面。依赖硬缺口 analyzer，不可落。"""
        raise NotImplementedError(#禁止假实现
            '工作区Typert生成器.discover: 依赖硬缺口 analyzer（WorkspaceAnalyzer.discoverPackages），不可落'
        )#结束

    def generate(自身,packages=None,faces=None):#生成全部或指定包
        """分析后发射。依赖硬缺口 analyzer；已有模型请用自模型生成。"""
        raise NotImplementedError(#禁止假实现
            '工作区Typert生成器.generate: 依赖硬缺口 analyzer（WorkspaceAnalyzer.analyze），不可落'
        )#结束

    def 自模型生成(自身,工作区模型,校验导出=True):#从已分析 WorkspaceModel 发射
        """每个包面一件制品；可选核对 package.json。不触 analyzer。"""
        制品列表=[]#累积
        for 面 in (工作区模型['faces'] if 'faces' in 工作区模型 and 工作区模型['faces'] is not None else []):#每个程序面
            输出器=面模型代码输出器(面)#按该面模型
            for 包模型 in (面['packages'] if 'packages' in 面 and 面['packages'] is not None else []):#该面下每个包
                制品={**输出器.输出代码(包模型['name']),'packageRoot':包模型['root']}#叠上包根
                if 校验导出:#核对 exports/files
                    校验制品导出(自身.根,制品)#校验
                制品列表.append(制品)#收入
        return 制品列表#每包一面一件

    def 校验导出(自身,制品):#单件校验
        """委托校验制品导出。"""
        校验制品导出(自身.根,制品)#校验
