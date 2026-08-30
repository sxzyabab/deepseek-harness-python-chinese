"""轨迹步骤格：下标 · 种类标签 · 文本 · 可选消息指标 · 已用时间。

对齐上游 `ui-trajectory/src/client/TrajectoryCell.tsx`。公开面仅中文名。
样式正文落在同目录 轨迹格.module.css，本模块读成 样式表。
"""
import os#同目录样式路径
from .轨迹记录 import 格式化已用秒数,取字段#记录面

__all__=['轨迹格','种类标签','样式表','样式文件']#仅中文公开名

_本目录=os.path.dirname(os.path.abspath(__file__))#本包目录
样式文件='轨迹格.module.css'#上游单文件

def _读样式(文件名):#读真实 CSS
    """从同目录读取样式正文。"""
    路径=os.path.join(_本目录,文件名)#绝对路径
    with open(路径,'r',encoding='utf-8') as 文件:#读文件
        return 文件.read()#全文

样式表=_读样式(样式文件)#完整格样式

种类标签={#种类 → 设计标签
    'system':'System','user':'User','context':'Context','compacted':'Compacted',
    'message':'Message','tool':'Tool','subtool':'Sub',
}#结束

标签类={#种类 → CSS 类
    'system':'tagSystem','user':'tagUser','context':'tagContext','compacted':'tagSystem',
    'message':'tagMessage','tool':'tagTool','subtool':'tagSubtool',
}#结束

class 轨迹格:#一步格
    """渲染一步轨迹格。"""

    def __init__(自身,属性=None):#可选 props
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """产出格结构树。"""
        p=自身.属性#props
        种类=取字段(p,'kind','message')#种类
        选中=bool(取字段(p,'selected',False))#选中
        显示指标=种类=='message'#消息才有指标
        return {#结构树
            'type':'trajectory-cell',#类型
            'kind':种类,#种类
            'selected':选中,#选中
            'index':取字段(p,'index'),#下标
            'tag':种类标签.get(种类,种类),#标签
            'tagClass':标签类.get(种类),#类
            'text':取字段(p,'text',''),#文本
            'metrics':{#指标
                'input':取字段(p,'input','') if 显示指标 else None,#入
                'output':取字段(p,'output','') if 显示指标 else None,#出
                'think':取字段(p,'think','') if 显示指标 else None,#思
            } if 显示指标 else None,#指标结束
            'time':格式化已用秒数(取字段(p,'timeSeconds')),#时间
            'css':样式表,#样式
            'cssModule':样式文件,#样式文件名
        }#结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷新
        return 自身.渲染()#渲
