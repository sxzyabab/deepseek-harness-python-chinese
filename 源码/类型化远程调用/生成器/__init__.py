from .模型 import 子类型节点标识列表,关键字类型名,类型运算符名,成员可见性#模型
from .分析器 import (#分析器公开面（真实现硬缺口；边界已登记）
    Typert分析错误,
    工作区分析器,
    工作区缓存,
    分析模式,
    工作区分析器选项,
    已发现Typert包,
)#分析器
from .工作区 import (#工作区（discover/generate 显式硬缺口；自模型生成可落）
    相同导出,校验制品导出,工作区Typert生成器,
)#工作区
from .渲染器 import 类型图渲染器,类型图渲染错误#渲染器
from .代码输出 import (#代码输出
    面模型代码输出器,Typert代码输出错误,
    引号,缩进,参数边界键,结果边界键,上下文边界键,边界根列表,
    安全标识符,远程贡献骨架字面量,
)#代码输出
from .目录投影 import (#Cordis 目录投影
    Cordis目录投影器,
    投影Cordis目录,
    收集事件,收集服务,
    解析JsDoc,渲染运行时Api,
    渲染页区域,渲染继承页,
    区域开,区域闭,
)#目录投影
from .不变量 import 应用 as 应用不变量#不变量配套
from .tsdown插件 import (#tsdown 插件面（部分依赖硬缺口 analyzer）
    typert插件,输出制品,
    有Typert导出,读清单,
    包根,工作区根,
)#tsdown 插件

__all__=[#公开面
    '子类型节点标识列表',
    '关键字类型名','类型运算符名','成员可见性',
    'Typert分析错误',
    '工作区分析器','工作区缓存',
    '分析模式',
    '工作区分析器选项',
    '已发现Typert包',
    '相同导出','校验制品导出',
    '工作区Typert生成器',
    '类型图渲染器','类型图渲染错误',
    '面模型代码输出器','Typert代码输出错误',
    '引号','缩进','参数边界键','结果边界键','上下文边界键','边界根列表',
    '远程贡献骨架字面量','安全标识符',
    'Cordis目录投影器',
    '投影Cordis目录',
    '收集事件','收集服务',
    '解析JsDoc','渲染运行时Api',
    '渲染页区域','渲染继承页',
    '区域开','区域闭',
    '应用不变量',
    'typert插件','输出制品',
    '有Typert导出','读清单',
    '包根','工作区根',
]#结束

# 硬缺口（不迁；依赖 TypeScript 编译器 API）：
# 3. typert 自动生成 remotes（Remote dtsMap 细粒度 gen-mapping；现为合法空映射）
# 4. generator TS analyzer 真实现（analyze / discoverPackages / indexSourceDeclarations / Program）
# 已登记 NotImplementedError 边界（勿假实现）：
#   工作区.discover / generate；目录投影.projectCordisCatalog / collectEvents / collectServices；
#   分析器.WorkspaceAnalyzer 公开方法；tsdown 写包 generate·discover 与装饰器 transpile
