from .文案 import 会话命名空间
from .图像卡片模型 import 图像卡模型
from .读取族表行 import 读族行
from .槽 import 槽名工具调用视图,槽名工具调用图片

__all__=['读图像行','读图像工具视图']

class 读图像行:
    '读族行加上耐久图像。图库走 tool.call.images'
    def __new__(类,属性):
        '把图像卡交给读族行'
        return 读族行(属性,{
            'image':图像卡模型(属性['block']),
            'renderSlot':属性.get('renderSlot'),
            'loadImage':属性.get('loadImage'),
        })

def 应用读图像工具视图(上下文,配置=None):
    '登记 read_image，并声明图像子槽'
    def 登记():
        '写入按键视图槽'
        return 上下文.slots.register({
            'name':槽名工具调用视图,
            'key':'read_image',
            'locale':会话命名空间,
            'children':{槽名工具调用图片:{'kind':'single','scope':'session'}},
        },读图像行)
    上下文.slots.inject(槽名工具调用视图,登记)

读图像工具视图={
    'name':'read-image-toolview',
    'inject':['slots'],
    'apply':应用读图像工具视图,
}
