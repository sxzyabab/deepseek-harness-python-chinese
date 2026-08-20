"""子智能体只读撰写器：目录寻址会话无法接受人工输入时的替换面。

对齐上游 `ui-subagent/src/client/SubagentReadOnlyComposer.tsx`。公开面仅中文名。
"""

__all__=['只读撰写器','样式表']#仅中文公开名

样式表='''#对齐 SubagentReadOnlyComposer.module.css
.frame{display:flex;align-items:center;justify-content:center;gap:8px;margin:0 24px 20px;min-height:54px;padding:10px 16px;border:1px solid var(--dsw-alias-border-l2);border-radius:14px;background:var(--dsw-alias-bg-layer-1);color:var(--dsw-alias-label-tertiary);font-size:13px;line-height:20px}
.frame strong{color:var(--dsw-alias-label-primary);font-weight:510}
'''#样式表结束

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 只读撰写器:#只读撰写器替换面
    """说明为何普通撰写器不可用。"""

    def __init__(自身,属性=None):#记下 props
        """记下匹配原因与翻译。"""
        自身.属性=属性 or {}#合成 props

    def 更新(自身,属性):#刷新 props
        """刷新合成 props。"""
        自身.属性=属性#新 props

    def 渲染(自身):#产出结构树
        """与上游 JSX 同构。"""
        匹配=取字段(自身.属性,'matched') or {}#认领结果
        翻译=取字段(自身.属性,'t')#文案
        一次性=取字段(匹配,'reason')=='one-shot'#一次性
        标题键='readonly.oneShot.title' if 一次性 else 'readonly.title'#标题键
        正文键='readonly.oneShot.body' if 一次性 else 'readonly.body'#正文键
        return {#结构树
            'type':'subagent-readonly-composer',#类型
            'role':'status',#无障碍角色
            'class':'frame',#样式类
            'title':翻译(标题键) if callable(翻译) else 标题键,#标题
            'body':翻译(正文键) if callable(翻译) else 正文键,#正文
            'reason':取字段(匹配,'reason'),#原因
        }#结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
