"""智能体预设偏好行：新会话默认预设选择器。

对齐上游 `ui-agent-preset/src/client/AgentPresetRow.tsx`。公开面仅中文名。
"""
from .文案 import 预设展示文案#展示文案

__all__=['预设行','样式表']#仅中文公开名

样式表='''#对齐 AgentPresetRow.module.css
.row{display:flex;align-items:center;gap:8px;padding:16px 0;border-bottom:1px solid var(--dsw-alias-border-l2)}
.rowText{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px;padding-right:48px}
.title{font-size:14px;font-weight:400;line-height:22px;color:var(--dsw-alias-label-primary)}
.desc{font-size:12px;font-weight:400;line-height:18px;color:var(--dsw-alias-label-tertiary)}
.selector{display:inline-flex;align-items:center;gap:12px;height:36px;padding:0 14px;border:none;border-radius:18px;background:var(--dsw-alias-bg-module-platform);font:inherit;font-size:14px;line-height:22px;color:var(--dsw-alias-label-primary);cursor:pointer}
'''#样式表结束

def 读(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 预设行:#通用设置行组件
    """部署无预设时返回 None。"""
    def __init__(自身,属性):#构造
        """记下 props 并触发 load。"""
        自身.属性=属性#合成
        自身.打开=False#菜单
        加载=读(属性,'load')#加载
        if 加载 is not None:#有
            加载()#拉名册

    def 更新(自身,属性):#刷新
        """不可写则关菜单。"""
        自身.属性=属性#最新
        态=自身.状态()#状态
        if 读(态,'writable') and 读(态,'status')!='unavailable':#仍可用
            return#保留
        自身.打开=False#关

    def 状态(自身):#读设置快照
        """经 useAgentPreset。"""
        用=读(自身.属性,'useAgentPreset')#选择器
        if 用 is None:#无
            return {'status':'unavailable','options':[],'currentValue':'','writable':False,'error':None}#不可用
        return 用(lambda 快照:快照) or {}#快照

    def 选定(自身,标识):#选定默认
        """关菜单并 select。"""
        自身.打开=False#关
        选=读(自身.属性,'select')#选定
        if 选 is not None:#有
            选(标识)#提交

    def 渲染(自身):#结构化视图
        """产出与上游 JSX 同构的结构化视图。"""
        态=自身.状态()#状态
        if 读(态,'status')=='unavailable':#无预设
            return None#不渲染
        翻译=读(自身.属性,'t')#翻译
        忙=读(态,'status') in ('loading','saving')#忙碌
        当前=读(态,'currentValue') or ''#当前
        选中=None#选项
        for 项 in 读(态,'options') or []:#找
            if 读(项,'id')==当前:#命中
                选中=项#记下
                break#停
        展示=预设展示文案(选中,翻译) if 选中 is not None and 翻译 else None#展示
        if 当前=='' and 翻译 is not None:#加载中标签
            标签=翻译('loading')#加载
        elif 展示 is not None:#有展示
            标签=展示['name']#名
        else:#回退
            标签=当前#id
        说明=读(态,'error')#错误
        if 说明 is None and 翻译 is not None:#无错
            说明=翻译('description')#说明
        return {#结构化视图
            'type':'agent-preset-row',#类型
            'title':翻译('title') if 翻译 else 'Agent preset',#标题
            'description':说明,#说明
            'label':标签,#选择器标签
            'open':自身.打开,#菜单开
            'busy':忙,#忙碌
            'writable':读(态,'writable'),#可写
            'options':读(态,'options') or [],#选项
            'currentValue':当前,#当前
            'toggle':lambda:setattr(自身,'打开',not 自身.打开),#切换
            'select':自身.选定,#选定
            'css':样式表,#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
