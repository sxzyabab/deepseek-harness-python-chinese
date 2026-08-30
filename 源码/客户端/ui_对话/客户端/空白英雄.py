"""空白草稿阶段英雄铬：鱼标标题、辉光与工作区芯片。

对齐上游 `ui-conversation/src/client/skeleton/EmptyHero.tsx`。公开面仅中文名。
"""

__all__=['工作区标签','工作区芯片','英雄辉光','英雄壳']#仅中文公开名

def 工作区标签(工作目录):#芯片 basename
    """分隔符-only 路径回显原 cwd。"""
    if not 工作目录:#空
        return 工作目录#原样
    段=工作目录.replace('\\','/').rstrip('/').split('/')#分段
    基=段[-1] if 段 else ''#末段
    return 基 if 基!='' else 工作目录#空则原路径

class 工作区芯片:#文件夹+标签+chevron
    """无标签时占位「选择工作区」。"""

    def __init__(自身,属性=None):#记下 props
        """记下合成 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """始终可点。"""
        属性=自身.属性#props
        翻译=属性.get('t',lambda 键,**_:键)#文案
        标签=属性.get('label')#标签
        菜单开=属性.get('menuOpen',False)#展开
        return {#芯片
            'className':'workspace',#类
            'aria-label':翻译('hero.chooseWorkspace'),#aria
            'aria-haspopup':'menu',#菜单
            'aria-expanded':菜单开,#展开
            'onClick':属性.get('onClick'),#点击
            'folder':'closed' if 标签 is None else 'open',#文件夹态
            'label':标签 if 标签 is not None else 翻译('hero.chooseWorkspace'),#文案
            'chevron':True,#下箭头
        }#结束芯片

class 英雄辉光:#柔蓝椭圆背光
    """属主 className 供位；滤镜 id 防碰撞。"""

    def __init__(自身,类名=None,滤镜标识=None):#记下
        """记下定位类与滤镜 id。"""
        自身.类名=类名#定位
        自身.滤镜标识=滤镜标识 or 'empty-glow'#滤镜

    def 渲染(自身):#SVG 结构
        """1051×468 椭圆，opacity 0.08。"""
        return {#辉光
            'className':自身.类名,#定位类
            'viewBox':'0 0 1051 468',#视口
            'aria-hidden':True,#装饰
            'filterId':自身.滤镜标识,#滤镜
            'ellipse':{'cx':525.5,'cy':234,'rx':425.5,'ry':134,'fill':'#6187D8','fillOpacity':0.08},#椭圆
            'blur':50,#高斯模糊
        }#结束辉光

class 英雄壳:#仅标题行
    """无辉光、无 composer、无工作区行。"""

    def __init__(自身,属性=None):#记下 props
        """记下合成 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """鱼标+标题+预览徽。"""
        属性=自身.属性#props
        翻译=属性.get('t',lambda 键,**_:键)#文案
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
            'children':属性.get('children'),#覆盖层
        }#结束壳
