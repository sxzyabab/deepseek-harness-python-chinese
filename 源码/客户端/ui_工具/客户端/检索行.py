"""检索工具行：grep/glob 共用。

对齐上游 `ui-tool/src/client/tool/toolviews/search-row.tsx`。公开面仅中文名。
"""
from .调用模型 import 派生工具行#行模型
from .检索卡模型 import 检索卡模型#检索卡
from .工具行 import 工具行#外壳
from .文案 import 会话命名空间#词典席

__all__=['检索行','检索工具视图','检索标题表']#仅中文公开名

检索标题表={'grep':'Grep','glob':'Glob'}#figma 字面标题

class 检索行:#grep/glob 行
    """共享 ToolRow；卡在 search 材料。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成
        自身.行=工具行()#外壳

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """派生后交给工具行。"""
        属性=自身.属性#props
        工具名=属性.get('toolName') if isinstance(属性,dict) else getattr(属性,'toolName',None)#名
        块=属性.get('block') if isinstance(属性,dict) else getattr(属性,'block',None)#块
        模型=派生工具行(工具名,块)#行模型
        检索=检索卡模型(块)#卡
        标题=检索标题表.get(工具名)#专用标题
        if 标题 is None:#无
            标题=模型.get('title') if isinstance(模型,dict) else getattr(模型,'title',None)#回退
        摘要=None#摘要
        if 检索 is not None:#有卡
            摘要=检索.get('title') if isinstance(检索,dict) else getattr(检索,'title',None)#卡标题优先
        if 摘要 is None:#无
            摘要=模型.get('summary') if isinstance(模型,dict) else getattr(模型,'summary',None)#模型摘要
        载荷={#行 props
            't':属性.get('t') if isinstance(属性,dict) else getattr(属性,'t',None),#文案
            'variant':模型.get('variant') if isinstance(模型,dict) else getattr(模型,'variant',None),#变体
            'toolName':工具名,#名
            'icon':'search',#图标
            'title':标题,#标题
            'summary':摘要,#摘要
            'body':None,#无 args 体
            'output':模型.get('output') if isinstance(模型,dict) else getattr(模型,'output',None),#输出
            'errorSummary':模型.get('errorSummary') if isinstance(模型,dict) else getattr(模型,'errorSummary',None),#错
            'search':检索,#检索卡
            'state':模型.get('state') if isinstance(模型,dict) else getattr(模型,'state',None),#态
            'inspect':属性.get('inspect') if isinstance(属性,dict) else getattr(属性,'inspect',None),#检查
        }#载荷结束
        自身.行.更新(载荷)#刷
        return 自身.行.渲染()#渲

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

检索工具视图={#登记：双键
    'name':'search-toolview',#名
    'inject':['slots'],#依赖
    'keys':('grep','glob'),#双键
    'locale':会话命名空间,#词典
    'component':检索行,#组件
}#视图结束
