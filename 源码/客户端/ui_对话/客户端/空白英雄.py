"""空白草稿阶段英雄铬：鱼标标题、辉光与工作区芯片。

对齐上游 `ui-conversation/src/client/skeleton/EmptyHero.tsx`。公开面仅中文名。
属性为 dict。
"""

__all__=['工作区标签','工作区芯片','英雄辉光','英雄壳']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 工作区标签(工作目录):
    """分隔符-only 路径回显原 cwd。"""
    if 工作目录 is None or 工作目录=='':#空
        return 工作目录#原样
    段=工作目录.replace('\\','/').rstrip('/').split('/')#分段
    基=段[-1] if len(段)>0 else ''#末段
    return 基 if 基!='' else 工作目录#空则原路径

class 工作区芯片:
    """无标签时占位「选择工作区」。"""

    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """始终可点。"""
        属性=自身.属性#props
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        标签=属性['label'] if 'label' in 属性 else None#标签
        菜单开=属性['menuOpen'] is True if 'menuOpen' in 属性 else False#展开
        点击=属性['onClick'] if 'onClick' in 属性 else None#点击
        return {#芯片
            'className':'workspace',#类
            'aria-label':翻译('hero.chooseWorkspace'),#aria
            'aria-haspopup':'menu',#菜单
            'aria-expanded':菜单开,#展开
            'onClick':点击,#点击
            'folder':'closed' if 标签 is None else 'open',#文件夹态
            'label':标签 if 标签 is not None else 翻译('hero.chooseWorkspace'),#文案
            'chevron':True,#下箭头
        }#结束芯片

class 英雄辉光:
    """属主 className 供位；滤镜 id 防碰撞。"""

    def __init__(自身,类名=None,滤镜标识=None):
        """记下定位类与滤镜 id。"""
        自身.类名=类名#定位
        自身.滤镜标识=滤镜标识 if 滤镜标识 not in (None,'') else 'empty-glow'#滤镜

    def 渲染(自身):
        """1051×468 椭圆，opacity 0.08。"""
        return {#辉光
            'className':自身.类名,#定位类
            'viewBox':'0 0 1051 468',#视口
            'aria-hidden':True,#装饰
            'filterId':自身.滤镜标识,#滤镜
            'ellipse':{'cx':525.5,'cy':234,'rx':425.5,'ry':134,'fill':'#6187D8','fillOpacity':0.08},#椭圆
            'blur':50,#高斯模糊
        }#结束辉光

class 英雄壳:
    """无辉光、无 composer、无工作区行。"""

    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """鱼标+标题+预览徽。"""
        属性=自身.属性#props
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        子=属性['children'] if 'children' in 属性 else None#覆盖层
        return {#壳
            'className':'root',#根
            'stack':{#栈
                'className':'stack',#类
                'headline':{#标题行
                    'className':'headline',#类
                    'fish':{'size':34,'className':'fish'},#鱼标
                    'text':翻译('hero.headline'),#标题
                    'badge':翻译('hero.preview'),#预览徽
                },#结束标题
                'body':{'className':'body'},#空 body 位
            },#结束栈
            'children':子,#覆盖层
        }#结束壳
