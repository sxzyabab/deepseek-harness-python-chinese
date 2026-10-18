from .目录浏览器 import 目录浏览器#页内目录对话框

__all__=['浏览目录流']

class 浏览目录流:
    '把主人对话接到页内目录对话框。浏览失败留在对话框里，不调用 onError'
    def __init__(自身,属性):
        '记下主人对话和注入面。构造不画'
        自身.属性=属性#合成 props
        自身.浏览器=None#页内对话框

    def 更新(自身,属性):
        '换上最新的主人对话'
        自身.属性=属性#最新
        if 自身.浏览器 is not None:#已经造过
            自身.浏览器.更新(自身.对话框属性())#同步

    def 对话框属性(自身):
        '确认是选中路径，关掉是取消'
        属性=自身.属性#主人与注入
        return {#交给对话框
            'open':True if 属性.get('open') else False,#是否打开
            'busy':True if 属性.get('busy') else False,#主人正在采纳
            'listDirectory':属性.get('listDirectory'),#列举
            'createDirectory':属性.get('createDirectory'),#创建
            't':属性.get('t'),#文案绑定，显示不走它
            'onOpen':属性.get('onPicked'),#确认
            'onClose':属性.get('onCancel'),#取消
            'window':属性.get('window'),#窗口
        }#结束

    def 渲染(自身):
        '画出对话框。关掉时收起'
        面=自身.对话框属性()#对话框 props
        if 自身.浏览器 is None:#初建
            自身.浏览器=目录浏览器(面)#构造不画
        else:#已有
            自身.浏览器.更新(面)#同步
        return 自身.浏览器.渲染()#节点或空

    def 拆除(自身):
        '槽位卸下时作废在飞请求并拆掉对话框'
        if 自身.浏览器 is not None:#有对话框
            自身.浏览器.卸载()#拆掉
            自身.浏览器=None#丢掉
