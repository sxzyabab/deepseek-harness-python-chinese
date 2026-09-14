from .文案 import 预设展示文案#展示文案

__all__=['预设标签']#仅中文公开名

class 预设标签:
    """无预设记录时返回 None。属性与快照都是 dict。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props；有预设时拉名册。"""
        自身.属性=dict(属性) if 属性 is not None else {}#基础
        自身.属性.update(关键字参数)#覆盖
        自身.确保加载()#按需加载

    def 更新(自身,属性):
        """刷新并按需加载。"""
        自身.属性=dict(属性)#最新
        自身.确保加载()#加载

    def 会话预设(自身):
        """经 useSessions 读 byId[sessionId].agentPreset。会话列表快照是对象。"""
        属性=自身.属性#props
        会话标识=属性['sessionId']#会话
        def 选摘要(态):
            """当前会话摘要。byId 是 dict。"""
            表=态.byId#会话表
            if 表 is None or 会话标识 not in 表:#无
                return None#无
            return 表[会话标识]#摘要 dict
        摘要=属性['useSessions'](选摘要)#摘要
        if 摘要 is None:#无
            return None#无
        return 摘要['agentPreset'] if 'agentPreset' in 摘要 else None#预设

    def 取选项列表(自身):
        """经 useAgentPresets 读 options。"""
        def 选选项(快照):
            """名册选项。"""
            return 快照['options']#选项
        return 自身.属性['useAgentPresets'](选选项)#选项

    def 确保加载(自身):
        """部署无预设时不请求。"""
        if 自身.会话预设() is None:#无
            return#跳过
        自身.属性['load']()#拉

    def 渲染(自身):
        """产出页眉标签；无预设则 None。"""
        预设=自身.会话预设()#预设 id
        if 预设 is None:#无
            return None#不画
        翻译=自身.属性['t']#翻译
        选项=None#命中项
        for 项 in 自身.取选项列表():#找
            if 项['id']==预设:#命中
                选项=项#记下
                break#停
        展示=预设展示文案(选项,翻译) if 选项 is not None else None#展示
        名=展示['name'] if 展示 is not None else 预设#名
        说明=展示['description'] if 展示 is not None and 'description' in 展示 else None#说明
        if 说明 is None:#回退提示
            说明=翻译('headerHint')#页眉提示
        return {#视图
            'type':'agent-preset-label',#类型
            'name':名,#名
            'title':说明,#悬停
            'presetId':预设,#id
            'cssModule':'预设标签.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有
            合并=dict(属性) if 属性 is not None else {}#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
