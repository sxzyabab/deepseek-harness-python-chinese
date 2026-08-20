"""Typert 分析器、与编译器无关的模型、以及由模型驱动的制品发射器的公开 API。

对齐上游 `typert/generator/src/index.ts` 已迁面。公开面仅中文名。
分析器真实现属硬缺口4；本包再导出其公开符号与 NotImplementedError 边界。
"""
from .模型 import 子类型节点标识们,childTypeNodeIds,关键字类型名,类型运算符名,成员可见性,取字段#模型
from .分析器 import (#分析器公开面（真实现硬缺口；边界已登记）
    Typert分析错误,TypertAnalysisError,
    工作区分析器,WorkspaceAnalyzer,
    工作区缓存,WorkspaceCaches,
    分析模式,AnalysisMode,
    工作区分析器选项,WorkspaceAnalyzerOptions,
    已发现Typert包,DiscoveredTypertPackage,
)#分析器
from .工作区 import (#工作区（discover/generate 显式硬缺口；自模型生成可落）
    相同导出,校验制品导出,工作区Typert生成器,
    sameExport,validateArtifactExport,WorkspaceTypertGenerator,
)#工作区
from .渲染器 import 类型图渲染器,类型图渲染错误,TypeGraphRenderer,TypeGraphRenderError#渲染器
from .发射器 import (#发射器
    面模型发射器,FaceModelEmitter,Typert发射错误,TypertEmitError,
    引号,缩进,参数边界键,结果边界键,上下文边界键,调用边界根们,
    quote,indent,invocationBoundaryRoots,安全标识符,safeIdentifier,
)#发射器
from .发射辅助 import 远程贡献骨架字面量#骨架字面量
from .目录投影 import (#Cordis 目录投影
    Cordis目录投影器,CordisCatalogProjector,
    投影Cordis目录,projectCordisCatalog,
    收集事件,collectEvents,收集服务,collectServices,
    解析JsDoc,parseJsDoc,渲染运行时Api,renderRuntimeApi,
    渲染页区域,renderPageRegion,渲染继承页,renderInheritedPage,
    区域开,区域闭,REGION_BEGIN,REGION_END,
)#目录投影
from .不变量 import 应用 as 应用不变量#不变量配套
from .tsdown插件 import (#tsdown 插件面（部分依赖硬缺口 analyzer）
    typert插件,typertPlugin,发射制品,emitArtifacts,
    有Typert导出,hasTypertExport,读清单,readManifest,
    包根,packageRoot,工作区根,workspaceRoot,
)#tsdown 插件

__all__=[#公开面
    '子类型节点标识们','childTypeNodeIds','取字段',
    '关键字类型名','类型运算符名','成员可见性',
    'Typert分析错误','TypertAnalysisError',
    '工作区分析器','WorkspaceAnalyzer','工作区缓存','WorkspaceCaches',
    '分析模式','AnalysisMode',
    '工作区分析器选项','WorkspaceAnalyzerOptions',
    '已发现Typert包','DiscoveredTypertPackage',
    '相同导出','校验制品导出',
    'sameExport','validateArtifactExport',
    '工作区Typert生成器','WorkspaceTypertGenerator',
    '类型图渲染器','类型图渲染错误','TypeGraphRenderer','TypeGraphRenderError',
    '面模型发射器','FaceModelEmitter','Typert发射错误','TypertEmitError',
    '引号','缩进','参数边界键','结果边界键','上下文边界键','调用边界根们',
    '远程贡献骨架字面量','安全标识符','safeIdentifier',
    'quote','indent','invocationBoundaryRoots',
    'Cordis目录投影器','CordisCatalogProjector',
    '投影Cordis目录','projectCordisCatalog',
    '收集事件','collectEvents','收集服务','collectServices',
    '解析JsDoc','parseJsDoc','渲染运行时Api','renderRuntimeApi',
    '渲染页区域','renderPageRegion','渲染继承页','renderInheritedPage',
    '区域开','区域闭','REGION_BEGIN','REGION_END',
    '应用不变量',
    'typert插件','typertPlugin','发射制品','emitArtifacts',
    '有Typert导出','hasTypertExport','读清单','readManifest',
    '包根','packageRoot','工作区根','workspaceRoot',
]#结束

# 硬缺口（不迁；依赖 TypeScript 编译器 API）：
# 3. typert 自动生成 remotes（Remote dtsMap 细粒度 gen-mapping；现为合法空映射）
# 4. generator TS analyzer 真实现（analyze / discoverPackages / indexSourceDeclarations / Program）
# 已登记 NotImplementedError 边界（勿假实现）：
#   工作区.discover / generate；目录投影.projectCordisCatalog / collectEvents / collectServices；
#   分析器.WorkspaceAnalyzer 公开方法；tsdown 写包 generate·discover 与装饰器 transpile
