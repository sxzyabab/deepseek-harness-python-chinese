import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import 图标勾16,图标右chevron14,图标播放16
from ...ui_基础界面组件.markdown.代码块 import 代码块
from ...ui_基础界面组件.markdown.Markdown文本 import Markdown文本
from .文案 import 中文文案
from .原语文案 import 代码工具条文案,标记文案

__all__=['工具详情','详情项']

样式模块='dsh-tool-details'

def 确保样式(文档):
    '工具详情样式只插一次'
    注入模块样式文件(
        文档,
        'dsh-tool-details',
        os.path.join(os.path.dirname(__file__),'工具详情.module.css'),
        样式模块,
    )

def 元素(文档,标签,类名=None):
    '带样式模块的节点'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
        标样式模块(节点,样式模块)
    return 节点

class 详情项:
    '一条记录、回执或可折叠分组'
    def __new__(类,属性):
        '画出这一条'
        自身=object.__new__(类)
        自身.属性=属性
        return 自身.渲染()

    def 打开文件(自身,事件):
        '打开记录里的路径'
        位置=自身.属性['item'].get('location')
        打开=自身.属性.get('onOpenFile')
        if 位置 is None or 打开 is None:
            return
        if 'line' in 位置 and 位置['line'] is not None:
            打开(位置['path'],{'line':位置['line']})
        else:
            打开(位置['path'])

    def 渲染(自身):
        '标题、字段、正文、代码和分组'
        窗口=自身.属性['window']
        文档=窗口.document
        确保样式(文档)
        条目=自身.属性['item']
        根=元素(文档,'li','item')
        变更=条目.get('change')
        if isinstance(变更,dict) and 'value' in 变更:
            根.setAttribute('data-change',变更['value'])
        if 'title' in 条目:
            头=元素(文档,'div','heading')
            状态=条目.get('status')
            if isinstance(状态,dict):
                态=元素(文档,'span','status')
                态.setAttribute('role','img')
                if isinstance(变更,dict) and 'label' in 变更:
                    态.setAttribute('aria-label',变更['label'])
                else:
                    态.setAttribute('aria-label',状态.get('label') or '')
                if isinstance(变更,dict) and 变更.get('value')=='added':
                    态.textContent='+'
                elif isinstance(变更,dict) and 变更.get('value')=='removed':
                    态.textContent='−'
                elif 状态.get('value')=='completed':
                    态.appendChild(图标勾16({'window':窗口,'size':14}))
                elif 状态.get('value')=='in_progress':
                    态.appendChild(图标播放16({'window':窗口,'size':14}))
                else:
                    点=元素(文档,'span','pending')
                    态.appendChild(点)
                头.appendChild(态)
            位置=条目.get('location')
            打开=自身.属性.get('onOpenFile')
            if isinstance(位置,dict) and 打开 is not None:
                按钮=元素(文档,'button','path')
                按钮.type='button'
                按钮.textContent=条目['title']
                按钮.addEventListener('click',自身.打开文件)
                头.appendChild(按钮)
            else:
                文=元素(文档,'span','text')
                文.textContent=条目['title']
                头.appendChild(文)
            徽章=条目.get('badge')
            if isinstance(徽章,dict):
                标=元素(文档,'span','badge')
                if 'tone' in 徽章:
                    标.setAttribute('data-tone',徽章['tone'])
                标.textContent=徽章.get('label') or ''
                头.appendChild(标)
            if isinstance(状态,dict):
                态文=元素(文档,'span','statusText')
                if 'previousStatus' in 条目:
                    先前=元素(文档,'span','previous')
                    先前.textContent=条目['previousStatus']
                    态文.appendChild(先前)
                    箭头=文档.createTextNode(' → ')
                    态文.appendChild(箭头)
                现=文档.createElement('span')
                现.textContent=状态.get('label') or ''
                态文.appendChild(现)
                if isinstance(变更,dict) and 变更.get('value')=='updated' and 'previousStatus' not in 条目:
                    补=文档.createTextNode(' · '+变更.get('label',''))
                    态文.appendChild(补)
                头.appendChild(态文)
            根.appendChild(头)
        if 'subtitle' in 条目:
            副=元素(文档,'div','subtitle')
            副.textContent=条目['subtitle']
            根.appendChild(副)
        if 'description' in 条目:
            说明=元素(文档,'p','description')
            说明.textContent=条目['description']
            根.appendChild(说明)
        字段表=条目.get('fields') or []
        if len(字段表)>0:
            表=元素(文档,'dl','fields')
            for 字段 in 字段表:
                行=元素(文档,'div','field')
                名=文档.createElement('dt')
                名.textContent=字段['label']
                值=文档.createElement('dd')
                值.textContent=字段['value']
                行.appendChild(名)
                行.appendChild(值)
                表.appendChild(行)
            根.appendChild(表)
        if 'lines' in 条目:
            列表=元素(文档,'ul','lines')
            for 行文 in 条目['lines']:
                项=文档.createElement('li')
                项.textContent=行文
                列表.appendChild(项)
            根.appendChild(列表)
        if 'markdown' in 条目:
            散文=元素(文档,'div','prose')
            散文.appendChild(Markdown文本({
                'window':窗口,
                'text':条目['markdown'],
                'labels':标记文案(),
            }).渲染())
            根.appendChild(散文)
        if 'code' in 条目 and isinstance(条目['code'],dict):
            根.appendChild(代码块({
                'window':窗口,
                'toolbarLabels':代码工具条文案(),
                'className':'code',
                'code':条目['code'].get('text') or '',
                'lang':条目['code'].get('language'),
                'copyLabel':中文文案('copy'),
                'copiedLabel':中文文案('copied'),
            }).渲染())
        分组=条目.get('groups') or []
        序=0
        for 组 in 分组:
            盒=元素(文档,'details','group')
            要=文档.createElement('summary')
            要.appendChild(图标右chevron14({'window':窗口}))
            字=文档.createElement('span')
            字.textContent=组.get('label') or ''
            要.appendChild(字)
            盒.appendChild(要)
            列表=元素(文档,'ul','list')
            for 子 in 组.get('items') or []:
                列表.appendChild(详情项({
                    'window':窗口,
                    'item':子,
                    'onOpenFile':自身.属性.get('onOpenFile'),
                }))
            盒.appendChild(列表)
            根.appendChild(盒)
            序=序+1
        return 根

