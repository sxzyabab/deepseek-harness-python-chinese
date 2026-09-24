__all__=['平台覆盖层']

class 平台覆盖层:
    """Desktop Platform 视口；原生子进程拥有远程内容与凭据。"""
    def __init__(自身,属性):
        """记下 props 并打开原生页。"""
        自身.属性=属性
        自身.尝试=0
        自身.状况='loading'
        自身.已关闭=False
        自身.打开()

    def 更新(自身,属性):
        """桥或目标页变了则重开。"""
        旧桥=自身.属性.get('bridge')
        旧页=自身.属性.get('page')
        自身.属性=属性
        if 属性.get('bridge') is not 旧桥 or 属性.get('page')!=旧页:
            自身.尝试+=1
            自身.打开()

    def 取边界(自身):
        """视口矩形；缺测量时给零。"""
        视口=自身.属性.get('viewportBounds')
        if 视口 is None:
            return {'x':0,'y':0,'width':0,'height':0}
        return 视口

    def 打开(自身):
        """打开原生页并订尺寸。"""
        自身.已关闭=False
        自身.状况='loading'
        桥=自身.属性['bridge']
        代=自身.尝试
        def 失败():
            """未拆除才标失败。"""
            if not 自身.已关闭 and 代==自身.尝试:
                自身.状况='failed'
        try:
            桥.open(自身.属性['page'],自身.取边界())
            if not 自身.已关闭 and 代==自身.尝试:
                自身.状况='loaded'
        except Exception:
            失败()

    def 设边界(自身):
        """原生视口随布局更新。"""
        if 自身.已关闭:
            return
        try:
            自身.属性['bridge'].setBounds(自身.取边界())
        except Exception:
            if not 自身.已关闭:
                自身.状况='failed'

    def 重试(自身):
        """同一目标页再加载。"""
        自身.尝试+=1
        自身.打开()

    def 拆除(自身):
        """还原 inert 并销毁原生文档。"""
        自身.已关闭=True
        try:
            自身.属性['bridge'].close()
        except Exception:
            return

    def 渲染(自身):
        """全窗覆盖层。"""
        return {
            'type':'platform-overlay',
            'cssModule':'平台覆盖层.module.css',
            'page':自身.属性['page'],
            'status':自身.状况,
            'backLabel':自身.属性['backLabel'],
            'loadingLabel':自身.属性['loadingLabel'],
            'failureLabel':自身.属性['failureLabel'],
            'retryLabel':自身.属性['retryLabel'],
            'onClose':自身.属性['onClose'],
            'onRetry':自身.重试,
            'onBounds':自身.设边界,
            'dispose':自身.拆除,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
