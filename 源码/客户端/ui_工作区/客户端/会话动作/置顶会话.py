'置顶：菜单一行和行尾一枚按钮。归档的行不提供置顶'
from ....模块.客户端.通告 import 取握手窗口
from ....ui_基础界面组件.提示泡 import 提示泡
from .派生 import 菜单项按钮,画图标,换上
from ..文案 import 中文

__all__=['置顶会话菜单项','置顶会话行按钮']

class 置顶会话菜单项:
    '菜单里的置顶或取消置顶。归档行不画'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#宿主属性
        自身.根=None#节点

    def 渲染(自身):
        '按当前是否置顶画出菜单项'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        会话号=属性['sessionId']#会话
        def 是否置顶(集):
            '这一行是否已置顶'
            return 会话号 in 集#成员
        def 是否归档(集):
            '这一行是否已归档'
            return 会话号 in 集#成员
        置顶=属性['usePinned'](是否置顶)#是否置顶
        归档=属性['useArchived'](是否归档)#是否归档
        if 归档:#归档不提供
            return 换上(自身,None)#不画
        打开对=属性['useMenuOpenState']()#打开状态
        def 点下():
            '关掉菜单再置顶或取消'
            打开对[1](False)#关掉
            if 置顶:#已置顶
                属性['unpinSession'](会话号)#取消
            else:#未置顶
                属性['pinSession'](会话号)#置顶
        名='pin-fill-16' if 置顶 else 'pin-outline-16'#图标
        文=中文['menu.unpinSession'] if 置顶 else 中文['menu.pinSession']#中文
        根=菜单项按钮(窗口,文,点下,画图标(窗口,名))#菜单项
        return 换上(自身,根)#节点

class 置顶会话行按钮:
    '行尾的置顶按钮。归档行不画'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#宿主属性
        自身.根=None#节点

    def 渲染(自身):
        '提示泡里放一枚图标按钮'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        文档=窗口.document#文档
        会话号=属性['sessionId']#会话
        def 是否置顶(集):
            '这一行是否已置顶'
            return 会话号 in 集#成员
        def 是否归档(集):
            '这一行是否已归档'
            return 会话号 in 集#成员
        置顶=属性['usePinned'](是否置顶)#是否置顶
        归档=属性['useArchived'](是否归档)#是否归档
        if 归档:#归档不提供
            return 换上(自身,None)#不画
        钮=文档.createElement('button')#按钮
        钮.type='button'#按钮
        钮.className='iconButton'#上游类名
        钮.setAttribute('aria-label',中文['menu.unpinSession'] if 置顶 else 中文['menu.pinSession'])#无障碍
        def 点击(事件):
            '置顶或取消'
            if 置顶:#已置顶
                属性['unpinSession'](会话号)#取消
            else:#未置顶
                属性['pinSession'](会话号)#置顶
        钮.addEventListener('click',点击)#点击
        图=画图标(窗口,'pin-fill-16' if 置顶 else 'pin-outline-16',14)#图标
        if 图 is not None:#有
            钮.appendChild(图)#放入
        泡=提示泡({
            'window':窗口,
            'label':中文['actions.unpin'] if 置顶 else 中文['actions.pin'],
            'side':'bottom',
            'align':'end',
            'delayMs':500,
            'portal':True,
            'children':钮,
        })#提示
        return 换上(自身,泡.渲染())#节点

def 置顶会话菜单项组件(属性):
    '渲染器按函数调用'
    return 置顶会话菜单项(属性).渲染()#节点

def 置顶会话行按钮组件(属性):
    '渲染器按函数调用'
    return 置顶会话行按钮(属性).渲染()#节点
