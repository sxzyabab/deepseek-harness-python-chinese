"""官方 popupSelect 壳：渲染一会话弹出控制器到 input.overlay。

对齐上游 `ui-commands/src/client/PopupSelectView.tsx`。公开面仅中文名。
"""
from .弹出 import 过滤选项#本地过滤

__all__=['弹出选择视图','样式表']#仅中文公开名

样式表='''#对齐 PopupSelectView.module.css
.card{position:absolute;bottom:calc(100% + 4px);left:0;z-index:100;padding:4px;display:flex;flex-direction:column;min-width:min(220px,100%);max-width:100%;max-height:320px;overflow:hidden;border:1px solid var(--dsw-alias-border-inverted);border-radius:12px;background:var(--dsw-specific-menu);box-shadow:var(--dsw-shadow-lv3)}
.viewport{display:flex;flex-direction:column;min-height:0;overflow-y:auto}
.row{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:8px;cursor:pointer;font-size:13px;color:var(--dsw-alias-label-primary)}
.rowActive{background:var(--dsw-alias-interactive-bg-hover)}
.label{flex:1 1 auto;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.detail{font-size:12px;color:var(--dsw-alias-label-tertiary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.status{padding:8px 10px;font-size:13px;color:var(--dsw-alias-label-tertiary)}
.search{margin:2px 2px 4px;padding:6px 8px;border:1px solid var(--dsw-alias-border-inverted);border-radius:8px;background:transparent;font-size:13px;color:var(--dsw-alias-label-primary);outline:none}
.error{display:flex;align-items:center;gap:8px;padding:6px 8px;font-size:12px;color:var(--dsw-alias-state-error-primary)}
.retry{padding:2px 8px;border:1px solid var(--dsw-alias-border-inverted);border-radius:6px;background:transparent;font-size:12px;cursor:pointer}
'''#样式表结束

def 读(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 弹出选择视图:#popupSelect 壳组件
    """打开时渲染卡片；关闭返回 None。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """产出与上游 JSX 同构的结构化视图。"""
        弹出=读(自身.属性,'popup')#控制器
        翻译=读(自身.属性,'t')#翻译
        if 弹出 is None:#无
            return None#空
        态=弹出.state.getSnapshot()#快照
        if not 态.get('open'):#关闭
            return None#不渲染
        行=过滤选项(态.get('options') or [],态.get('search') or '')#过滤行
        确认=读(态.get('confirming'),'confirmation') if 态.get('confirming') else None#确认文案
        return {#结构化视图
            'type':'popup-select-view',#类型
            'command':态.get('command'),#命令
            'status':态.get('status'),#状态
            'search':态.get('search'),#搜索
            'active':态.get('active'),#高亮
            'submitting':态.get('submitting'),#提交中
            'error':态.get('error'),#错误
            'rows':行,#行
            'confirming':态.get('confirming'),#确认项
            'confirmation':确认,#确认文案
            'acknowledged':态.get('acknowledged'),#勾选
            'setSearch':弹出.setSearch,#改搜索
            'move':弹出.move,#移动
            'highlight':弹出.highlight,#高亮
            'select':弹出.select,#选定
            'retry':弹出.retry,#重试
            'dismiss':弹出.dismiss,#关闭
            'acknowledge':弹出.acknowledge,#勾选
            'cancelConfirmation':弹出.cancelConfirmation,#取消确认
            'confirm':弹出.confirm,#确认
            'aria':翻译('overlay.aria',{'command':str(态.get('command'))}) if 翻译 else '',#浮层 aria
            'css':样式表,#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
