
__all__=['向导体','样式表','最多带说明入口数']#仅中文公开名

from nicegui import ui as 界面
from ....异常 import 异常原文

最多带说明入口数=4#超过则隐藏各入口 description

样式表='''#对齐 GuideBody.module.css
.guide{display:flex;flex-direction:column;gap:14px;align-items:center;justify-content:center;box-sizing:border-box;min-height:100%;padding:0 24px}
.guide::after{content:'';flex:0 1 10%}
.hero{display:flex;margin-bottom:16px;color:var(--dsw-static-neutral-200)}
.entry{display:flex;gap:14px;align-items:center;box-sizing:border-box;width:380px;max-width:100%;min-height:56px;padding:14px 20px;color:var(--dsw-alias-label-primary);font:inherit;text-align:left;background:var(--dsw-alias-bg-layer-1);border:0.5px solid var(--dsw-alias-border-l3);border-radius:var(--dsw-radius-xl);cursor:pointer}
.entry:hover,button.q-btn.entry:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
button.q-btn.entry{width:380px;max-width:100%;min-height:56px;padding:14px 20px;justify-content:flex-start;border:0.5px solid var(--dsw-alias-border-l3) !important;border-radius:var(--dsw-radius-xl);background:var(--dsw-alias-bg-layer-1) !important;color:var(--dsw-alias-label-primary) !important;box-shadow:none !important}
button.q-btn.entry .q-btn__content{gap:14px;justify-content:flex-start;flex-wrap:nowrap;width:100%}
.entryIcon{display:flex;flex:none;align-items:center;justify-content:center;width:26px;height:26px;color:var(--dsw-alias-label-secondary)}
.placeholderInk{color:var(--dsw-alias-label-tertiary)}
.entryText{display:flex;flex-direction:column;gap:3px;min-width:0}
.entryTitle{overflow:hidden;font-size:14px;line-height:1.4;white-space:nowrap;text-overflow:ellipsis}
.entryDescription{overflow:hidden;color:var(--dsw-alias-label-tertiary);font-size:11px;line-height:1.4;white-space:nowrap;text-overflow:ellipsis}
.entryCell{width:380px;max-width:100%}
body[data-ds-dark-theme] .hero{color:var(--dsw-static-neutral-700)}
'''#样式表结束

界面.add_css(样式表,shared=True)

from ...约定.槽位 import 席名右侧向导,席名右侧向导条目#席名
from .向导标题 import 立方标记,罗盘标记,画字形#字形


