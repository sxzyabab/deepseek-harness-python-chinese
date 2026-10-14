from .上下文体 import 上下文体#按 form 选体
from .消息项 import 打开列

__all__=['上下文注入行']#仅中文公开名

from nicegui import ui as 界面

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

class 上下文注入行:
    '折叠披露'
    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.打开=False
        自身.体=上下文体()#体
        自身.根=None#列

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换(自身):
        '翻转开合'
        自身.打开=not 自身.打开#翻

    def 渲染(自身):
        '披露行'
        属性=自身.属性#props
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        出处=属性['provenance'] if 'provenance' in 属性 and 属性['provenance'] is not None else {}#出处
        形态=属性['form'] if 'form' in 属性 else None#form
        内容=属性['content'] if 'content' in 属性 else None#内容
        源=属性['source'] if 'source' in 属性 else None#源
        角色=出处['role'] if 'role' in 出处 else None#角色
        题键='message.contextRecall' if 角色=='recall' else 'message.contextInjection'#题
        标签=出处['label'] if 'label' in 出处 else None#标签
        def 点切换():
            '展开或收起注入正文。'
            自身.切换()
            自身.渲染()
        with 打开列(自身,'上下文注入行'):
            with 界面.row().classes('注入头'):
                界面.label(翻译(题键)).classes('标题')
                if 标签 is not None and not (isinstance(标签,str) and 标签==''):
                    界面.label(str(标签))
                界面.button(翻译('message.compaction.expand'),on_click=点切换)
            自身.体.更新({'content':内容,'source':源,'form':形态,'t':翻译,'open':自身.打开})
            自身.体.渲染()

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:
            自身.更新(属性)#刷
        自身.渲染()#画
