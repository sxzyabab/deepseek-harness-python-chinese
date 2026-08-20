"""会话页眉只读预设标签。

对齐上游 `ui-agent-preset/src/client/AgentPresetLabel.tsx`。公开面仅中文名。
会话一旦开跑组合即固定，页眉只报告正在跑什么。
"""
from .文案 import 预设展示文案#展示文案

__all__=['预设标签']#仅中文公开名

def 读(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 预设标签:#页眉只读标签
    """无预设记录时返回 None。"""
    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props；有预设时拉名册。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.确保加载()#按需加载

    def 更新(自身,属性):#刷新
        """刷新并按需加载。"""
        自身.属性=dict(属性)#最新
        自身.确保加载()#加载

    def 会话预设(自身):#本会话预设 id
        """经 useSessions 读 byId[sessionId].agentPreset。"""
        属性=自身.属性#props
        会话标识=读(属性,'sessionId')#会话
        用会话=读(属性,'useSessions')#会话钩
        if 用会话 is None or 会话标识 is None:#缺
            return None#无
        摘要=用会话(lambda 态:读(读(态,'byId') or {},会话标识))#摘要
        return 读(摘要,'agentPreset') if 摘要 is not None else None#预设

    def 选项们(自身):#名册选项
        """经 useAgentPresets 读 options。"""
        用=读(自身.属性,'useAgentPresets')#钩
        if 用 is None:#无
            return []#空
        return 用(lambda 快照:读(快照,'options') or []) or []#选项

    def 确保加载(自身):#有预设才拉名册
        """部署无预设时不请求。"""
        if 自身.会话预设() is None:#无
            return#跳过
        加载=读(自身.属性,'load')#加载
        if 加载 is not None:#有
            加载()#拉

    def 渲染(自身):#结构化视图
        """产出页眉标签；无预设则 None。"""
        预设=自身.会话预设()#预设 id
        if 预设 is None:#无
            return None#不画
        翻译=读(自身.属性,'t')#翻译
        选项=None#命中项
        for 项 in 自身.选项们():#找
            if 读(项,'id')==预设:#命中
                选项=项#记下
                break#停
        展示=预设展示文案(选项,翻译) if 选项 is not None and 翻译 is not None else None#展示
        名=展示['name'] if 展示 is not None else 预设#名
        说明=展示['description'] if 展示 is not None else None#说明
        if 说明 is None and 翻译 is not None:#回退提示
            说明=翻译('headerHint')#页眉提示
        return {#视图
            'type':'agent-preset-label',#类型
            'name':名,#名
            'title':说明,#悬停
            'presetId':预设,#id
            'cssModule':'预设标签.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
