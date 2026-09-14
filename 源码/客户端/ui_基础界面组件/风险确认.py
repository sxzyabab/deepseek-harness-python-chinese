from .模态 import 模态#模态外壳
from .按钮 import 按钮#动作按钮

__all__=['风险确认']#仅中文公开名

class 风险确认:#勾选门控确认
    """属主控制 acknowledged；组合模态页脚。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        """打开时出警告+勾选+双按钮。"""
        属性=自身.属性#props
        已认=属性['acknowledged'] is True if 'acknowledged' in 属性 else False#已勾选
        禁用=属性['disabled'] is True if 'disabled' in 属性 else False#禁用
        取消钮=按钮({#取消
            'variant':'outline','className':'modalAction',
            'onClick':属性['onCancel'] if 'onCancel' in 属性 else None,'children':属性['cancelLabel'] if 'cancelLabel' in 属性 else None,
        })#取消结束
        确认钮=按钮({#确认
            'variant':'primary','className':'confirmAction',
            'disabled':禁用 is True or 已认 is False,
            'onClick':属性['onConfirm'] if 'onConfirm' in 属性 else None,'children':属性['confirmLabel'] if 'confirmLabel' in 属性 else None,
        })#确认结束
        体={#内容
            'warning':{#警告行
                'icon':'warning-16',#警告图标
                'description':属性['description'] if 'description' in 属性 else None,#说明
            },#警告结束
            'acknowledgement':{#勾选
                'checked':已认,#态
                'disabled':禁用,#禁
                'label':属性['acknowledgeLabel'] if 'acknowledgeLabel' in 属性 else None,#文案
                'autoFocus':True,#自动焦
                'onChange':属性['onAcknowledgedChange'] if 'onAcknowledgedChange' in 属性 else None,#变更
            },#勾选结束
        }#体结束
        壳=模态({#模态
            'open':属性['open'] if 'open' in 属性 else None,#开
            'onClose':属性['onCancel'] if 'onCancel' in 属性 else None,#关=取消
            'title':属性['title'] if 'title' in 属性 else None,#标题
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

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
