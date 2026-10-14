from nicegui import ui as 界面
from ..引擎.树 import 取节点#树
from .标签面板 import 标签面板#窗格

__all__=['窗格树']#仅中文公开名


class 窗格树:
    '自节点标识递归渲染分割或窗格'

    def __init__(自身,状态,节点标识,回调,预览=None):
        '预览为 {splitId, sizes} 或 None'
        自身.状态=状态#布局
        自身.节点标识=节点标识#节点
        自身.回调=回调#回调
        自身.预览=预览#尺寸预览

    def 更新(自身,状态,节点标识,回调,预览=None):
        'props 变更'
        自身.状态=状态#态
        自身.节点标识=节点标识#节点
        自身.回调=回调#回调
        自身.预览=预览#预览

    def 渲染(自身):
        '画出分割或窗格'
        节点=取节点(自身.状态,自身.节点标识)#节点
        if 节点['kind']=='pane':#叶
            标签面板(自身.状态,节点,自身.回调).渲染()#窗格自己画
            return
        if 自身.预览 is not None and 自身.预览['splitId']==节点['id']:#预览本分割
            尺寸表=自身.预览['sizes']#预览
        else:#录制
            尺寸表=节点['sizes']#份额
        容器=界面.row() if 节点['axis']=='row' else 界面.column()
        with 容器.classes('dockkit-split'):
            for 序号,子标识 in enumerate(节点['children']):#逐子
                if 序号>0:#分隔
                    隔下标=序号-1
                    def 按下(分=节点['id'],甲=隔下标):
                        '按下分隔条'
                        自身.回调['onDividerPressed'](分,甲,None)
                    界面.element('div').classes('dockkit-divider').on('mousedown',按下)
                with 界面.column().style('flex-grow:'+str(尺寸表[序号])):
                    窗格树(自身.状态,子标识,自身.回调,自身.预览).渲染()
