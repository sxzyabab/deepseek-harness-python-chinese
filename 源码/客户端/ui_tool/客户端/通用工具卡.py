"""通用工具卡：未登记工具名的回退行。

对齐上游 `ui-tool/src/client/tool/toolviews/GenericToolCard.tsx`。公开面仅中文名。
"""
from .调用模型 import 派生工具行#行模型
from .读卡模型 import 读卡模型#读
from .差异卡模型 import 差异卡模型#差异
from .检索卡模型 import 检索卡模型#检索
from .终端卡模型 import 终端卡模型,终端已失败#终端
from .网页卡模型 import 网页卡模型#网页
from .工具行 import 工具行#外壳

__all__=['通用工具卡','变体图标表']#仅中文公开名

变体图标表={#变体→图标名
    'search':'search',#检索
    'read':'browse',#读
    'bash':'api',#终端
    'write':'edit',#写
    'edit':'edit',#改
    'code':'code',#代码
    'others':'sparkle',#其它
}#图标表结束

class 通用工具卡:#默认工具行
    """分类变体并填全部卡材料。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成
        自身.行=工具行()#外壳

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """派生态与卡后交给工具行。"""
        属性=自身.属性#props
        工具名=属性.get('toolName') if isinstance(属性,dict) else getattr(属性,'toolName',None)#名
        块=属性.get('block') if isinstance(属性,dict) else getattr(属性,'block',None)#块
        工作目录=属性.get('cwd') if isinstance(属性,dict) else getattr(属性,'cwd',None)#cwd
        模型=派生工具行(工具名,块,工作目录)#行
        终端=终端卡模型(块,工作目录)#终端卡
        读=读卡模型(块,工作目录)#读卡
        差异=差异卡模型(块)#差异卡
        检索=检索卡模型(块)#检索卡
        网页=网页卡模型(块)#网页卡
        态=模型.get('state') if isinstance(模型,dict) else getattr(模型,'state',None)#态
        if 态=='ok' and 终端 is not None and 终端已失败(终端):#终端失败抬红
            态='error'#红
        单文件=None#路径
        if isinstance(模型,dict):#映射
            单文件=模型.get('filePath')#路径
        else:#对象
            单文件=getattr(模型,'filePath',None)#路径
        摘要=None#摘要
        if 终端 is not None:#终端描述优先
            摘要=终端.get('description') if isinstance(终端,dict) else getattr(终端,'description',None)#描述
        if 摘要 is None and 检索 is not None:#检索标题次之
            摘要=检索.get('title') if isinstance(检索,dict) else getattr(检索,'title',None)#标题
        if 摘要 is None:#模型摘要
            摘要=模型.get('summary') if isinstance(模型,dict) else getattr(模型,'summary',None)#摘要
        变体=模型.get('variant') if isinstance(模型,dict) else getattr(模型,'variant','others')#变体
        载荷={#行
            't':属性.get('t') if isinstance(属性,dict) else getattr(属性,'t',None),#文案
            'variant':变体,#变体
            'toolName':工具名,#名
            'icon':变体图标表.get(变体,'sparkle'),#图标
            'title':模型.get('title') if isinstance(模型,dict) else getattr(模型,'title',None),#标题
            'summary':摘要,#摘要
            'body':None if 单文件 is not None else (模型.get('body') if isinstance(模型,dict) else getattr(模型,'body',None)),#体
            'output':模型.get('output') if isinstance(模型,dict) else getattr(模型,'output',None),#输出
            'errorSummary':模型.get('errorSummary') if isinstance(模型,dict) else getattr(模型,'errorSummary',None),#错
            'terminal':终端,#终端
            'diff':差异,#差异
            'read':读,#读
            'search':检索,#检索
            'web':网页,#网页
            'state':态,#态
            'filePath':单文件,#路径
            'onOpenFile':(属性.get('openFile') if isinstance(属性,dict) else getattr(属性,'openFile',None)) if 单文件 is not None else None,#开文件
            'inspect':属性.get('inspect') if isinstance(属性,dict) else getattr(属性,'inspect',None),#检查
        }#载荷结束
        自身.行.更新(载荷)#刷
        return 自身.行.渲染()#渲

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
