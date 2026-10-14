import json,os
from ...基础设施.通用工具.序列化编码 import 紧凑json编码
from .异常 import Typert分析错误
from .分析器 import 工作区分析器,工作区缓存
from .代码输出 import 面模型代码输出器

__all__=[
    'Typert分析错误','相同导出','校验制品导出','工作区Typert生成器',
]

def 相同导出(实际,期望):
    'types 与 default 都逐字相同才通过。列表不是导出对象'
    if not isinstance(实际,dict):
        return False
    if 'types' not in 实际 or 'default' not in 实际:
        return False
    return 实际['types']==期望['types'] and 实际['default']==期望['default']

def 校验制品导出(工作区根,制品):
    '核对该包 exports 与 files。说明里只用包名和导出子路径'
    清单路径=os.path.join(工作区根,制品['packageRoot'],'package.json')
    文件=open(清单路径,'r',encoding='utf-8')
    try:
        清单=json.load(文件)
    finally:
        文件.close()
    子路径='./typert' if 制品['face']=='host' else './client/typert'
    期望={
        'types':'./lib/typert.'+制品['face']+'.d.ts',
        'default':'./lib/typert.'+制品['face']+'.js',
    }
    导出面=清单['exports'] if 'exports' in 清单 else None
    实际=导出面[子路径] if isinstance(导出面,dict) and 子路径 in 导出面 else None
    if not 相同导出(实际,期望):
        raise Typert分析错误('typert('+制品['face']+'): '+制品['package']+' must export '+子路径+' as '+紧凑json编码(期望))
    文件列表=清单['files'] if 'files' in 清单 and isinstance(清单['files'],list) else []
    for 文件名 in ('lib/typert.'+制品['face']+'.js','lib/typert.'+制品['face']+'.d.ts'):
        if 文件名 not in 文件列表:
            raise Typert分析错误('typert('+制品['face']+'): '+制品['package']+' package files must include '+文件名)
    if 制品['face']!='host':
        return
    远程期望={'types':'./lib/typert.remote-client.d.ts','default':'./lib/typert.remote-client.js'}
    远程实际=导出面['./remote'] if isinstance(导出面,dict) and './remote' in 导出面 else None
    远程文件列表=['lib/typert.remote-client.js','lib/typert.remote-client.d.ts']
    if 'remote' not in 制品 or 制品['remote'] is None:
        if 远程实际 is not None or any(文件名 in 文件列表 for 文件名 in 远程文件列表):
            raise Typert分析错误('typert(host): '+制品['package']+' publishes Remote artifacts but has no Remote methods')
        return
    if not 相同导出(远程实际,远程期望):
        raise Typert分析错误('typert(host): '+制品['package']+' must export ./remote as '+紧凑json编码(远程期望))
    for 文件名 in 远程文件列表:
        if 文件名 not in 文件列表:
            raise Typert分析错误('typert(host): '+制品['package']+' package files must include '+文件名)

class 工作区Typert生成器:
    '发现、分析，再按面输出制品'
    def __init__(自身,根,选项=None):
        '绑定工作区根。检查诊断缺省为真，显式 False 保留'
        if 选项 is None:
            选项={}
        自身.根=根
        自身.缓存=工作区缓存()
        自身.检查诊断=缺省诊断(选项)

    def discover(自身,面列表=None):
        '发现公开包面'
        return 工作区分析器(分析选项(自身,面列表)).discoverPackages()

    def generate(自身,包列表=None,面列表=None):
        '未给包列表时先发现。空列表表示一个包都不生成'
        if 包列表 is None:
            选定=[项['package'] for 项 in 自身.discover(面列表)]
        else:
            选定=list(包列表)
        选项=分析选项(自身,面列表)
        选项['包列表']=选定
        选项['检查诊断']=自身.检查诊断
        工作区模型=工作区分析器(选项).analyze()
        return 自身.自模型生成(工作区模型,True)

    def 自模型生成(自身,工作区模型,校验导出=True):
        '从已经分析好的工作区模型输出。空的 faces 得到空制品列表'
        制品列表=[]
        面清单=工作区模型['faces'] if 'faces' in 工作区模型 and 工作区模型['faces'] is not None else []
        for 面 in 面清单:
            输出器=面模型代码输出器(面)
            包清单=面['packages'] if 'packages' in 面 and 面['packages'] is not None else []
            for 包模型 in 包清单:
                制品={**输出器.输出代码(包模型['name']),'packageRoot':包模型['root']}
                if 校验导出:
                    校验制品导出(自身.根,制品)
                制品列表.append(制品)
        return 制品列表

    def 校验导出(自身,制品):
        '委托校验制品导出'
        校验制品导出(自身.根,制品)

def 缺省诊断(选项):
    '只有缺键或 None 才回到真。False 表示这次跳过诊断'
    if '检查诊断' not in 选项 or 选项['检查诊断'] is None:
        return True
    return 选项['检查诊断']

def 分析选项(生成器,面列表):
    '拼给工作区分析器的选项。面列表为 None 时让分析器自己填缺省'
    选项={'根':生成器.根,'缓存':生成器.缓存}
    if 面列表 is not None:
        选项['面列表']=list(面列表)
    return 选项
