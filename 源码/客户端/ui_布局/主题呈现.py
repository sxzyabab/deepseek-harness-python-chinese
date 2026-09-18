import builtins#探测 document

__all__=['深色属性','主题源属性','内容字号变量','主题呈现器']#仅中文公开名

深色属性='data-ds-dark-theme'#深色调色板属性名
主题源属性='data-ds-theme-source'#主题源属性名
内容字号变量='--dsh-content-font-size'#内容字号 CSS 变量

class 主题呈现器:#文档主题呈现器
    """纯写入面；无 document 时只缓存快照。自有 theme-color meta。"""
    def __init__(自身):
        """记下已施加令牌名，预创建 theme-color meta。"""
        自身.已施加令牌=[]#收回集合
        自身.最近快照=None#最近快照
        自身.主题色元=None#自有 meta；有 DOM 时铸造
        try:#探测 DOM
            文档=builtins.document#浏览器 document
        except AttributeError:#无
            return#无 DOM 不铸 meta
        元=文档.createElement('meta')#铸造 meta
        元.name='theme-color'#标成 theme-color
        自身.主题色元=元#记下

    def 施加(自身,快照):
        """有 DOM 则写 color-scheme / 主题源 / 调色板 / 字号 / 令牌 / theme-color；否则只记快照。"""
        自身.最近快照=快照#缓存
        活动=快照['active'] if 快照 is not None and 'active' in 快照 else None#活动主题
        活动=活动 if 活动 is not None else {}#空则空表
        方案=活动['colorScheme'] if 'colorScheme' in 活动 else None#色方案
        令牌=活动['tokens'] if 'tokens' in 活动 and 活动['tokens'] is not None else {}#令牌表
        偏好=快照['preference'] if 快照 is not None and 'preference' in 快照 else None#偏好
        字号=快照['fontSize'] if 快照 is not None and 'fontSize' in 快照 else None#字号
        try:#探测 DOM
            文档=builtins.document#浏览器 document
        except AttributeError:#无
            文档=None#无 DOM
        if 文档 is None:#无浏览器
            自身.已施加令牌=list(令牌.keys())#仅记名
            return#结束
        根=文档.documentElement#根
        根.style.colorScheme=方案#根 color-scheme
        根.setAttribute(主题源属性,'system' if 偏好=='system' else 方案)#发布主题源
        体=文档.body#body
        if 方案=='dark':#深色
            体.setAttribute(深色属性,'')#打属性
        else:#浅色
            体.removeAttribute(深色属性)#摘属性
        if 字号 is not None:#有字号
            体.style.setProperty(内容字号变量,f'{字号}px')#写入内容字号轴
        for 名 in 自身.已施加令牌:#清上次
            体.style.removeProperty(名)#清变量
        自身.已施加令牌=[]#清空
        for 名,值 in 令牌.items():#写入
            体.style.setProperty(名,值)#设变量
            自身.已施加令牌.append(名)#记入
        if 自身.主题色元 is not None:#有自有 meta
            自身.主题色元.content=文档.defaultView.getComputedStyle(体).backgroundColor if hasattr(文档,'defaultView') and 文档.defaultView is not None else ''#跟计算背景
            if not 自身.主题色元.isConnected:#尚未挂上
                文档.head.append(自身.主题色元)#插入 head

    def 拆除(自身):
        """清根 color-scheme、主题源、调色板属性、字号轴、令牌与自有 meta。"""
        自身.最近快照=None#清快照
        try:#探测 DOM
            文档=builtins.document#浏览器 document
        except AttributeError:#无
            自身.已施加令牌=[]#清集合
            return#无 DOM
        根=文档.documentElement#根
        根.style.removeProperty('color-scheme')#清根 color-scheme
        根.removeAttribute(主题源属性)#清主题源
        体=文档.body#body
        体.removeAttribute(深色属性)#摘深色属性
        体.style.removeProperty(内容字号变量)#清内容字号轴
        for 名 in list(自身.已施加令牌):#清令牌
            体.style.removeProperty(名)#清变量
        自身.已施加令牌=[]#清集合
        if 自身.主题色元 is not None:#有自有 meta
            自身.主题色元.remove()#摘掉
