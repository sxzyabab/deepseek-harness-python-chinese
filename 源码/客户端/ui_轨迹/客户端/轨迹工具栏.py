"""轨迹工具栏：时间线与账本折叠控件。

对齐上游 `ui-trajectory/src/client/TrajectoryToolbar.tsx`。公开面仅中文名。
样式正文落在同目录 轨迹工具栏.module.css，本模块读成 样式表。
"""
import os#同目录样式路径

__all__=['轨迹工具栏','样式表','样式文件']#仅中文公开名

_本目录=os.path.dirname(os.path.abspath(__file__))#本包目录
样式文件='轨迹工具栏.module.css'#上游单文件

def _读样式(文件名):#读真实 CSS
    """从同目录读取样式正文。"""
    路径=os.path.join(_本目录,文件名)#绝对路径
    with open(路径,'r',encoding='utf-8') as 文件:#读文件
        return 文件.read()#全文

样式表=_读样式(样式文件)#完整工具栏样式

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 轨迹工具栏:#粘性工具栏
    """时长开关、折叠轮次/调用、搜索。"""

    def __init__(自身,属性=None):#可选 props
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """产出工具栏结构树。"""
        p=自身.属性#props
        翻译=取字段(p,'t') or (lambda 键,*_a,**_k:键)#文案
        实测=bool(取字段(p,'actualDuration',False))#实测时长
        实际时=bool(取字段(p,'actualTime',False))#实际时间
        全轮折=bool(取字段(p,'allTurnsCollapsed',False))#全轮折叠
        全助折=bool(取字段(p,'allAssistantsCollapsed',False))#全助手折叠
        查询=取字段(p,'searchQuery','') or ''#查询
        return {#结构树
            'type':'trajectory-toolbar',#类型
            'role':'toolbar',#角色
            'aria':翻译('toolbar.aria'),#无障碍
            'actualDuration':实测,#实测
            'actualTime':实际时,#实际时
            'allTurnsCollapsed':全轮折,#轮
            'allAssistantsCollapsed':全助折,#助
            'searchQuery':查询,#查询
            'labels':{#文案
                'duration':翻译('toolbar.duration'),#时长
                'turns':翻译('toolbar.turns'),#轮次
                'calls':翻译('toolbar.calls'),#调用
                'search':翻译('toolbar.search'),#搜索
                'searchPlaceholder':翻译('toolbar.searchPlaceholder'),#占位
            },#文案结束
            'onActualDurationChange':取字段(p,'onActualDurationChange'),#时长切
            'onActualTimeChange':取字段(p,'onActualTimeChange'),#时间切
            'onToggleAllTurns':取字段(p,'onToggleAllTurns'),#轮切
            'onToggleAllAssistants':取字段(p,'onToggleAllAssistants'),#助切
            'onSearchQueryChange':取字段(p,'onSearchQueryChange'),#搜索
            'css':样式表,#样式
            'cssModule':样式文件,#样式文件名
        }#结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷新
        return 自身.渲染()#渲
