"""触发候选菜单：渲染 InputTriggerService 菜单仓到 input.overlay。

对齐上游 `ui-input-trigger/src/client/MenuView.tsx`。公开面仅中文名。
"""

__all__=['菜单视图','选项标识','样式表']#仅中文公开名

样式表='''#对齐 MenuView.module.css
.menu{position:absolute;bottom:calc(100% + 4px);left:0;z-index:100;min-width:min(260px,100%);max-width:min(537px,100%);max-height:320px;overflow:hidden;padding:4px;display:flex;flex-direction:column;border:1px solid var(--dsw-alias-border-inverted);border-radius:12px;background:var(--dsw-specific-menu);box-shadow:var(--dsw-shadow-lv3)}
.viewport{display:flex;flex-direction:column;min-height:0;overflow-y:auto}
.item{display:flex;align-items:center;gap:8px;width:100%;min-height:40px;padding:8px 10px;border:none;border-radius:10px;background:transparent;cursor:pointer;font-size:14px;line-height:22px;color:var(--dsw-alias-label-primary);text-align:left}
.item:hover,.item.active{background:var(--dsw-alias-interactive-bg-hover)}
.itemName{flex:none;max-width:40%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.itemDescription{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--dsw-alias-label-tertiary)}
.groupTitle{padding:8px 10px;font-size:12px;line-height:16px;color:var(--dsw-alias-label-tertiary)}
.loading{display:flex;align-items:center;min-height:40px;padding:8px 10px;font-size:14px;line-height:22px;color:var(--dsw-alias-label-dimmed)}
'''#样式表结束

def 选项标识(来源,下标):#DOM id
    """aria-activedescendant 目标。"""
    return 'dsh-slash-option-'+来源+'-'+str(下标)#拼 id

def 缺省翻译(键,_插值=None):#无文案函数
    """原样返回键。"""
    return 键#键

class 菜单视图:#候选菜单叠层组件
    """打开时渲染分组；关闭返回 None。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """产出与上游 JSX 同构的结构化视图。"""
        菜单=自身.属性['menu'] if 'menu' in 自身.属性 else None#菜单仓
        翻译=自身.属性['t'] if 't' in 自身.属性 else 缺省翻译#翻译
        点选=自身.属性['onPick'] if 'onPick' in 自身.属性 else None#点选
        关闭=自身.属性['onDismiss'] if 'onDismiss' in 自身.属性 else None#关闭
        if 菜单 is None:#无
            return None#空
        态=菜单.getSnapshot()#快照
        if not 态['open']:#关闭
            return None#不渲染
        高亮=态['highlight']#高亮
        组视图=[]#分组
        for 组 in 态['groups']:#各组
            if 组['status']=='ready' and len(组['items'])==0:#空就绪；length 语义
                continue#跳过
            项视图=[]#项
            if 组['status']=='pending':#待加载
                项视图=None#用 loading 行
            else:#就绪
                for 号,项 in enumerate(组['items']):#逐项
                    活=高亮 is not None and 高亮['source']==组['source'] and 高亮['index']==号#是否高亮
                    def 造点选(来源,下标):#闭包点选
                        """点该项。"""
                        def 点该项():#点击
                            """转发 onPick。"""
                            if 点选 is not None:#有
                                点选(来源,下标)#点选
                        return 点该项#回调
                    项视图.append({#一项
                        'id':选项标识(组['source'],号),#id
                        'active':活,#高亮
                        'name':项['name'] if 'name' in 项 else None,#名
                        'description':项['description'] if 'description' in 项 else None,#说明
                        'icon':项['icon'] if 'icon' in 项 else None,#图标
                        'pick':造点选(组['source'],号),#点选
                    })#项结束
            组视图.append({#一组
                'source':组['source'],#来源
                'title':翻译(组['source']),#标题
                'status':组['status'],#状态
                'loading':翻译('loading'),#加载文
                'items':项视图,#项或 None
            })#组结束
        活动标识=选项标识(高亮['source'],高亮['index']) if 高亮 is not None else None#activedescendant
        return {#结构化视图
            'type':'slash-menu-view',#类型
            'aria':翻译('suggestions.aria'),#aria
            'activeId':活动标识,#activedescendant
            'groups':组视图,#分组
            'dismiss':关闭,#关闭
            'css':样式表,#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
