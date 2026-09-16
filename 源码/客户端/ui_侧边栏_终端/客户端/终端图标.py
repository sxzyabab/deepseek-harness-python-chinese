__all__=['终端图标','终端引导图标']#仅中文公开名

class 终端图标:#页签标题线条字形
    """十六像素装饰线条字形。"""
    def 视图(自身):#投影 svg
        """返回标题用终端图标。"""
        return {#svg
            'tag':'svg',#标签
            'width':'16',#宽
            'height':'16',#高
            'viewBox':'0 0 16 16',#视口
            'fill':'none',#无填充
            'aria-hidden':'true',#装饰
            'children':[{#路径
                'tag':'path',#路径
                'd':'m3 4 4 4-4 4M9 12h4',#折线
                'stroke':'currentColor',#描边
                'strokeWidth':'1.5',#宽
                'strokeLinecap':'round',#端点
                'strokeLinejoin':'round',#连接
            }],#子
        }#结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        return 自身.视图()#视图

class 终端引导图标:#开始页卡片字形
    """深色圆角终端卡片加白色提示符。"""
    def __init__(自身,属性=None):#记下尺寸与类名
        """记下画布尺寸与布局类。"""
        自身.属性=属性 if 属性 is not None else {}#合成 props

    def 更新(自身,属性):#props 变更
        """刷新合成 props。"""
        自身.属性=属性#最新

    def 视图(自身):#投影 svg
        """返回引导卡片图标。"""
        尺寸=自身.属性['size'] if 'size' in 自身.属性 else 26#默认 26
        类名=自身.属性['className'] if 'className' in 自身.属性 else None#布局类
        return {#svg
            'tag':'svg',#标签
            'width':尺寸,#宽
            'height':尺寸,#高
            'className':类名,#类
            'viewBox':'0 0 28 28',#视口
            'fill':'none',#无填充
            'aria-hidden':'true',#装饰
            'children':[{#底
                'tag':'rect',#矩形
                'x':'3','y':'5','width':'22','height':'19','rx':'3',#几何
                'fill':'#17191d',#底色
            },{#提示符
                'tag':'path',#路径
                'd':'m8 10 4 4-4 4M15 18h5',#折线
                'stroke':'#fff',#白
                'strokeWidth':'1.7',#宽
                'strokeLinecap':'round',#端点
                'strokeLinejoin':'round',#连接
            }],#子
        }#结束

    def __call__(自身,属性=None):#组件调用
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.视图()#视图
