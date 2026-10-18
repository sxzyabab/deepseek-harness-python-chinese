from .文案 import 会话命名空间
from .读卡模型 import 读卡模型,读调用行
from .读取族表行 import 读族行
from .槽 import 槽名工具调用视图

__all__=['读行','读工具视图']

class 读行:
    '展开已完成的读取，并按调用起点打开路径'
    def __new__(类,属性):
        '交给读族行'
        return 读族行(属性,{
            'read':读卡模型(属性['block'],属性.get('cwd'),属性.get('home')),
            'filePathLine':读调用行(属性['block']),
        })

def 应用读工具视图(上下文,配置=None):
    '登记 read'
    def 登记():
        '写入按键视图槽'
        return 上下文.slots.register({
            'name':槽名工具调用视图,
            'key':'read',
            'locale':会话命名空间,
        },读行)
    上下文.slots.inject(槽名工具调用视图,登记)

读工具视图={
    'name':'read-toolview',
    'inject':['slots'],
    'apply':应用读工具视图,
}