class 工具详情:
    '已记录字段和列表。空列表用空态文案'
    def __new__(类,属性):
        '画出详情体'
        自身=object.__new__(类)
        自身.属性=属性 if isinstance(属性,dict) else {}
        return 自身.渲染()

    def 渲染(自身):
        '标题说明、条目和未变化折叠'
        窗口=自身.属性['window']
        文档=窗口.document
        确保样式(文档)
        模型=自身.属性['model']
        根=元素(文档,'div','root')
        if 自身.属性.get('hasInspect') is True:
            根.setAttribute('data-inspect','')
        if 模型.get('caption') is not None:
            根.setAttribute('data-caption','')
            说明=元素(文档,'div','caption')
            说明.textContent=模型['caption']
            根.appendChild(说明)
        条目表=模型.get('items') or []
        if len(条目表)==0:
            空=元素(文档,'p','empty')
            空.textContent=模型.get('empty') or ''
            根.appendChild(空)
        else:
            列表=元素(文档,'ul','list')
            for 条目 in 条目表:
                列表.appendChild(详情项({
                    'window':窗口,
                    'item':条目,
                    'onOpenFile':自身.属性.get('onOpenFile'),
                }))
            根.appendChild(列表)
        未变=模型.get('unchanged')
        if isinstance(未变,dict):
            盒=元素(文档,'details','unchanged')
            要=文档.createElement('summary')
            要.appendChild(图标右chevron14({'window':窗口}))
            要.appendChild(文档.createTextNode(未变.get('label') or ''))
            盒.appendChild(要)
            列表=元素(文档,'ul','list')
            for 条目 in 未变.get('items') or []:
                列表.appendChild(详情项({
                    'window':窗口,
                    'item':条目,
                    'onOpenFile':自身.属性.get('onOpenFile'),
                }))
            盒.appendChild(列表)
            根.appendChild(盒)
        return 根
