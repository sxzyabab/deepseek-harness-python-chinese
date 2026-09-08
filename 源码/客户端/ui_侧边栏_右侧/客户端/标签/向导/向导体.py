"""向导正文：链宿主与出厂向导回退。

对齐上游 `ui-sidebar-right/src/client/tabs/guide/GuideBody.tsx`。公开面仅中文名。
无 React：视图模型产出结构树 dict；链席由宿主 renderSlotChain 调度。
"""

__all__=['向导体','样式表']#仅中文公开名

样式表='''#对齐 GuideBody.module.css
.guide{display:flex;flex-direction:column;gap:8px;align-items:center;padding-top:24px;text-align:center}
.guideTitle{margin:0;color:var(--dsw-alias-label-primary);font-size:var(--dsh-content-font-size, 14px);font-weight:500;line-height:1.6}
.guideBody{margin:0;color:var(--dsw-alias-label-secondary);font-size:var(--dsh-content-font-size-secondary, 13px);line-height:1.6}
.entries{display:grid;grid-template-columns:repeat(auto-fill, minmax(160px, 1fr));gap:8px;width:100%;max-width:480px;margin-top:16px}
.entry{display:flex;gap:8px;align-items:flex-start;padding:10px 12px;color:inherit;font:inherit;text-align:left;background:transparent;border:0.5px solid var(--dsw-alias-border-l1);border-radius:8px;cursor:pointer}
.entry:hover{background:var(--dsw-alias-interactive-bg-hover)}
.entryIcon{display:flex;flex:none;margin-top:1px;color:var(--dsw-alias-label-secondary)}
.entryText{display:flex;flex-direction:column;gap:2px;min-width:0}
.entryTitle{color:var(--dsw-alias-label-primary);font-size:var(--dsh-content-font-size, 14px);line-height:1.4}
.entryDescription{color:var(--dsw-alias-label-secondary);font-size:var(--dsh-content-font-size-secondary, 13px);line-height:1.4}
'''#样式表结束


class 向导体:#向导正文视图模型
    """链席回退为出厂向导：说明文案与入口盒。"""

    def __init__(自身,属性):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#props

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#最新

    def 点选入口(自身,条目):
        """入口打开对应种类并替换本签。"""
        信息=自身.属性['useTabInfo']()#标签信息
        信息['tab']['actions']['openTab'](条目['kind'],{'replaceTab':True})#开

    def 出厂树(自身):
        """出厂向导结构树。"""
        属性=自身.属性#props
        翻译=属性['t']#文案
        用入口=属性['useGuideEntries'] if 'useGuideEntries' in 属性 else None#入口钩
        条目表=用入口(lambda 表:表) if 用入口 is not None else ()#条目
        入口节点=[]#节点
        for 序,条目 in enumerate(条目表):#逐入口
            图标=条目['icon'] if 'icon' in 条目 else None#图标
            子=[]#子
            if 图标 is not None:#有图标
                子.append({'type':'span','className':'entryIcon','props':{'icon':图标,'size':16}})#图标
            子.append({'type':'span','className':'entryText','children':[#文
                {'type':'span','className':'entryTitle','text':条目['title']()},
                {'type':'span','className':'entryDescription','text':条目['description']()},
            ]})#文结束
            入口节点.append({#按钮
                'type':'button',
                'className':'entry',
                'props':{'data-sidebar-right-guide-entry':条目['kind'],'entry':条目},
                'onClick':lambda 甲=条目:自身.点选入口(甲),
                'children':子,
            })#按钮结束
        子节点=[#主文
            {'type':'p','className':'guideTitle','text':翻译('guide.lead')},
            {'type':'p','className':'guideBody','text':翻译('guide.body')},
        ]#主文
        if len(入口节点)>0:#有入口
            子节点.append({'type':'div','className':'entries','children':入口节点})#入口区
        return {'type':'div','className':'guide','props':{'data-sidebar-right-guide':True},'children':子节点}#树

    def 渲染(自身):
        """经链席；无替换则出厂树。"""
        属性=自身.属性#props
        链=属性['renderSlotChain'] if 'renderSlotChain' in 属性 else None#链
        回退=自身.出厂树()#回退
        if 链 is None:#无链
            return 回退#出厂
        return 链('sidebar.right.tab.guide',{},{#链选项
            'hookContext':属性['useTabInfo'],
            'fallback':回退,
        })#链结果
