__all__=[
    'Typert分析错误',
    '分析模式',
    '工作区分析器选项',
    '已发现Typert包',
    '工作区缓存',
    '工作区分析器',
]

from .异常 import Typert分析错误

分析模式=frozenset(['check','write'])
需要程序='typert: 分析需要 TypeScript 程序'

def 工作区分析器选项(**关键字参数):
    '把调用方给出的键收成一份选项字典，不在这里填缺省'
    return dict(关键字参数)

def 已发现Typert包(包,根,面列表):
    '一条发现结果：package、root、faces'
    return {'package':包,'root':根,'faces':list(面列表)}

def 缺省或自有(选项,键,缺省):
    '键不在或值为 None 时用缺省。空列表、空串和 False 都保留'
    if 键 not in 选项 or 选项[键] is None:
        return 缺省
    return 选项[键]

class 工作区缓存:
    '一份工作区快照上的解析备忘。改过磁盘之后要换新实例'
    def __init__(自身):
        '配置、登记和按面记住的编译宿主都从空表开始'
        自身.配置表={}
        自身.登记表={}
        自身._宿主表={}

    def config(自身,路径):
        '解析一份 tsconfig。当前运行时没有 TypeScript 程序'
        raise Typert分析错误(需要程序)

    def programHost(自身,面,选项):
        '取一面共享的编译宿主。当前运行时没有 TypeScript 程序'
        raise Typert分析错误(需要程序)

    def invalidate(自身,文件):
        '丢掉一份已编辑源文件的缓存解析。还没有宿主缓存时什么都不做'
        for 条目 in 自身._宿主表.values():
            文件表=条目.get('files') if isinstance(条目,dict) else None
            if not isinstance(文件表,dict):
                continue
            for 键 in list(文件表):
                if 键==文件:
                    文件表.pop(键,None)

class 工作区分析器:
    '把宿主与客户端当作独立程序来分析'
    def __init__(自身,选项=None):
        '保存解析后的选项。不在构造时读盘'
        if 选项 is None:
            选项={}
        if not isinstance(选项,dict):
            raise Typert分析错误('typert: WorkspaceAnalyzer 的选项必须是字典')
        根=选项.get('根')
        if not isinstance(根,str) or len(根)==0:
            raise Typert分析错误('typert: WorkspaceAnalyzer 需要根目录')
        自身.选项={
            '根':根,
            '宿主配置':缺省或自有(选项,'宿主配置','tsconfig.host.json'),
            '客户端配置':缺省或自有(选项,'客户端配置','tsconfig.client.json'),
            '面列表':list(缺省或自有(选项,'面列表',['host','client'])),
            '检查诊断':缺省或自有(选项,'检查诊断',True),
            '模式':缺省或自有(选项,'模式','check'),
        }
        if '包列表' in 选项 and 选项['包列表'] is not None:
            自身.选项['包列表']=list(选项['包列表'])
        缓存=选项.get('缓存')
        自身.缓存=缓存 if 缓存 is not None else 工作区缓存()

    def analyze(自身):
        '分析整个工作区。当前运行时没有 TypeScript 程序'
        raise Typert分析错误(需要程序)

    def analyzeInBatches(自身,批大小=8):
        '按批分析再合并。批大小先校验，再进入需要程序的分析'
        if '包列表' not in 自身.选项:
            raise Typert分析错误('typert: 分批分析需要显式的包列表')
        if isinstance(批大小,bool) or not isinstance(批大小,int) or 批大小<1:
            raise Typert分析错误(f'typert: 批大小必须是正整数，收到的是 {批大小}')
        if len(自身.选项['包列表'])==0:
            return {'faces':[],'crossFaceLinks':[]}
        return 自身.analyze()

    def discoverPackages(自身):
        '发现有业务面的包。当前运行时没有 TypeScript 程序'
        raise Typert分析错误(需要程序)

    def indexSourceDeclarations(自身):
        '词法索引导出类型声明。当前运行时没有 TypeScript 程序'
        raise Typert分析错误(需要程序)
