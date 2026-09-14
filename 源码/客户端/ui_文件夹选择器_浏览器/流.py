from .目录浏览器 import 目录浏览器#应用内目录浏览器

__all__=['浏览目录流']#仅中文公开名

class 浏览目录流:#流占用者
    """把主人对话接到浏览器对话框；浏览失败留在对话框告警面，从不驱动 onError。"""
    def __init__(自身,属性):#按合成 props 构造
        """记下 props 并建造浏览器。"""
        自身.属性=属性#合成 props
        自身.浏览器=目录浏览器({#对话框 props
            'open':属性['open'],#是否打开
            'busy':属性['busy'],#主人正在采纳
            'listDirectory':属性['listDirectory'],#列举
            'createDirectory':属性['createDirectory'],#创建
            't':属性['t'],#文案
            'onOpen':属性['onPicked'],#确认=选中
            'onClose':属性['onCancel'],#关掉=取消
        })#浏览器结束

    def 更新(自身,属性):#props 变更
        """刷新主人对话与注入面。"""
        自身.属性=属性#最新
        自身.浏览器.更新({#同步对话框
            'open':属性['open'],#打开
            'busy':属性['busy'],#忙碌
            'listDirectory':属性['listDirectory'],#列举
            'createDirectory':属性['createDirectory'],#创建
            't':属性['t'],#文案
            'onOpen':属性['onPicked'],#确认
            'onClose':属性['onCancel'],#取消
        })#更新结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用；返回对话框视图。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.浏览器()#对话框视图
