"""智能体预设偏好行：新会话默认预设选择器。

对齐上游 `ui-agent-preset/src/client/AgentPresetRow.tsx`。公开面仅中文名。
"""
from .文案 import 预设展示文案#展示文案

__all__=['预设行','样式表']#仅中文公开名

样式表='''#对齐 AgentPresetRow.module.css
.row{display:flex;align-items:center;gap:16px;padding:16px 0;border-bottom:1px solid var(--dsw-alias-border-l2)}
.rowText{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px;padding-right:48px}
.title{font-size:14px;font-weight:400;line-height:22px;color:var(--dsw-alias-label-primary)}
.desc{font-size:12px;font-weight:400;line-height:18px;color:var(--dsw-alias-label-tertiary)}
.selector{display:inline-flex;align-items:center;gap:12px;height:36px;padding:0 14px;border:none;border-radius:18px;background:var(--dsw-alias-bg-module-platform);font:inherit;font-size:14px;line-height:22px;color:var(--dsw-alias-label-primary);cursor:pointer}
'''#样式表结束

class 预设行:
    """部署无预设时返回 None。属性与快照都是 dict。"""
    def __init__(自身,属性):
        """记下 props 并触发 load。"""
        自身.属性=属性#合成
        自身.打开=False#菜单
        属性['load']()#拉名册

    def 更新(自身,属性):
        """不可写则关菜单。"""
        自身.属性=属性#最新
        态=自身.状态()#状态
        if 态['writable'] and 态['status']!='unavailable':#仍可用
            return#保留
        自身.打开=False#关

    def 状态(自身):
        """经 useAgentPreset。"""
        def 恒等(快照):
            """整表。"""
            return 快照#快照
        return 自身.属性['useAgentPreset'](恒等)#快照

    def 选定(自身,标识):
        """关菜单并 select。"""
        自身.打开=False#关
        自身.属性['select'](标识)#提交

    def 切换菜单(自身):
        """翻转菜单开闭。"""
        自身.打开=not 自身.打开#翻转

    def 渲染(自身):
        """产出与上游 JSX 同构的结构化视图。"""
        态=自身.状态()#状态
        if 态['status']=='unavailable':#无预设
            return None#不渲染
        翻译=自身.属性['t']#翻译
        忙=态['status'] in ('loading','saving')#忙碌
        当前=态['currentValue']#当前
        选中=None#选项
        for 项 in 态['options']:#找
            if 项['id']==当前:#命中
                选中=项#记下
                break#停
        展示=预设展示文案(选中,翻译) if 选中 is not None else None#展示
        if 当前=='' :#加载中标签
            标签=翻译('loading')#加载
        elif 展示 is not None:#有展示
            标签=展示['name']#名
        else:#回退
            标签=当前#id
        说明=态['error']#错误
        if 说明 is None:#无错
            说明=翻译('description')#说明
        return {#结构化视图
            'type':'agent-preset-row',#类型
            'title':翻译('title'),#标题
            'description':说明,#说明
            'label':标签,#选择器标签
            'open':自身.打开,#菜单开
            'busy':忙,#忙碌
            'writable':态['writable'],#可写
            'options':态['options'],#选项
            'currentValue':当前,#当前
            'toggle':自身.切换菜单,#切换
            'select':自身.选定,#选定
            'css':样式表,#样式
        }#视图结束

    def __call__(自身,属性=None):
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
