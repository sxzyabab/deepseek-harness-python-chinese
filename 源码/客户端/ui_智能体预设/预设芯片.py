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

def 读(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 介绍错开毫秒(字数):#每字起步间隔
    """短名按上限；长名压进同一揭开窗。"""
    if 字数<=1:#单字
        return 0#无错开
    return min(介绍字符错开毫秒,介绍文字揭开毫秒/(字数-1))#夹取

class 预设芯片:#新会话芯片
    """部署无名册时返回 None。"""
    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props 并拉名册。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.打开=False#菜单
        自身.介绍中=False#介绍动画
        加载=读(自身.属性,'load')#加载
        if 加载 is not None:#有
            加载()#拉

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=dict(属性)#最新

    def 状态(自身):#芯片快照
        """经 useAgentPresetSeat。"""
        用=读(自身.属性,'useAgentPresetSeat')#钩
        if 用 is None:#无
            return {'options':[],'current':'','busy':False,'error':None,'introduce':False}#空
        return 用(lambda 快照:快照) or {}#快照

    def 选定(自身,标识):#暂存预设
        """关菜单并 select。"""
        自身.打开=False#关
        选=读(自身.属性,'select')#选定
        if 选 is not None:#有
            选(标识)#提交

    def 开始介绍(自身,标签):#武装介绍动画
        """减动效则立刻 acknowledge。"""
        态=自身.状态()#态
        if not 读(态,'introduce'):#无提示
            return#跳过
        就绪=len(读(态,'options') or [])>0 and 读(态,'current')!=''#就绪
        if not 就绪:#未就绪
            return#跳过
        介绍完=读(自身.属性,'introduced')#完结
        字们=list(标签)#字符
        if len(字们)==0:#空
            if 介绍完 is not None:#有
                介绍完()#完
            return#结束
        自身.介绍中=True#开动画
        错开=介绍错开毫秒(len(字们))#错开
        自身.介绍时长=介绍文字延迟毫秒+(len(字们)-1)*错开+介绍字符淡入毫秒#总时长
        自身.介绍完结=介绍完#回调

    def 渲染(自身):#结构化视图
        """产出芯片+菜单；无名册则 None。"""
        属性=自身.属性#props
        态=自身.状态()#态
        翻译=读(属性,'t')#翻译
        选项们=读(态,'options') or []#选项
        当前=读(态,'current') or ''#当前
        就绪=len(选项们)>0 and 当前!=''#就绪
        if not 就绪:#无
            return None#不画
        选中=None#项
        for 项 in 选项们:#找
            if 读(项,'id')==当前:#命中
                选中=项#记下
                break#停
        展示=预设展示文案(选中,翻译) if 选中 is not None and 翻译 is not None else None#展示
        标签=展示['name'] if 展示 is not None else 当前#标签
        if 读(态,'introduce') and not 自身.介绍中:#武装介绍
            自身.开始介绍(标签)#武装
        字们=list(标签)#字符
        错开=介绍错开毫秒(len(字们))#错开
        条目=[]#菜单项
        for 项 in 选项们:#逐项
            文=预设展示文案(项,翻译) if 翻译 is not None else None#文
            条目.append({#项
                'id':读(项,'id'),#id
                'name':文['name'] if 文 is not None else 读(项,'id'),#名
                'description':(文['description'] if 文 is not None else None) or (翻译('noDescription') if 翻译 else ''),#述
            })#结束
        return {#视图
            'type':'agent-preset-seat',#类型
            'open':自身.打开,#菜单
            'busy':bool(读(态,'busy')),#忙
            'title':读(态,'error') or (翻译('seatHint') if 翻译 else ''),#提示
            'label':标签,#当前名
            'introducing':自身.介绍中,#介绍中
            'characters':字们,#字符
            'staggerMs':错开,#错开
            'introTextDelayMs':介绍文字延迟毫秒,#延迟
            'items':条目,#菜单项
            'selectedId':当前,#选中
            'toggle':lambda:setattr(自身,'打开',not 自身.打开),#切换
            'close':lambda:setattr(自身,'打开',False),#关
            'select':自身.选定,#选定
            'cssModule':'预设芯片.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
