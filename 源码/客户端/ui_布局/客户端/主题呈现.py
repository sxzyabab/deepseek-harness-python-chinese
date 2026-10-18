from ...模块.客户端.通告 import 取握手窗口

__all__=['深色属性','主题源属性','内容字号变量','主题呈现器']

深色属性='data-ds-dark-theme'#深色调色板
主题源属性='data-ds-theme-source'#light、dark 或 system
内容字号变量='--dsh-content-font-size'#正文字号

字号变量={
    'text':内容字号变量,
    'code':'--dsh-code-font-size',
    'terminal':'--dsh-terminal-font-size',
}#三个角色的字号变量
字体变量={
    'text':'--dsh-font-family-text',
    'code':'--dsh-font-family-code',
    'terminal':'--dsh-font-family-terminal',
}#三个角色的字体列表。空字符串表示用内置栈


class 主题呈现器:
    '把主题快照写到文档上。只收回自己写过的属性和那一个 theme-color'
    def __init__(自身):
        '先建好自有的 theme-color，等第一份快照再挂进 head'
        自身.已施加令牌=[]
        自身.窗口=取握手窗口()
        自身.主题色元=自身.窗口.document.createElement('meta')
        自身.主题色元.setAttribute('name','theme-color')

    def 施加(自身,快照):
        '写色板、字号、字体和令牌，再用算出的底色更新 theme-color'
        文档=自身.窗口.document
        方案=快照['active']['colorScheme']
        根=文档.documentElement
        根.style.setProperty('color-scheme',方案)
        if 快照['preference']=='system':
            源='system'
        else:
            源=方案
        根.setAttribute(主题源属性,源)
        体=文档.body
        if 方案=='dark':
            体.setAttribute(深色属性,'')
        else:
            体.removeAttribute(深色属性)
        字号表=快照['fontSizes']
        for 角色,变量名 in 字号变量.items():
            体.style.setProperty(变量名,str(字号表[角色])+'px')
        字体表=快照['fontFamilies']
        for 角色,变量名 in 字体变量.items():
            列表=字体表[角色]
            if 列表=='':
                体.style.removeProperty(变量名)
            else:
                体.style.setProperty(变量名,列表)
        for 名 in 自身.已施加令牌:
            体.style.removeProperty(名)
        自身.已施加令牌=[]
        for 名,值 in 快照['active']['tokens'].items():
            体.style.setProperty(名,值)
            自身.已施加令牌.append(名)
        计算=自身.窗口.getComputedStyle(体)
        自身.主题色元.setAttribute('content',计算.backgroundColor)
        if not 自身.主题色元.isConnected:
            文档.head.appendChild(自身.主题色元)

    def 拆除(自身):
        '收回色板、字号、字体、令牌和自有的 theme-color'
        文档=自身.窗口.document
        根=文档.documentElement
        根.style.removeProperty('color-scheme')
        根.removeAttribute(主题源属性)
        体=文档.body
        体.removeAttribute(深色属性)
        for 变量名 in 字号变量.values():
            体.style.removeProperty(变量名)
        for 变量名 in 字体变量.values():
            体.style.removeProperty(变量名)
        for 名 in 自身.已施加令牌:
            体.style.removeProperty(名)
        自身.已施加令牌=[]
        自身.主题色元.remove()
