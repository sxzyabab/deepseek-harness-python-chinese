from .目录浏览器 import 目录浏览器#应用内目录浏览器

__all__=['浏览目录流']#仅中文公开名

def 键齐(属性):#浏览流能否画
    'open、列举、创建、文案和两个回调都在才画'
    if not isinstance(属性,dict):#不是映射
        return False#缺
    if 'open' not in 属性:#没有打开旗
        return False#缺
    if not callable(属性.get('listDirectory')):#没有列举
        return False#缺
    if not callable(属性.get('createDirectory')):#没有创建
        return False#缺
    if not callable(属性.get('t')):#没有文案
        return False#缺
    if not callable(属性.get('onPicked')):#没有采纳
        return False#缺
    if not callable(属性.get('onCancel')):#没有取消
        return False#缺
    return True#齐

def 对话框属性(属性):#交给页内浏览器的 props
    '确认是选中路径，关掉是取消。不在这里登记工作区。'
    return {#对话框 props
        'open':属性['open'],#是否打开
        'busy':属性['busy'] if 'busy' in 属性 else False,#主人正在采纳
        'listDirectory':属性['listDirectory'],#列举
        'createDirectory':属性['createDirectory'],#创建
        't':属性['t'],#文案
        'onOpen':属性['onPicked'],#确认=选中
        'onClose':属性['onCancel'],#关掉=取消
    }#对话框结束

class 浏览目录流:#流占用者
    '把主人对话接到浏览器对话框；浏览失败留在对话框告警面，从不驱动 onError'
    def __init__(自身,属性):#按合成 props 构造
        '记下 props。槽位只调用构造，键齐才画。浏览器构造时不画。'
        自身.属性=属性 if isinstance(属性,dict) else {}#合成 props
        自身.浏览器=None#页内对话框
        if 键齐(自身.属性):#键齐
            自身.渲染()#末尾画一次

    def 更新(自身,属性):#props 变更
        '刷新主人对话与注入面。不在这里再画。'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新
        if 自身.浏览器 is not None and 键齐(自身.属性):#已有对话框
            自身.浏览器.更新(对话框属性(自身.属性))#同步

    def 渲染(自身):
        '画出目录浏览器。子组件构造时不画，这里画一次。关闭时浏览器自己收起。'
        if not 键齐(自身.属性):#键未齐
            return None#空槽留给主人
        面=对话框属性(自身.属性)#对话框 props
        if 自身.浏览器 is None:#初建
            自身.浏览器=目录浏览器(面)#构造不画
        return 自身.浏览器.渲染()#画一次

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 组件调用；画出对话框'
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()#对话框
