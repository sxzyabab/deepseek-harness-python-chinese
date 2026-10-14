from nicegui import ui as 界面

__all__=['吐司','保持毫秒','淡出毫秒']#仅中文公开名

保持毫秒=3000#全不透明保持
淡出毫秒=1000#淡出时长

样式已登记=False

def 登记样式():
    '同一段样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css('''
.吐司{position:fixed;top:40px;left:50%;z-index:1100;pointer-events:none;display:flex;align-items:center;gap:10px;width:max-content;max-width:min(640px,calc(100vw - 48px));padding:12px 16px;border-radius:var(--dsw-radius-lg);background:var(--dsw-alias-toast-bg);color:var(--dsw-alias-toast-label);font-size:14px;line-height:22px;box-shadow:var(--dsw-shadow-lv3);transform:translateX(-50%)}
''')
    样式已登记=True

class 吐司:#顶栏公告
    '滑入-保持-淡出；业主在 onDone 卸载'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 总时长(自身):
        '保持+淡出'
        return 保持毫秒+淡出毫秒#毫秒

    def 渲染(自身):
        '画出公告条，到时调用完成回调'
        登记样式()
        属性=自身.属性#props
        文=属性['text'] if 'text' in 属性 else ''#文案
        if 文 is None:#缺
            文=''#空
        图标=属性['icon'] if 'icon' in 属性 else None#图标
        完成=属性['onDone'] if 'onDone' in 属性 else None#完成
        行=界面.row().classes('吐司')#条
        with 行:#内容
            if isinstance(图标,str) and 图标!='':
                尾=图标.rsplit('-',1)[-1]#尺寸后缀
                图标名=图标.rsplit('-',1)[0] if 尾.isdigit() else 图标#去掉尺寸后缀
                界面.icon(图标名)#图
            界面.label(文)#文案
        if 完成 is not None:#到时卸载
            def 到期():
                '保持加淡出结束后通知业主'
                完成()#调用
            界面.timer((保持毫秒+淡出毫秒)/1000,到期,once=True)#定时

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
