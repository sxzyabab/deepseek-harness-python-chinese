"""受控风险确认对话框。

对齐上游 `ui-primitives/src/RiskConfirmation.tsx`。公开面仅中文名。
主操作在勾选确认前不可用；组合模态+按钮。
"""
from .模态 import 模态#模态外壳
from .按钮 import 按钮#动作按钮

__all__=['风险确认']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 风险确认:#勾选门控确认
    """属主控制 acknowledged；组合模态页脚。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):#结构树
        """打开时出警告+勾选+双按钮。"""
        属性=自身.属性#props
        已认=bool(取字段(属性,'acknowledged'))#已勾选
        禁用=bool(取字段(属性,'disabled',False))#禁用
        取消钮=按钮({#取消
            'variant':'outline','className':'modalAction',
            'onClick':取字段(属性,'onCancel'),'children':取字段(属性,'cancelLabel'),
        })#取消结束
        确认钮=按钮({#确认
            'variant':'primary','className':'confirmAction',
            'disabled':禁用 or (not 已认),
            'onClick':取字段(属性,'onConfirm'),'children':取字段(属性,'confirmLabel'),
        })#确认结束
        体={#内容
            'warning':{#警告行
                'icon':'warning-16',#警告图标
                'description':取字段(属性,'description'),#说明
            },#警告结束
            'acknowledgement':{#勾选
                'checked':已认,#态
                'disabled':禁用,#禁
                'label':取字段(属性,'acknowledgeLabel'),#文案
                'autoFocus':True,#自动焦
                'onChange':取字段(属性,'onAcknowledgedChange'),#变更
            },#勾选结束
        }#体结束
        壳=模态({#模态
            'open':取字段(属性,'open'),#开
            'onClose':取字段(属性,'onCancel'),#关=取消
            'title':取字段(属性,'title'),#标题
            'className':'confirmation',#卡类
            'contentClassName':'confirmationContent',#内容类
            'footer':(取消钮,确认钮),#脚
            'children':体,#体
        })#壳结束
        视图=壳.渲染()#渲模态
        if 视图 is None:#关
            return None#不画
        视图['type']='risk-confirmation'#抬类型
        视图['cssModule']='风险确认.module.css'#样式
        return 视图#结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
