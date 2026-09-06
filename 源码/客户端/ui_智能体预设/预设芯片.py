"""新会话屏预设芯片（主屏座位）。

对齐上游 `ui-agent-preset/src/client/AgentPresetSeat.tsx`。公开面仅中文名。
对话开跑后宿主拒绝换预设，故控件只在空白会话屏存活。
"""
from .文案 import 预设展示文案#展示文案

__all__=['预设芯片','介绍文字延迟毫秒','介绍字符错开毫秒','介绍文字揭开毫秒','介绍字符淡入毫秒']#仅中文公开名

介绍文字延迟毫秒=150#图标入场后再揭字
介绍字符错开毫秒=40#每字起步间隔上限
介绍文字揭开毫秒=200#整段揭开窗
介绍字符淡入毫秒=400#单字淡入时长

def 介绍错开毫秒(字数):
    """短名按上限；长名压进同一揭开窗。"""
    if 字数<=1:#单字
        return 0#无错开
    return min(介绍字符错开毫秒,介绍文字揭开毫秒/(字数-1))#夹取

class 预设芯片:
    """部署无名册时返回 None。属性与快照都是 dict。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props 并拉名册。"""
        自身.属性=dict(属性) if 属性 is not None else {}#基础
        自身.属性.update(关键字参数)#覆盖
        自身.打开=False#菜单
        自身.介绍中=False#介绍动画
        自身.属性['load']()#拉

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=dict(属性)#最新

    def 状态(自身):
        """经 useAgentPresetSeat。"""
        def 恒等(快照):
            """整表。"""
            return 快照#快照
        return 自身.属性['useAgentPresetSeat'](恒等)#快照

    def 选定(自身,标识):
        """关菜单并 select。"""
        自身.打开=False#关
        自身.属性['select'](标识)#提交

    def 切换菜单(自身):
        """翻转菜单开闭。"""
        自身.打开=not 自身.打开#翻转

    def 关闭菜单(自身):
        """关菜单。"""
        自身.打开=False#关

    def 开始介绍(自身,标签):
        """减动效则立刻 acknowledge。"""
        态=自身.状态()#态
        if not 态['introduce']:#无提示
            return#跳过
        就绪=len(态['options'])>0 and 态['current']!=''#就绪；判 length 与空串
        if not 就绪:#未就绪
            return#跳过
        介绍完=自身.属性['introduced']#完结
        字列表=list(标签)#字符
        if len(字列表)==0:#空
            介绍完()#完
            return#结束
        自身.介绍中=True#开动画
        错开=介绍错开毫秒(len(字列表))#错开
        自身.介绍时长=介绍文字延迟毫秒+(len(字列表)-1)*错开+介绍字符淡入毫秒#总时长
        自身.介绍完结=介绍完#回调

    def 渲染(自身):
        """产出芯片+菜单；无名册则 None。"""
        属性=自身.属性#props
        态=自身.状态()#态
        翻译=属性['t']#翻译
        选项列表=态['options']#选项
        当前=态['current']#当前
        就绪=len(选项列表)>0 and 当前!=''#就绪；判 length 与空串
        if not 就绪:#无
            return None#不画
        选中=None#项
        for 项 in 选项列表:#找
            if 项['id']==当前:#命中
                选中=项#记下
                break#停
        展示=预设展示文案(选中,翻译) if 选中 is not None else None#展示
        标签=展示['name'] if 展示 is not None else 当前#标签
        if 态['introduce'] and not 自身.介绍中:#武装介绍
            自身.开始介绍(标签)#武装
        字列表=list(标签)#字符
        错开=介绍错开毫秒(len(字列表))#错开
        条目=[]#菜单项
        for 项 in 选项列表:#逐项
            文=预设展示文案(项,翻译)#文
            述=文['description'] if 'description' in 文 else None#述
            if 述 is None:#无述
                述=翻译('noDescription')#回退
            条目.append({#项
                'id':项['id'],#id
                'name':文['name'],#名
                'description':述,#述
            })#结束
        标题=态['error']#错误
        if 标题 is None:#无错
            标题=翻译('seatHint')#提示
        return {#视图
            'type':'agent-preset-seat',#类型
            'open':自身.打开,#菜单
            'busy':态['busy'],#忙
            'title':标题,#提示
            'label':标签,#当前名
            'introducing':自身.介绍中,#介绍中
            'characters':字列表,#字符
            'staggerMs':错开,#错开
            'introTextDelayMs':介绍文字延迟毫秒,#延迟
            'items':条目,#菜单项
            'selectedId':当前,#选中
            'toggle':自身.切换菜单,#切换
            'close':自身.关闭菜单,#关
            'select':自身.选定,#选定
            'cssModule':'预设芯片.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有
            合并=dict(属性) if 属性 is not None else {}#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
