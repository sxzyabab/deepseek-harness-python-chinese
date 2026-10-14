from nicegui import ui as 界面

__all__=['终端图标','终端引导图标']

class 终端图标:
    '十六像素装饰线条字形'
    def 视图(自身):
        '返回标题用终端图标'
        return {
            'tag':'svg',
            'width':'16',
            'height':'16',
            'viewBox':'0 0 16 16',
            'fill':'none',
            'aria-hidden':'true',
            'children':[{
                'tag':'path',
                'd':'m3 4 4 4-4 4M9 12h4',
                'stroke':'currentColor',
                'strokeWidth':'1.5',
                'strokeLinecap':'round',
                'strokeLinejoin':'round',
            }],
        }

    def 渲染(自身):
        '画出十六像素终端折线'
        界面.html(
            '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">'
            '<path d="M3 4L7 8L3 12" stroke="currentColor"/>'
            '<path d="M9 12H13" stroke="currentColor"/>'
            '</svg>',
            sanitize=False,
        )

    def __call__(自身,属性=None):
        '画出当前图标'
        return 自身.渲染()

class 终端引导图标:
    '深色圆角终端卡片加白色提示符'
    def __init__(自身,属性=None):
        '记下画布尺寸与布局类。父组件调用渲染，构造时不画'
        自身.属性=属性 if 属性 is not None else {}

    def 更新(自身,属性):
        '刷新尺寸与类名'
        自身.属性=属性

    def 视图(自身):
        '返回引导卡片图标'
        尺寸=自身.属性['size'] if 'size' in 自身.属性 else 26
        类名=自身.属性['className'] if 'className' in 自身.属性 else None
        return {
            'tag':'svg',
            'width':尺寸,
            'height':尺寸,
            'className':类名,
            'viewBox':'0 0 28 28',
            'fill':'none',
            'aria-hidden':'true',
            'children':[{
                'tag':'rect',
                'x':'3','y':'5','width':'22','height':'19','rx':'3',
                'fill':'#17191d',
            },{
                'tag':'path',
                'd':'m8 10 4 4-4 4M15 18h5',
                'stroke':'#fff',
                'strokeWidth':'1.7',
                'strokeLinecap':'round',
                'strokeLinejoin':'round',
            }],
        }

    def 渲染(自身):
        '画出引导卡片字形'
        尺寸=自身.属性['size'] if 'size' in 自身.属性 else 26
        宽=尺寸 if isinstance(尺寸,int) else 26
        界面.html(
            '<svg width="'+str(宽)+'" height="'+str(宽)+'" viewBox="0 0 28 28" fill="none" aria-hidden="true">'
            '<rect x="3" y="5" width="22" height="19" rx="3" fill="#17191d"/>'
            '<path d="m8 10 4 4-4 4M15 18h5" stroke="#fff" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>'
            '</svg>',
            sanitize=False,
        )

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
