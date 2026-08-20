"""工作区级发现与由模型驱动的 Typert 生成。

对齐上游 `typert/generator/src/workspace.ts`。公开面仅中文名。
`discover` / `generate` 编排依赖硬缺口 analyzer，本叶以显式 NotImplementedError 登记边界；
已有 WorkspaceModel 上的发射走 `自模型生成`（不触 TS 编译器）。
"""
import json,os#读 package.json
from .分析器 import Typert分析错误,TypertAnalysisError#分析错误类型（上游自 analyzer 再导出）
from .发射器 import 面模型发射器#按面模型发射

__all__=[#公开面
    'Typert分析错误','相同导出','校验制品导出','工作区Typert生成器',
    'sameExport','validateArtifactExport','WorkspaceTypertGenerator',
    'TypertAnalysisError',
]#结束

def 相同导出(实际,期望):#比较 types/default 是否逐字相同
    """非普通对象则不同；两项都相等才通过。"""
    if not isinstance(实际,dict) or isinstance(实际,list):#非普通对象
        return False#不同
    return 实际.get('types')==期望['types'] and 实际.get('default')==期望['default']#两项相等

sameExport=相同导出#上游名

def 校验制品导出(工作区根,制品):#核对该包 exports 与 files
    """对齐 WorkspaceTypertGenerator.validateExport。"""
    清单路径=os.path.join(工作区根,制品['packageRoot'],'package.json')#清单绝对路径
    with open(清单路径,'r',encoding='utf-8') as 文件:#读清单
        清单=json.load(文件)#解析
    子路径='./typert' if 制品['face']=='host' else './client/typert'#宿主/客户端子路径
    期望={#该面约定的 types/default
        'types':'./lib/typert.'+制品['face']+'.d.ts',#声明
        'default':'./lib/typert.'+制品['face']+'.js',#运行时
    }#结束
    导出面=清单.get('exports')#exports
    实际=导出面.get(子路径) if isinstance(导出面,dict) else None#该子路径
    if not 相同导出(实际,期望):#不一致
        raise Typert分析错误('typert('+制品['face']+'): '+制品['package']+' must export '+子路径+' as '+json.dumps(期望))#错误
    文件们=清单.get('files') if isinstance(清单.get('files'),list) else []#files
    for 文件 in ('lib/typert.'+制品['face']+'.js','lib/typert.'+制品['face']+'.d.ts'):#逐项
        if 文件 not in 文件们:#漏了
            raise Typert分析错误('typert('+制品['face']+'): '+制品['package']+' package files must include '+文件)#错误
    if 制品['face']!='host':#非宿主面
        return#结束
    远程期望={'types':'./lib/typert.remote-client.d.ts','default':'./lib/typert.remote-client.js'}#Remote 约定
    远程实际=导出面.get('./remote') if isinstance(导出面,dict) else None#./remote
    远程文件们=['lib/typert.remote-client.js','lib/typert.remote-client.d.ts']#必须列入
    if 制品.get('remote') is None:#无 Remote 方法
        if 远程实际 is not None or any(文件 in 文件们 for 文件 in 远程文件们):#却发布了
            raise Typert分析错误('typert(host): '+制品['package']+' publishes Remote artifacts but has no Remote methods')#错误
        return#结束
    if not 相同导出(远程实际,远程期望):#不一致
        raise Typert分析错误('typert(host): '+制品['package']+' must export ./remote as '+json.dumps(远程期望))#错误
    for 文件 in 远程文件们:#逐项
        if 文件 not in 文件们:#漏了
            raise Typert分析错误('typert(host): '+制品['package']+' package files must include '+文件)#错误

validateArtifactExport=校验制品导出#上游名

class 工作区Typert生成器:#工作区级发现、分析与发射
    """发现/分析依赖硬缺口 analyzer；已有模型可直接发射。"""
    def __init__(自身,根):#绑定工作区根
        """含各面聚合 tsconfig 的目录。"""
        自身.根=根#工作区根

    def discover(自身,faces=None):#发现公开包面
        """对齐上游 discover → WorkspaceAnalyzer.discoverPackages；显式硬缺口。"""
        raise NotImplementedError(#禁止假实现
            '工作区Typert生成器.discover: 依赖硬缺口 analyzer（WorkspaceAnalyzer.discoverPackages），不可落'
        )#结束

    def generate(自身,packages=None,faces=None):#生成全部或指定包
        """对齐上游 generate → analyze + 发射；显式硬缺口。已有模型请用自模型生成。"""
        raise NotImplementedError(#禁止假实现
            '工作区Typert生成器.generate: 依赖硬缺口 analyzer（WorkspaceAnalyzer.analyze），不可落'
        )#结束

    def 自模型生成(自身,工作区模型,校验导出=True):#从已分析 WorkspaceModel 发射
        """每个包面一件制品；可选核对 package.json。不触 analyzer。"""
        制品们=[]#累积
        for 面 in 取字段(工作区模型,'faces') or []:#每个程序面
            发射器=面模型发射器(面)#按该面模型
            for 包模型 in 取字段(面,'packages') or []:#该面下每个包
                制品={**发射器.emit(取字段(包模型,'name')),'packageRoot':取字段(包模型,'root')}#叠上包根
                if 校验导出:#核对 exports/files
                    校验制品导出(自身.根,制品)#校验
                制品们.append(制品)#收入
        return 制品们#每包一面一件

    def 校验导出(自身,制品):#单件校验
        """委托校验制品导出。"""
        校验制品导出(自身.根,制品)#校验

WorkspaceTypertGenerator=工作区Typert生成器#上游名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性
