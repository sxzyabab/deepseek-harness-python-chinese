__all__=['Markdown委托提供方','读取Markdown委托']

当前=[{'openExternalLink':None,'openFile':None,'fileImages':None}]

class Markdown委托提供方:
    '包住一块 Markdown。里层替换外层的打开文件和打开外链'
    def __init__(自身,属性=None):
        '记下回调和子内容'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.已进=False

    def 渲染(自身):
        '进入时把委托压栈，子节点画在里面'
        属性=自身.属性
        if 自身.已进:
            当前.pop()
            自身.已进=False
        当前.append({
            'openExternalLink':属性.get('openExternalLink'),
            'openFile':属性.get('openFile'),
            'fileImages':属性.get('fileImages'),
        })
        自身.已进=True
        子=属性.get('children')
        if hasattr(子,'tagName'):
            自身.根=子
        return 子

    def 拆除(自身):
        '离开这块范围时弹出委托'
        if 自身.已进:
            当前.pop()
            自身.已进=False

def 读取Markdown委托():
    '最近一层委托。外面没有提供方时是空能力'
    return 当前[-1]
