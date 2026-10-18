'向导正文。链上有人接走就用那一页，否则画出入口'
from .....模块.客户端.通告 import 取握手窗口
import os
from .....ui_对话.异常 import 注入模块样式文件,标样式模块
from ...约定.槽位 import 席名右侧向导,席名右侧向导条目
from .向导标题 import 罗盘字形,立方字形

__all__=['向导体','入口盒','出厂向导']

样式路径=os.path.join(os.path.dirname(__file__),'向导体.module.css')
样式模块='sidebar-right-guide'
描述上限=4


def _窗口(属性):
    '调用方带来的窗口，否则用桥上的窗口'
    if isinstance(属性,dict) and 属性.get('window') is not None:
        return 属性['window']
    return 取握手窗口()


def _订(钩子,回调):
    '选择器钩子上挂着的订阅'
    订=getattr(钩子,'_subscribe',None)
    if callable(订):
        return 订(回调)
    return None


def _键帽(文档,键表):
    '一串按键。共享键帽组件还没迁过来，这里按同样的字画出来'
    if not isinstance(键表,(list,tuple)) or len(键表)==0:
        return None
    根=文档.createElement('span')
    for 键 in 键表:
        帽=文档.createElement('kbd')
        帽.textContent=str(键)
        根.appendChild(帽)
    return 根


class 入口盒:
    '一个入口：图标、标题，名单短的时候还有说明'

    def __init__(自身,窗口,入口,写出说明,快捷,选中):
        '记下这一条'
        自身.窗口=窗口
        自身.属性={'window':窗口}
        自身.入口=入口
        自身.写出说明=写出说明
        自身.快捷=快捷
        自身.选中=选中
        自身.根=None

    def 渲染(自身):
        '点一下就按这个种类打开'
        文档=自身.窗口.document
        注入模块样式文件(文档,'向导体样式',样式路径,样式模块)
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='entry'
        标样式模块(钮,样式模块)
        钮.setAttribute('data-sidebar-right-guide-entry',str(自身.入口.get('kind')))
        if 自身.快捷 is not None and 自身.快捷.get('aria'):
            钮.setAttribute('aria-keyshortcuts',自身.快捷['aria'])

        def 点击():
            '交给外面打开'
            自身.选中(自身.入口)

        钮.addEventListener('click',lambda 事件: 点击())
        说明=None
        if 自身.写出说明 and callable(自身.入口.get('description')):
            说明=自身.入口['description']()
        尺寸=22 if 说明 is None else 26
        图标=自身.入口.get('icon')
        图标盒=文档.createElement('span')
        图标盒.className='entryIcon'
        标样式模块(图标盒,样式模块)
        类名='placeholderInk' if 图标 is None else None
        if 图标 is None:
            图=立方字形(自身.窗口,尺寸,类名).渲染()
        elif hasattr(图标,'渲染'):
            图=图标.渲染()
        elif callable(图标):
            图=图标(自身.窗口,尺寸,类名)
        else:
            图=立方字形(自身.窗口,尺寸,类名).渲染()
        if 图 is not None and hasattr(图,'tagName'):
            图标盒.appendChild(图)
        钮.appendChild(图标盒)
        文=文档.createElement('span')
        文.className='entryText'
        标样式模块(文,样式模块)
        题=文档.createElement('span')
        题.className='entryTitle'
        标样式模块(题,样式模块)
        题.textContent=自身.入口['title']() if callable(自身.入口.get('title')) else ''
        文.appendChild(题)
        if 说明 is not None:
            述=文档.createElement('span')
            述.className='entryDescription'
            标样式模块(述,样式模块)
            述.textContent=str(说明)
            文.appendChild(述)
        钮.appendChild(文)
        if 自身.快捷 is not None:
            帽=_键帽(文档,自身.快捷.get('keys'))
            if 帽 is not None:
                钮.appendChild(帽)
        自身.根=钮
        return 钮


class 出厂向导:
    '罗盘下面一列入口'

    def __init__(自身,窗口,子节点):
        '记下入口节点'
        自身.窗口=窗口
        自身.属性={'window':窗口}
        自身.子节点=子节点
        自身.根=None

    def 渲染(自身):
        '居中的一列'
        文档=自身.窗口.document
        注入模块样式文件(文档,'向导体样式',样式路径,样式模块)
        根=文档.createElement('div')
        根.className='guide'
        标样式模块(根,样式模块)
        根.setAttribute('data-sidebar-right-guide','')
        英雄=文档.createElement('span')
        英雄.className='hero'
        标样式模块(英雄,样式模块)
        英雄.setAttribute('aria-hidden','true')
        英雄.appendChild(罗盘字形(自身.窗口,56).渲染())
        根.appendChild(英雄)
        for 节点 in 自身.子节点:
            if 节点 is not None and hasattr(节点,'tagName'):
                根.appendChild(节点)
        自身.根=根
        return 根


