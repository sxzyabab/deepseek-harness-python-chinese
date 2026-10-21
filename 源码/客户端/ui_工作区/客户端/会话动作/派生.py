'把一个可观察源投影成另一个。源快照身份没变时不重算'
from ....ui_基础界面组件.icons import 图标
from ....ui_基础界面组件.快捷键 import 快捷键

__all__=['派生','菜单项按钮','画图标','换上']

def 派生(源,投影):
    '订阅仍走源。读快照时，源身份变了才重新投影'
    见过=[None]#上次源快照
    值=[None]#上次投影
    def 取快照():
        '源没换身份就返回上次投影'
        快照=源.getSnapshot()#源快照
        if 值[0] is None or 快照 is not 见过[0]:#还没算或源换了
            见过[0]=快照#记下源
            值[0]=投影(快照)#重算
        return 值[0]#投影
    def 订阅(监听):
        '变更跟着源走'
        return 源.subscribe(监听)#退订
    return {'getSnapshot':取快照,'subscribe':订阅}#可观察源

def 菜单项按钮(窗口,文案,点下,图标节点=None,快捷=None,危险=False):
    '一行 role=menuitem。基础界面组件还没有菜单项按钮，这里按它的结构画'
    文档=窗口.document#文档
    绕=文档.createElement('div')#行外层
    绕.className='itemWrap'#上游类名
    if 危险:#危险行
        绕.className='itemWrap danger'#带危险
    钮=文档.createElement('button')#按钮
    钮.type='button'#按钮
    钮.setAttribute('role','menuitem')#菜单项
    钮.className='item danger' if 危险 else 'item'#上游类名
    if 快捷 is not None and isinstance(快捷,dict) and 快捷.get('aria'):#无障碍组合
        钮.setAttribute('aria-keyshortcuts',str(快捷['aria']))#快捷键
    def 点击(事件):
        '激活这一行'
        点下()#交给动作
    钮.addEventListener('click',点击)#点击
    if 图标节点 is not None:#有图标
        图盒=文档.createElement('span')#图标槽
        图盒.className='itemIcon'#上游类名
        图盒.appendChild(图标节点)#放入
        钮.appendChild(图盒)#挂上
    字=文档.createElement('span')#标签
    字.className='itemLabel'#上游类名
    字.textContent=文案#中文
    钮.appendChild(字)#挂上
    if 快捷 is not None and isinstance(快捷,dict) and 快捷.get('keys'):#键帽
        帽=快捷键({'window':窗口,'keys':快捷['keys'],'className':'shortcutKeys'})#键帽
        帽盒=文档.createElement('span')#键帽槽
        帽盒.setAttribute('aria-hidden','true')#装饰
        帽盒.className='shortcut'#上游类名
        帽节点=帽.渲染()#画出
        if 帽节点 is not None:#有
            帽盒.appendChild(帽节点)#放入
        钮.appendChild(帽盒)#挂上
    绕.appendChild(钮)#按钮
    return 绕#整行

def 画图标(窗口,名,尺寸=None):
    '按图标表画一枚。表里没有就返回 None'
    属性={'window':窗口}#窗口
    if 尺寸 is not None:#指定边长
        属性['size']=尺寸#边长
    return 图标(名,属性)#svg 或空

def 换上(组件,新根):
    '新节点先画好。旧节点留到同一次替换完成，中间不先拆空'
    旧=组件.根#上一份
    if 旧 is 新根:#还是这一份
        return 新根#节点
    if 新根 is not None and 旧 is not None and 旧.parentNode is not None:#还挂在页面上
        旧.parentNode.replaceChild(新根,旧)#一次换完
    elif 旧 is not None:#没有位置可换
        旧.remove()#拆掉
    组件.根=新根#记下
    return 新根#节点
