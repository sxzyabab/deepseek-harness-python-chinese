
__all__=['回车行为行','选项表']#仅中文公开名

选项表=(#忙碌 Enter 选项
    {'id':'queue','label':'settings.enter.queue'},#排队
    {'id':'steer','label':'settings.enter.steer'},#插话
)#选项结束

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 恒等选(值):
    """选择器原样返回偏好。"""
    return 值#原样

class 回车行为行:
    """忙碌态纯 Enter 行为选择器。"""
    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性#合成 props
        自身.打开=False#菜单开

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性#最新

    def 读行为(自身):
        """经 useBusyEnter。"""
        用=自身.属性['useBusyEnter'] if 'useBusyEnter' in 自身.属性 else None#选择器
        if 用 is not None:#有
            出=用(恒等选)#行为
            return 出 if 出 is not None else 'queue'#缺则排队
        钩=自身.属性['hooks'] if 'hooks' in 自身.属性 and 自身.属性['hooks'] is not None else {}#hooks
        存储=钩['busyEnter'] if 'busyEnter' in 钩 else None#存储
        if 存储 is not None:#有
            return 存储.getSnapshot()#行为
        return 'queue'#默认

    def 切换菜单(自身):
        """翻转开合。"""
        自身.打开=not 自身.打开#翻

    def 关菜单(自身):
        """关闭。"""
        自身.打开=False#关

    def 选择(自身,标识):
        """写入并关菜单。"""
        自身.打开=False#关
        设=自身.属性['setBusyEnter'] if 'setBusyEnter' in 自身.属性 else None#写入
        if 设 is not None:#有
            设(标识)#写

    def 渲染(自身):
        """标题、说明与选择器。"""
        翻译=自身.属性['t'] if 't' in 自身.属性 else 恒等翻译#文案
        行为=自身.读行为()#当前
        选中标签='settings.enter.queue' if 行为=='queue' else 'settings.enter.steer'#标签键
        return {#视图
            'type':'enter-behavior-row',#类型
            'title':翻译('settings.enter.title'),#标题
            'description':翻译('settings.enter.description'),#说明
            'open':自身.打开,#菜单
            'selectedId':行为,#选中
            'selectedLabel':翻译(选中标签),#选中文案
            'items':[{'id':项['id'],'label':翻译(项['label'])} for 项 in 选项表],#菜单项
            'onToggle':自身.切换菜单,#切换菜单
            'onClose':自身.关菜单,#关菜单
            'onSelect':自身.选择,#选择
            'cssModule':'回车行为行.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
