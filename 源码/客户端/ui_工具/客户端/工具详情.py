"""工具详情体：选中调用的结构化输出。

对齐上游 `ui-tool/src/client/tool/ToolDetails.tsx`。公开面仅中文名。
按卡片意图优先；未知则展平结果文本。
"""
from .差异卡模型 import 差异卡模型#diff
from .读卡模型 import 读卡模型#读
from .检索卡模型 import 检索卡模型#检索
from .终端卡模型 import 终端卡模型,终端块文案#终端
from .网页卡模型 import 网页卡模型#网页
from .调用模型 import 结果文本,取字段#结果文本

__all__=['工具详情']#仅中文公开名

class 工具详情:#详情体
    """已知呈现意图走对应块；否则展平文本。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """按意图分派。"""
        属性=自身.属性#props
        块=取字段(属性,'block')#块
        工作目录=取字段(属性,'cwd')#cwd
        翻译=取字段(属性,'t')#文案
        终端=终端卡模型(块,工作目录)#终端
        if 终端 is not None:#终端优先
            return {#终端体
                'type':'tool-details',#类型
                'kind':'terminal',#种
                'description':取字段(终端,'description'),#描述
                'card':取字段(终端,'card'),#卡
                'labels':终端块文案(翻译) if callable(翻译) else None,#文案
                'cssModule':'工具详情.module.css',#样式
            }#结束
        读=读卡模型(块,工作目录)#读
        if 读 is not None:#读
            return {#读体
                'type':'tool-details','kind':'read','card':读,
                'cssModule':'工具详情.module.css',
            }#结束
        差异=差异卡模型(块)#diff
        if 差异 is not None:#diff
            return {#diff 体
                'type':'tool-details','kind':'diff','card':取字段(差异,'card'),
                'cssModule':'工具详情.module.css',
            }#结束
        检索=检索卡模型(块)#检索
        if 检索 is not None:#检索
            return {#检索体
                'type':'tool-details','kind':'search',
                'card':取字段(检索,'card'),
                'recovery':取字段(检索,'recovery'),
                'cssModule':'工具详情.module.css',
            }#结束
        网页=网页卡模型(块)#网页
        if 网页 is not None:#网页
            正文=结果文本(块) if (取字段(块,'kind') is not None or (isinstance(块,dict) and 'kind' in 块)) else ''#正文
            return {#网页体
                'type':'tool-details','kind':'web','card':网页,
                'body':正文 if 正文!='' else None,
                'cssModule':'工具详情.module.css',
            }#结束
        已结算=取字段(块,'kind') is not None or (isinstance(块,dict) and 'kind' in 块)#已结算
        if not 已结算:#仍在跑
            文=翻译('details.running') if callable(翻译) else 'details.running'#运行文案
            return {#空
                'type':'tool-details','kind':'running','text':文,
                'cssModule':'工具详情.module.css',
            }#结束
        return {#展平文本
            'type':'tool-details','kind':'code',
            'text':结果文本(块),
            'error':bool(取字段(块,'isError')),
            'cssModule':'工具详情.module.css',
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