class 向导体:#向导正文视图模型
    '链席回退为出厂向导：罗盘水印与入口胶囊'

    def __init__(自身,属性):
        '记下合成 props。槽位只调用构造，键齐了就画。'
        自身.属性=属性 if 属性 is not None else {}#props
        if 'useGuideEntries' in 自身.属性 or 'renderSlotChain' in 自身.属性 or 'useTabInfo' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#最新

    def 点选入口(自身,条目):
        '入口打开对应种类并替换本签'
        钩=自身.属性['useTabInfo'] if 'useTabInfo' in 自身.属性 else None#标签钩
        if not callable(钩):#没有
            return#不打开
        信息=钩()#标签信息
        签=信息['tab'] if isinstance(信息,dict) else 信息.tab#记录
        动作=签['actions'] if isinstance(签,dict) else 签.actions#动作
        动作['openTab'](条目['kind'],{'replaceTab':True})

    def _读入口(自身):
        '向导入口表；钩子未就绪则为空'
        自身._入口失败=None
        用入口=自身.属性['useGuideEntries'] if 'useGuideEntries' in 自身.属性 else None#入口钩
        if not callable(用入口):#无
            return ()#空
        try:
            值=用入口(lambda 表:表)#整表
        except Exception as 错误:
            自身._入口失败=错误
            return ()#空
        if 值 is None:#无
            return ()#空
        return tuple(值)#条目

    def _说明文(自身,条目,带说明):
        '短列表才取说明'
        if not 带说明:#长列表
            return None#不显示
        取说明=条目['description'] if 'description' in 条目 else None#可选
        if not callable(取说明):#无
            return None#无
        文=取说明()#文案
        if isinstance(文,str) and 文!='':
            return 文#说明
        return None#无

    def _出口内容(自身,结果):
        '槽出口的 content；其它原样'
        if isinstance(结果,dict) and 结果.get('type')=='slot-outlet':#出口
            return 结果.get('content')#内容
        return 结果#原样

    def _是回退(自身,结果,标记):
        '链或键控席没有当选，退回标记'
        return 自身._出口内容(结果) is 标记#同一标记

    def 画胶囊(自身,条目,带说明):
        '出厂入口：按钮、字形、标题，短列表再加说明'
        说明=自身._说明文(条目,带说明)#说明
        尺寸=22 if 说明 is None else 26#图标边
        图标=条目['icon'] if 'icon' in 条目 else None#登记的字形
        图标类='entryIcon' if 图标 is not None else 'entryIcon placeholderInk'#类
        def 点(条=条目):
            '打开该入口'
            自身.点选入口(条)
        种类=条目['kind'] if 'kind' in 条目 else ''#种类
        钮=界面.button(on_click=点).props('flat no-caps align=left').classes('entry')#胶囊
        钮.props('data-sidebar-right-guide-entry='+str(种类))#标记
        with 钮:#内容
            if isinstance(图标,str) and 图标.startswith('<'):#已是 svg
                界面.html(图标,sanitize=False).classes(图标类)#字形
            elif callable(图标):#宿主字形
                try:#交给它画
                    图标(尺寸)#画
                except TypeError:#不收尺寸
                    画字形(立方标记,尺寸,图标类)#立方
            else:#没有登记字形
                画字形(立方标记,尺寸,图标类)#立方
            标题=条目['title']() if 'title' in 条目 and callable(条目['title']) else ''#标题
            with 界面.column().classes('entryText'):#文
                界面.label(str(标题)).classes('entryTitle')#题
                if 说明 is not None:
                    界面.label(说明).classes('entryDescription')#述

    def 画入口(自身,条目,带说明):
        '先画登记的入口席；没有登记再画出厂胶囊'
        with 界面.element('div').classes('entryCell'):#一格
            画=自身.属性['renderSlot'] if 'renderSlot' in 自身.属性 else None#子槽
            标记=object()#回退身份
            已画=False#席是否已画
            if callable(画):
                说明=自身._说明文(条目,带说明)#说明
                拥有={'entryId':条目['id'] if 'id' in 条目 else None,'kind':条目['kind'] if 'kind' in 条目 else None}#属主
                if 'title' in 条目 and callable(条目['title']):#标题
                    拥有['title']=条目['title']()#文
                if 说明 is not None:#说明
                    拥有['description']=说明#文
                钩=自身.属性['useTabInfo'] if 'useTabInfo' in 自身.属性 else None#钩上下文
                try:#子槽失败则出厂胶囊
                    结果=画(席名右侧向导条目,拥有,{'entryKey':条目['providerId'] if 'providerId' in 条目 else None,'hookContext':钩,'fallback':标记})#画席
                    已画=not 自身._是回退(结果,标记)#当选才算画出
                except Exception as 错误:
                    界面.label(异常原文(错误))
                    已画=False#改出厂
            if not 已画:#没有登记
                自身.画胶囊(条目,带说明)#胶囊

    def 画出厂向导(自身):
        '罗盘水印和入口列'
        条目表=自身._读入口()#入口
        带说明=len(条目表)<=最多带说明入口数#短列表
        列=界面.column().classes('guide')#向导列
        列.props('data-sidebar-right-guide')#标记
        with 列:#内容
            if 自身._入口失败 is not None:
                界面.label(异常原文(自身._入口失败))
            罗盘=画字形(罗盘标记,56,'hero')#罗盘
            罗盘.props('aria-hidden=true')#装饰
            for 条目 in 条目表:#逐入口
                自身.画入口(条目,带说明)#一格

    def _链已画出(自身):
        '替换链有当选时，当选组件已在构造里画出'
        链=自身.属性['renderSlotChain'] if 'renderSlotChain' in 自身.属性 else None#链
        if not callable(链):#无
            return False#出厂
        标记=object()#回退身份
        钩=自身.属性['useTabInfo'] if 'useTabInfo' in 自身.属性 else None#钩上下文
        try:#链崩溃则出厂向导
            结果=链(席名右侧向导,{},{'hookContext':钩,'fallback':标记})#选举
        except Exception as 错误:
            界面.label(异常原文(错误))
            return False#出厂
        return not 自身._是回退(结果,标记)#当选

    def 渲染(自身):
        '链席当选则用它；否则画出厂罗盘和入口'
        if 自身._链已画出():#替换链已画
            return#一具正文
        自身.画出厂向导()#出厂
