import importlib.resources as 包资源
import re
from nicegui import ui as 界面

__all__=['平台覆盖层']

def _读样式():
    '读同目录样式并给类名加前缀。失败时异常文案只有样式读不到，不含路径'
    try:
        原文=包资源.files(__package__).joinpath('平台覆盖层.module.css').read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None
    原文=re.sub(r':global\(([^)]*)\)', r'\1', 原文)
    for 名 in ('trafficLights','controls','overlay','viewport','failure','spinner','header','status','retry','back'):
        原文=原文.replace('.'+名,'.platform-'+名)
    return 原文

界面.add_css(_读样式(),shared=True)

class 平台覆盖层:
    'Desktop Platform 视口；原生子进程拥有远程内容与凭据'
    def __init__(自身,属性):
        '记下 props 并打开原生页。父分区会调用，构造时不画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.尝试=0
        自身.状况='loading'
        自身.已关闭=False
        自身.打开()

    def 更新(自身,属性):
        '桥或目标页变了则重开'
        旧桥=自身.属性.get('bridge')
        旧页=自身.属性.get('page')
        自身.属性=属性
        if 属性.get('bridge') is not 旧桥 or 属性.get('page')!=旧页:
            自身.尝试+=1
            自身.打开()

    def 取边界(自身):
        '视口矩形；缺测量时给零'
        视口=自身.属性.get('viewportBounds')
        if 视口 is None:
            return {'x':0,'y':0,'width':0,'height':0}
        return 视口

    def 打开(自身):
        '打开原生页并订尺寸'
        自身.已关闭=False
        自身.状况='loading'
        桥=自身.属性['bridge']
        代=自身.尝试
        def 失败():
            '未拆除才标失败'
            if not 自身.已关闭 and 代==自身.尝试:
                自身.状况='failed'
        try:
            桥.open(自身.属性['page'],自身.取边界())
            if not 自身.已关闭 and 代==自身.尝试:
                自身.状况='loaded'
        except Exception:
            失败()

    def 设边界(自身):
        '原生视口随布局更新'
        if 自身.已关闭:
            return
        try:
            自身.属性['bridge'].setBounds(自身.取边界())
        except Exception:
            if not 自身.已关闭:
                自身.状况='failed'

    def 重试(自身):
        '同一目标页再加载'
        自身.尝试+=1
        自身.打开()

    def 拆除(自身):
        '还原 inert 并销毁原生文档；关闭失败交给调用方显示'
        自身.已关闭=True
        自身.属性['bridge'].close()

    def 渲染(自身):
        '画出全窗覆盖层'
        自身.设边界()
        with 界面.column().classes('platform-overlay'):
            with 界面.row().classes('platform-header'):
                with 界面.row().classes('platform-controls'):
                    界面.html('<span class="platform-trafficLights"></span>',sanitize=False)
                    界面.button(自身.属性['backLabel'], on_click=自身.属性['onClose']).props('flat no-caps').classes('platform-back')
            with 界面.column().classes('platform-viewport'):
                界面.label(自身.属性['page'])
                if 自身.状况=='loading':
                    with 界面.column().classes('platform-status'):
                        界面.html('<div class="platform-spinner"></div>',sanitize=False)
                        界面.label(自身.属性['loadingLabel'])
                elif 自身.状况=='failed':
                    with 界面.column().classes('platform-status'):
                        界面.label(自身.属性['failureLabel']).classes('platform-failure')
                        界面.button(自身.属性['retryLabel'], on_click=自身.重试).props('flat no-caps').classes('platform-retry')

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