class 向导体:
    '链槽优先。没有人接就画出厂向导'

    def __init__(自身,属性=None):
        '记下份额'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身._退订=[]
        自身.渲染()
        自身._订阅()

    def __call__(自身,属性=None):
        '再次绘制'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def _订阅(自身):
        '入口或快捷键变了就重画'
        def 变更():
            '还挂着才重画'
            if 自身.根 is not None and getattr(自身.根,'isConnected',True) is False:
                for 退 in 自身._退订:
                    退()
                自身._退订.clear()
                return
            自身.渲染()
        for 名 in ('useGuideEntries','useShortcuts','useTabInfo'):
            退=_订(自身.属性.get(名),变更)
            if 退 is not None:
                自身._退订.append(退)

    def 渲染(自身):
        '链的后备就是出厂向导'
        窗口=_窗口(自身.属性)
        文档=窗口.document
        注入模块样式文件(文档,'向导体样式',样式路径,样式模块)
        用签=自身.属性.get('useTabInfo')
        签={}
        if callable(用签):
            信息=用签()
            if isinstance(信息,dict) and isinstance(信息.get('tab'),dict):
                签=信息['tab']
        用入口=自身.属性.get('useGuideEntries')
        入口表=()
        if callable(用入口):
            def 原样(值):
                '入口名单'
                return 值
            读到=用入口(原样)
            if isinstance(读到,(list,tuple)):
                入口表=读到
        用快捷=自身.属性.get('useShortcuts')
        快捷表=()
        if callable(用快捷):
            def 原样快捷(值):
                '快捷键目录'
                return 值
            读到=用快捷(原样快捷)
            if isinstance(读到,(list,tuple)):
                快捷表=读到
        写出说明=len(入口表)<=描述上限
        格表=[]
        画槽=自身.属性.get('renderSlot')
        for 入口 in 入口表:
            说明=None
            if 写出说明 and callable(入口.get('description')):
                说明=入口['description']()
            快捷=None
            for 行 in 快捷表:
                if 行.get('id')==入口.get('commandId'):
                    快捷=行
                    break

            def 选中(选,动作=签.get('actions')):
                '在这张向导签的位置打开'
                if isinstance(动作,dict) and callable(动作.get('openTab')):
                    动作['openTab'](选['kind'],{'replaceTab':True})

            后备=入口盒(窗口,入口,写出说明,快捷,选中)
            格=文档.createElement('div')
            格.className='entryCell'
            标样式模块(格,样式模块)
            内容=None
            if callable(画槽):
                拥有={'entryId':入口.get('id'),'kind':入口.get('kind'),'title':入口['title']() if callable(入口.get('title')) else '','window':窗口}
                if 说明 is not None:
                    拥有['description']=说明
                内容=画槽(席名右侧向导条目,拥有,{
                    'entryKey':入口.get('providerId'),
                    'hookContext':用签,
                    'fallback':后备,
                })
            if 内容 is None:
                格.appendChild(后备.渲染())
            elif hasattr(内容,'tagName'):
                格.appendChild(内容)
            elif getattr(内容,'根',None) is not None:
                格.appendChild(内容.根)
            else:
                格.appendChild(后备.渲染())
            格表.append(格)
        后备页=出厂向导(窗口,格表)
        画链=自身.属性.get('renderSlotChain')
        根=None
        if callable(画链):
            根=画链(席名右侧向导,{},{'hookContext':用签,'fallback':后备页})
        if 根 is None:
            根=后备页.渲染()
        elif hasattr(根,'渲染'):
            画出=根.渲染()
            根=画出 if 画出 is not None else 后备页.渲染()
        elif getattr(根,'根',None) is not None:
            根=根.根
        自身.根=根 if hasattr(根,'tagName') else 后备页.渲染()
        父=自身.属性.get('parent')
        if 父 is not None and getattr(自身.根,'parentNode',None) is None:
            父.appendChild(自身.根)
        return 自身
