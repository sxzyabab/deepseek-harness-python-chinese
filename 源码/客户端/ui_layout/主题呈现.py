"""全局主题 DOM 施加器：把已解析 ThemeSnapshot 投影到 document。

对齐上游 `ui-layout/src/client/theme-presenter.ts`。公开面仅中文名。
无 DOM 时仅记录快照，供宿主半对照。
"""

__all__=['深色属性','主题呈现器']#仅中文公开名

深色属性='data-ds-dark-theme'#深色调色板属性名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 主题呈现器:#文档主题呈现器
    """纯写入面；无 document 时只缓存快照。"""
    def __init__(自身):#构造
        """记下已施加令牌名。"""
        自身.已施加令牌=[]#收回集合
        自身.最近快照=None#最近快照

    def 施加(自身,快照):#把快照投影到 document
        """有 DOM 则写 color-scheme / 调色板 / 令牌；否则只记快照。"""
        自身.最近快照=快照#缓存
        活动=取字段(快照,'active') or {}#活动主题
        方案=取字段(活动,'colorScheme')#色方案
        令牌=取字段(活动,'tokens') or {}#令牌表
        try:#探测 DOM
            文档=__import__('builtins').__dict__.get('document')#浏览器 document
        except Exception:#无
            文档=None#无 DOM
        if 文档 is None:#无浏览器
            自身.已施加令牌=list(令牌.keys()) if isinstance(令牌,dict) else []#仅记名
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
        if isinstance(令牌,dict):#有令牌
            for 名,值 in 令牌.items():#写入
                体.style.setProperty(名,值)#设变量
                自身.已施加令牌.append(名)#记入

    def 拆除(自身):#收回写入
        """清根 color-scheme、调色板属性与令牌。"""
        自身.最近快照=None#清快照
        自身.已施加令牌=[]#清集合
