import builtins#探测 document

__all__=['深色属性','主题呈现器']#仅中文公开名

深色属性='data-ds-dark-theme'#深色调色板属性名

class 主题呈现器:#文档主题呈现器
    """纯写入面；无 document 时只缓存快照。"""
    def __init__(自身):
        """记下已施加令牌名。"""
        自身.已施加令牌=[]#收回集合
        自身.最近快照=None#最近快照

    def 施加(自身,快照):
        """有 DOM 则写 color-scheme / 调色板 / 令牌；否则只记快照。"""
        自身.最近快照=快照#缓存
        活动=快照['active'] if 快照 is not None and 'active' in 快照 else None#活动主题
        活动=活动 if 活动 is not None else {}#空则空表
        方案=活动['colorScheme'] if 'colorScheme' in 活动 else None#色方案
        令牌=活动['tokens'] if 'tokens' in 活动 and 活动['tokens'] is not None else {}#令牌表
        try:#探测 DOM
            文档=builtins.document#浏览器 document
        except AttributeError:#无
            文档=None#无 DOM
        if 文档 is None:#无浏览器
            自身.已施加令牌=list(令牌.keys())#仅记名
            return#结束
        根=文档.documentElement#根
        根.style.colorScheme=方案#根 color-scheme
        体=文档.body#body
        if 方案=='dark':#深色
            体.setAttribute(深色属性,'')#打属性
        else:#浅色
            体.removeAttribute(深色属性)#摘属性
        for 名 in 自身.已施加令牌:#清上次
            体.style.removeProperty(名)#清变量
        自身.已施加令牌=[]#清空
        for 名,值 in 令牌.items():#写入
            体.style.setProperty(名,值)#设变量
            自身.已施加令牌.append(名)#记入

    def 拆除(自身):
        """清根 color-scheme、调色板属性与令牌。"""
        自身.最近快照=None#清快照
        自身.已施加令牌=[]#清集合
