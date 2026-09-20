__all__=[
    'Typert分析错误',
    '分析模式',
    '工作区分析器选项',
    '已发现Typert包',
    '工作区缓存',
    '工作区分析器',
]

class Typert分析错误(Exception):#带源码向诊断的分析失败
    """带源码向诊断的分析失败；工作区导出校验亦复用此类型。"""
    name='TypertAnalysisError'#错误名

分析模式=frozenset(['check','write'])#公开业务边界上缺失注解的处理方式

def 工作区分析器选项(**关键字参数):#构造选项字典（形状登记，不做校验）
    """选项字段名与 WorkspaceAnalyzerOptions 一致；真分析仍硬缺口。"""
    return dict(关键字参数)#原样字典

def 已发现Typert包(包,根,面列表):#发现结果条目
    """对齐 DiscoveredTypertPackage：package / root / faces。"""
    return {'package':包,'root':根,'faces':list(面列表)}#条目

硬缺口文案='依赖硬缺口 analyzer（TypeScript 编译器 API），不可落'#共用失败文案

class 工作区缓存:#一份不可变工作区快照上的共享备忘（结构可落，解析不可落）
    """对齐 WorkspaceCaches：configs/registrations 容器可建；config/programHost 需 TS。"""
    def __init__(自身):#空快照
        """新实例；改盘后调用方须换新，勿复用陈旧缓存。"""
        自身.configs={}#路径 → 解析结果（真解析仍欠）
        自身.registrations={}#清单键 → 登记数组（真加载仍欠）
        自身._hosts={}#面 → 编译宿主（真宿主仍欠）

    def config(自身,路径):#取或解析一份 tsconfig
        """需 TypeScript 解析；显式失败。"""
        raise NotImplementedError('工作区缓存.config: '+硬缺口文案)#边界

    def programHost(自身,面,选项):#一面共享的编译宿主
        """需 typescript.createCompilerHost；显式失败。"""
        raise NotImplementedError('工作区缓存.programHost: '+硬缺口文案)#边界

    def invalidate(自身,文件):#丢掉一份已编辑源文件的缓存解析
        """无宿主缓存时可空操作；有键则按路径删除。"""
        目标=文件#目标路径字面
        for 条目 in list(自身._hosts.values()):#每面
            文件表=条目.get('files') if isinstance(条目,dict) else None#源文件表
            if not isinstance(文件表,dict):#无表
                continue#跳过
            for 键 in list(文件表.keys()):#拷贝键
                if 键==目标:#命中
                    文件表.pop(键,None)#删缓存

class 工作区分析器:#把宿主与客户端当作独立 Program 来分析（公开方法均硬缺口）
    """对齐 WorkspaceAnalyzer 构造与公开方法名；方法体一律 NotImplementedError。"""
    def __init__(自身,选项=None):#填默认值并保存选项
        """选项为映射或 None；不触发任何 TS 解析。"""
        if 选项 is None:#缺省
            选项={}#空
        if not isinstance(选项,dict):#非映射则从对象抽常用字段
            选项={#常用键
                'root':getattr(选项,'root',None),#工作区根
                'hostConfig':getattr(选项,'hostConfig',None),#宿主聚合
                'clientConfig':getattr(选项,'clientConfig',None),#客户端聚合
                'packages':getattr(选项,'packages',None),#包子集
                'faces':getattr(选项,'faces',None),#面
                'checkDiagnostics':getattr(选项,'checkDiagnostics',None),#诊断
                'mode':getattr(选项,'mode',None),#模式
                'caches':getattr(选项,'caches',None),#缓存
            }#结束
        if 'root' not in 选项 or 选项['root']=='':#缺根
            raise Typert分析错误('typert: WorkspaceAnalyzer requires root')#对齐失败声
        根=选项['root']#工作区根
        自身.options={#解析后的选项（不读盘）
            'root':根,#工作区根
            'hostConfig':选项.get('hostConfig') or 'tsconfig.host.json',#宿主聚合默认名
            'clientConfig':选项.get('clientConfig') or 'tsconfig.client.json',#客户端聚合默认名
            'faces':选项.get('faces') or ['host','client'],#默认两面
            'checkDiagnostics':True if 'checkDiagnostics' not in 选项 else 选项['checkDiagnostics'],#默认诊断
            'mode':选项.get('mode') or 'check',#默认检查
        }#结束
        if 选项.get('packages') is not None:#有子集才写入
            自身.options['packages']=选项.get('packages')#包名
        缓存=选项.get('caches')#共享缓存
        自身.caches=缓存 if 缓存 is not None else 工作区缓存()#未传入则新建

    def analyze(自身):#分析整个工作区 → WorkspaceModel
        """需 Program / FaceAnalyzer；显式失败。"""
        raise NotImplementedError('工作区分析器.analyze: '+硬缺口文案)#边界

    def analyzeInBatches(自身,batchSize=8):#分批分析再合并
        """需 analyze；显式失败。"""
        raise NotImplementedError('工作区分析器.analyzeInBatches: '+硬缺口文案)#边界

    def discoverPackages(自身):#发现有业务面的包
        """需聚合 tsconfig + 源图词法面探测；显式失败。"""
        raise NotImplementedError('工作区分析器.discoverPackages: '+硬缺口文案)#边界

    def indexSourceDeclarations(自身):#词法索引导出类型声明
        """需 ts.createSourceFile；显式失败。"""
        raise NotImplementedError('工作区分析器.indexSourceDeclarations: '+硬缺口文案)#边界
