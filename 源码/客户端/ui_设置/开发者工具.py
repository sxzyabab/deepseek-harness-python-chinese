from ...存储 import 创建快照存储#本地开关仓

__all__=['开发者工具偏好']

class 开发者工具偏好:
    """一份已接受偏好驱动全部开发者工具消费方。"""
    def __init__(自身,作用域):
        """memory 用本地仓；host 跟表单已接受值，缺席为关。"""
        自身.作用域=作用域#配置表单
        自身.本地=创建快照存储(True)#浏览器本地默认开
        if 作用域.getSnapshot()['mode']=='memory':#进程内
            自身.enabled=自身.本地#本地可观察
            return
        def 取已启用():
            """已接受节的 enabled，尚未接受则关。"""
            值=作用域.getSnapshot()['value']#已接受节
            if 值 is None:#尚未接受
                return False#关
            return 值['enabled'] if 'enabled' in 值 else False#字段
        先前=[取已启用()]#上次扇出
        def 订阅(监听):
            """值变才转发给监听。"""
            def 转发():
                """比较后通知。"""
                下一=取已启用()#现态
                if 下一==先前[0]:#未变
                    return
                先前[0]=下一#记下
                监听()#通知
            return 作用域.subscribe(转发)#订表单
        自身.enabled={'getSnapshot':取已启用,'subscribe':订阅}#可观察

    def 设已启用(自身,已启用):
        """memory 写本地仓；host 有序写入，拒绝则抛。"""
        if 自身.作用域.getSnapshot()['mode']=='memory':#本地
            自身.本地.set(已启用)#写仓
            return
        if 自身.作用域.set('enabled',已启用) is not True:#宿主拒绝
            raise RuntimeError('开发者工具偏好未保存')
