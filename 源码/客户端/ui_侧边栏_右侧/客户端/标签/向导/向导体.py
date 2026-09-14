
__all__=['向导体','样式表','最多带说明入口数']#仅中文公开名

最多带说明入口数=4#超过则隐藏各入口 description

样式表='''#对齐 GuideBody.module.css
.guide{display:flex;flex-direction:column;gap:14px;align-items:center;justify-content:center;box-sizing:border-box;min-height:100%;padding:0 24px}
.guide::after{content:'';flex:0 1 10%}
.hero{display:flex;margin-bottom:16px;color:var(--dsw-static-neutral-200)}
.entry{display:flex;gap:14px;align-items:center;box-sizing:border-box;width:380px;max-width:100%;min-height:56px;padding:14px 20px;color:var(--dsw-alias-label-primary);font:inherit;text-align:left;background:var(--dsw-alias-bg-layer-1);border:0.5px solid var(--dsw-alias-border-l4);border-radius:24px;cursor:pointer}
.entry:hover{background:var(--dsw-alias-interactive-bg-hover)}
.entryIcon{display:flex;flex:none;align-items:center;justify-content:center;width:26px;height:26px;color:var(--dsw-alias-label-secondary)}
.placeholderInk{color:var(--dsw-alias-label-tertiary)}
.entryText{display:flex;flex-direction:column;gap:3px;min-width:0}
.entryTitle{overflow:hidden;font-size:15px;line-height:1.4;white-space:nowrap;text-overflow:ellipsis}
.entryDescription{overflow:hidden;color:var(--dsw-alias-label-caption);font-size:13px;line-height:1.4;white-space:nowrap;text-overflow:ellipsis}
'''#样式表结束


class 向导体:#向导正文视图模型
    """链席回退为出厂向导：罗盘水印与入口胶囊。"""

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

    def 入口节点(自身,条目,带说明):
        """一枚入口胶囊。"""
        图标=条目['icon'] if 'icon' in 条目 else None#图标
        说明=None#说明
        if 带说明:#短列表
            取说明=条目['description'] if 'description' in 条目 else None#可选
            if 取说明 is not None:#有
                说明=取说明()#文案
        尺寸=22 if 说明 is None else 26#图标边
        图标类='entryIcon'+( '' if 图标 is not None else ' placeholderInk')#类
        子=[{#图标
            'type':'span',
            'className':图标类,
            'props':{'icon':图标,'size':尺寸},
        }]#图标结束
        文子=[{'type':'span','className':'entryTitle','text':条目['title']()}]#标题
        if 说明 is not None:#有说明
            文子.append({'type':'span','className':'entryDescription','text':说明})#说明
        子.append({'type':'span','className':'entryText','children':文子})#文
        return {#按钮
            'type':'button',
            'className':'entry',
            'props':{'data-sidebar-right-guide-entry':条目['kind'],'entry':条目},
            'onClick':lambda 甲=条目:自身.点选入口(甲),
            'children':子,
        }#按钮结束

    def 出厂树(自身):
        """出厂向导结构树：罗盘 + 入口列。"""
        属性=自身.属性#props
        用入口=属性['useGuideEntries'] if 'useGuideEntries' in 属性 else None#入口钩
        条目表=用入口(lambda 表:表) if 用入口 is not None else ()#条目
        带说明=len(条目表)<=最多带说明入口数#短列表
        入口节点=[自身.入口节点(条目,带说明) for 条目 in 条目表]#胶囊
        return {#树
            'type':'div',
            'className':'guide',
            'props':{'data-sidebar-right-guide':True},
            'children':[
                {'type':'span','className':'hero','props':{'aria-hidden':'true','glyph':'compass','size':56}},
                *入口节点,
            ],
        }#树结束

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
