'撰写器上的模型座位。根菜单再钻进模型列表或推理等级'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import (
    常规描边,
    描边图标,
    图标下箭头描边常规,
    图标勾描边常规,
)
from ...ui_基础界面组件.吐司 import 处理吐司
from ...ui_基础界面组件.状态点 import 处理状态点
from ...ui_基础界面组件.输入 import 处理输入
from ...ui_基础界面组件.菜单组 import 菜单组,观察粘性菜单组
from ...ui_基础界面组件.菜单表面 import 菜单表面
from ...ui_基础界面组件.按名排序 import 按名排序
from .提供方顺序 import 排列模型提供方

__all__=['模型选择','渲染模型选择','数据图标']

样式模块='model-select'
序号=0
座位缓存={}

def 数据图标(属性=None):
    '常规数据字形。命令和触发器各用一次'
    图=描边图标(属性,'0 0 16 16',[
        {'d':'M7.8667 0.349609C8.96906 0.349634 10.0601 0.481272 11.0317 0.735352C11.9973 0.987845 12.8453 1.362 13.4644 1.84766C14.0744 2.32629 14.507 2.95539 14.5161 3.69336H14.5171V8.53516C14.0843 8.32076 13.6108 8.17679 13.1108 8.11816C13.1831 7.96848 13.2162 7.82856 13.2163 7.70312V5.76758C12.6269 6.16618 11.8739 6.47995 11.0317 6.7002C10.0602 6.95423 8.96896 7.08494 7.8667 7.08496C6.76461 7.08493 5.67411 6.95415 4.70264 6.7002C3.85994 6.48006 3.10694 6.1662 2.51709 5.76758V7.70312L2.521 7.78418C2.56374 8.19554 2.93361 8.74414 3.91357 9.23145C4.9281 9.73585 6.35004 10.0371 7.8667 10.0371C8.26373 10.0371 8.6543 10.0141 9.03271 9.97461C8.75596 10.3799 8.54664 10.8349 8.42041 11.3232C8.23666 11.3313 8.0518 11.3369 7.8667 11.3369C6.20108 11.3369 4.57025 11.01 3.33447 10.3955C3.04163 10.2499 2.76658 10.0836 2.51709 9.90039V11.6738C2.51728 12.1379 2.88589 12.7556 3.92236 13.292C4.93457 13.8157 6.35342 14.1289 7.8667 14.1289C8.12318 14.1289 8.37694 14.1161 8.62646 14.0986C8.82021 14.5535 9.08999 14.9682 9.41943 15.3271C8.91285 15.3934 8.39149 15.4287 7.8667 15.4287C6.19761 15.4287 4.56379 15.0869 3.32568 14.4463C2.11244 13.8185 1.21649 12.8562 1.21631 11.6738V3.76367C1.21595 3.74853 1.21438 3.733 1.21436 3.71777C1.21436 2.96917 1.65103 2.33053 2.26807 1.84668C2.88747 1.36112 3.73675 0.987685 4.70264 0.735352C5.67413 0.481376 6.76457 0.349636 7.8667 0.349609ZM7.8667 1.65039C6.86269 1.65042 5.88326 1.77028 5.03076 1.99316C4.17183 2.2176 3.50421 2.52956 3.06982 2.87012C2.65043 3.19909 2.52622 3.48898 2.51709 3.69336V3.74414C2.52719 3.94845 2.65185 4.23772 3.06982 4.56543C3.50425 4.90601 4.17172 5.21795 5.03076 5.44238C5.88326 5.66527 6.8627 5.78513 7.8667 5.78516C8.8707 5.78513 9.85015 5.66525 10.7026 5.44238C11.5611 5.21787 12.2286 4.9049 12.6626 4.56445C13.0982 4.22252 13.2163 3.9231 13.2163 3.71777L13.2104 3.63574C13.1818 3.43623 13.044 3.16941 12.6626 2.87012C12.2286 2.52957 11.5614 2.21773 10.7026 1.99316C9.85009 1.77025 8.8708 1.65041 7.8667 1.65039Z','fill':'currentColor'},
        {'d':'M12.8936 10.0361L13.2061 10.5566C13.2296 10.5959 13.2651 10.6562 13.3027 10.707C13.3469 10.7666 13.4148 10.8431 13.5195 10.9023C13.6244 10.9617 13.725 10.9801 13.7988 10.9873C13.8619 10.9934 13.9318 10.9932 13.9775 10.9932H14.6162L14.8896 11.4502L14.5947 11.9443C14.5698 11.9859 14.5312 12.0483 14.5029 12.1084C14.4781 12.1611 14.4514 12.2312 14.4395 12.3164L14.4326 12.4072L14.4395 12.4971C14.4514 12.5825 14.4781 12.6532 14.5029 12.7061C14.5312 12.7661 14.5689 12.8287 14.5938 12.8701L14.8896 13.3633L14.6162 13.8213H13.9775C13.9318 13.8213 13.8619 13.821 13.7988 13.8271C13.7433 13.8326 13.6728 13.8442 13.5967 13.875L13.5195 13.9121C13.4148 13.9714 13.3469 14.0478 13.3027 14.1074C13.265 14.1583 13.2296 14.2186 13.2061 14.2578L12.8936 14.7783H12.3115L11.999 14.2578C11.9755 14.2186 11.9401 14.1583 11.9023 14.1074C11.8693 14.0628 11.823 14.0083 11.7578 13.959L11.6855 13.9121L11.6074 13.875C11.5316 13.8445 11.4615 13.8325 11.4062 13.8271C11.3432 13.821 11.2733 13.8213 11.2275 13.8213H10.5889L10.3135 13.3633L10.6104 12.8701C10.6352 12.8287 10.6739 12.7661 10.7021 12.7061C10.7352 12.6357 10.7724 12.534 10.7725 12.4072C10.7724 12.2804 10.7352 12.1788 10.7021 12.1084C10.6739 12.0483 10.6353 11.9859 10.6104 11.9443L10.3135 11.4502L10.5889 10.9932H11.2275C11.2733 10.9932 11.3432 10.9934 11.4062 10.9873C11.4801 10.9801 11.5808 10.9616 11.6855 10.9023C11.7903 10.843 11.8582 10.7666 11.9023 10.707C11.94 10.6562 11.9755 10.5959 11.999 10.5566L12.3115 10.0361H12.8936Z','stroke':'currentColor'},
    ],16,常规描边)
    路=图.querySelectorAll('path')
    if isinstance(路,list) and len(路)>1:
        路[1].setAttribute('stroke-miterlimit','10')
    return 图

def 右箭头图标(属性=None):
    '常规一像素右箭头'
    return 描边图标(属性,'0 0 16 16',[
        'M6 12L9.29289 8.70711C9.68342 8.31658 9.68342 7.68342 9.29289 7.29289L6 4',
    ],14,常规描边)

def 拼类(*段):
    '拼出非空的 class'
    出=[]
    for 段名 in 段:
        if isinstance(段名,str) and 段名!='':
            出.append(段名)
    return ' '.join(出)

def 建(文档,标签,类名=None):
    '造一个挂了本页样式模块的节点'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    return 标样式模块(节点,样式模块)

def 渲染模型选择(属性):
    '同一份目录存储复用座位，把根节点交回槽位'
    目录=属性.get('directory') if isinstance(属性,dict) else None
    键=id(目录)
    已有=座位缓存.get(键)
    if 已有 is None:
        已有=模型选择(属性)
        座位缓存[键]=已有
    else:
        已有.更新(属性)
    return 已有.根

class 模型选择:
    '撰写器模型座位：触发器，以及模型 / 推理等级两级菜单'
    def __init__(自身,属性):
        '记下 props，画出触发器，并订阅这份目录'
        global 序号
        序号=序号+1
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.标识='dsh-model-'+str(序号)
        自身.打开=False
        自身.面板='root'
        自身.查询=''
        自身.高亮下标=None
        自身.选定焦点=False
        自身.上次动作='load'
        自身.吐司=None
        自身.吐司序号=0
        自身.吐司已画=None
        自身.吐司节点=None
        自身.面板焦点=None
        自身.上次显示搜索=False
        自身.根=None
        自身.触发=None
        自身.搜索框=None
        自身.菜单=None
        自身.菜单面=None
        自身.分组视口=None
        自身.行引用=[]
        自身.粘性拆除=None
        自身.已听滚动=False
        自身.已听点外=False
        自身.绘制中=False
        自身.待重画=False
        自身.退订=None
        自身.渲染()
        目录=自身.属性.get('directory')
        if 目录 is not None:
            自身.退订=目录.subscribe(自身.目录变了)

    def 更新(自身,属性):
        '换成这一次的 props 并重画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if 自身.退订 is None and 自身.属性.get('directory') is not None:
            自身.退订=自身.属性['directory'].subscribe(自身.目录变了)
        自身.渲染()

    def 窗口(自身):
        '宿主窗口。props 没给就用当前页'
        if 'window' in 自身.属性 and 自身.属性['window'] is not None:
            return 自身.属性['window']
        return 取握手窗口()

    def 读状态(自身):
        '目录存储的当前快照'
        return 自身.属性['directory'].getSnapshot()

    def 目录变了(自身):
        '目录快照变了就重画。绘制中则记一笔，画完再来'
        if 自身.绘制中:
            自身.待重画=True
            return
        if 自身.根 is not None and 自身.根.parentNode is None and 自身.退订 is not None:
            退=自身.退订
            自身.退订=None
            退()
            return
        自身.渲染()

    def 派生(自身,状态):
        '由目录快照算出当前模型、力度、搜索结果'
        分组=排列模型提供方(list(状态.get('groups') or []))
        选择=[]
        for 组 in 分组:
            for 模型 in 组.get('models') or []:
                选定={'provider':组['id'],'model':模型['id']}
                推理=模型.get('reasoning')
                if isinstance(推理,dict) and 推理.get('defaultEffort') is not None:
                    选定['reasoningEffort']=推理['defaultEffort']
                选择.append({'group':组,'model':模型,'selection':选定})
        显示搜索=len(选择)>4
        查询文本='' if 显示搜索 is not True else 自身.查询.strip()
        过滤=[]
        for 组 in 分组:
            模型列=按名排序(list(组.get('models') or []),查询文本)
            if len(模型列)>0:
                拷=dict(组)
                拷['models']=模型列
                过滤.append(拷)
        可见=[]
        for 组 in 过滤:
            for 模型 in 组['models']:
                可见.append({'provider':组['id'],'model':模型['id']})
        当前=状态.get('current')
        当前可见=-1
        序=0
        for 项 in 可见:
            if 当前 is not None and 项['provider']==当前.get('provider') and 项['model']==当前.get('model'):
                当前可见=序
                break
            序+=1
        if len(可见)==0:
            活跃=-1
        else:
            if 自身.高亮下标 is None:
                基准=0 if 当前可见<0 else 当前可见
            else:
                基准=自身.高亮下标
            上限=len(可见)-1
            活跃=上限 if 基准>上限 else 基准
        选中下标=-1
        if 当前 is not None:
            序=0
            for 项 in 选择:
                选=项['selection']
                if 选['provider']==当前.get('provider') and 选['model']==当前.get('model'):
                    选中下标=序
                    break
                序+=1
        当前选择=None if 选中下标<0 else 选择[选中下标]
        推理=None if 当前选择 is None else 当前选择['model'].get('reasoning')
        if not isinstance(推理,dict):
            推理=None
        有效力度=None
        if 当前 is not None and 当前.get('reasoningEffort') is not None:
            有效力度=当前['reasoningEffort']
        elif 推理 is not None:
            有效力度=推理.get('defaultEffort')
        if 当前选择 is None:
            力度文=None
        elif 推理 is None:
            力度文=状态.get('retainedEffort')
        elif 有效力度 is None:
            力度文='Default'
        else:
            力度文=有效力度
            for 级 in 推理.get('efforts') or []:
                if 级.get('id')==有效力度:
                    力度文=级.get('name')
                    break
        力度选项=[]
        if 推理 is not None:
            if 推理.get('defaultEffort') is None:
                力度选项.append({'key':'provider-default','effort':None,'label':'Default'})
            for 级 in 推理.get('efforts') or []:
                力度选项.append({
                    'key':'effort:'+str(级.get('id')),
                    'effort':级.get('id'),
                    'label':级.get('name'),
                })
        忙=状态.get('pending') is not None
        等待=当前选择 is None and 状态.get('status')=='loading'
        if 等待:
            模型文='正在加载模型…'
        elif 当前选择 is not None:
            模型文=当前选择['model'].get('name')
        else:
            模型文='请选择模型'
        if 等待:
            触发读法='正在加载模型…'
        elif 当前选择 is None:
            触发读法='请选择模型'
        elif 力度文 is None:
            触发读法='选择模型，当前 '+str(模型文)
        else:
            触发读法='选择模型，当前 '+str(模型文)+'，推理等级 '+str(力度文)
        if 力度文 is None:
            触发文=模型文
        else:
            触发文=str(模型文)+' · '+str(力度文)
        return {
            '选择':选择,
            '显示搜索':显示搜索,
            '过滤':过滤,
            '可见':可见,
            '活跃':活跃,
            '当前选择':当前选择,
            '推理':推理,
            '有效力度':有效力度,
            '力度文':力度文,
            '力度选项':力度选项,
            '忙':忙,
            '模型文':模型文,
            '触发文':触发文,
            '触发读法':触发读法,
        }

    def 重载(自身):
        '把最近一次动作记成加载，再拉目录'
        自身.上次动作='load'
        加载=自身.属性.get('load')
        if 加载 is not None:
            加载()

    def 显示(自身):
        '打开菜单。没有当前模型就直接进入模型列表'
        派生=自身.派生(自身.读状态())
        自身.选定焦点=False
        if 自身.触发 is not None:
            自身.触发.focus()
        自身.查询=''
        自身.高亮下标=None
        if 派生['当前选择'] is None:
            自身.面板焦点='drill'
        自身.面板='model' if 派生['当前选择'] is None else 'root'
        自身.打开=True
        自身.重载()
        自身.渲染()

    def 改查询(自身,下一):
        '换搜索词，并把高亮放回第一行'
        自身.查询=下一
        自身.高亮下标=0
        自身.渲染()

    def 关闭(自身,还焦=False):
        '关掉菜单并回到根面板'
        自身.打开=False
        自身.面板='root'
        if 还焦 is True:
            窗口=自身.窗口()
            def 聚焦():
                '把焦点还给触发器'
                if 自身.触发 is not None:
                    自身.触发.focus()
            窗口.queueMicrotask(聚焦)
        自身.渲染()

    def 选定后关闭(自身):
        '选中后关掉，焦点环先不画，直到触发器再失焦'
        自身.选定焦点=True
        自身.关闭(True)

    def 钻入(自身,下一):
        '从根行进入模型列表或推理等级'
        自身.查询=''
        自身.高亮下标=None
        自身.面板焦点='drill'
        自身.面板=下一
        自身.渲染()

    def 返回根(自身,来自):
        '从钻入的面板回到根行，焦点还给打开它的那一格'
        自身.面板焦点=来自
        自身.面板='root'
        自身.渲染()

    def 提交(自身,选定):
        '提交选定。成功关掉，失败在撰写卡片旁吐司'
        自身.上次动作='select'
        自身.选定焦点=True
        if 自身.触发 is not None:
            自身.触发.focus()
        结果=自身.属性['select'](选定)
        if 结果 is None:
            自身.渲染()
            return
        if 结果.get('ok') is True:
            if 自身.根 is not None:
                自身.选定后关闭()
            return
        错=结果.get('error') or {}
        自身.吐司序号+=1
        if 错.get('code')=='session/writer-held':
            文='当前会话已被占用，可能是其他正在运行的 DSH 导致的（如其他 dsh web、桌面端），请退出其他正在运行的 DSH 后重试。'
        else:
            文='模型操作失败：'+str(错.get('code'))+': '+str(错.get('message'))
        自身.吐司={'seq':自身.吐司序号,'text':文}
        自身.渲染()

    def 选定模型(自身,选定):
        '点的就是当前模型则只关闭，否则提交'
        当前=自身.读状态().get('current')
        if 当前 is not None and 当前.get('provider')==选定.get('provider') and 当前.get('model')==选定.get('model'):
            自身.选定后关闭()
            return
        自身.提交(选定)

    def 按键(自身,事件):
        'Escape 先退出钻入的面板。搜索时上下键只移动高亮'
        if getattr(事件,'isComposing',False) is True:
            return
        if 事件.key=='Escape' and 自身.打开:
            事件.preventDefault()
            派生=自身.派生(自身.读状态())
            if 自身.面板!='root' and 派生['当前选择'] is not None:
                自身.返回根(自身.面板)
            else:
                自身.关闭(True)
            return
        if 自身.打开 is not True:
            return
        派生=自身.派生(自身.读状态())
        显示搜索=派生['显示搜索']
        可见=派生['可见']
        活跃=派生['活跃']
        忙=派生['忙']
        if 自身.面板=='model' and 显示搜索 and 事件.key in ('ArrowDown','ArrowUp'):
            事件.preventDefault()
            if 忙 is not True and len(可见)>0:
                方向=1 if 事件.key=='ArrowDown' else -1
                自身.高亮下标=(活跃+方向+len(可见))%len(可见)
                if 自身.搜索框 is not None:
                    自身.搜索框.focus()
                自身.渲染()
            return
        目标=事件.target
        if (自身.面板=='model' and 显示搜索 and getattr(目标,'tagName',None)=='INPUT'
                and (事件.key=='Enter' or (事件.key=='Tab' and getattr(事件,'shiftKey',False) is not True))):
            if 事件.key=='Tab' and len(可见)==0:
                return
            事件.preventDefault()
            if 忙 is not True and 活跃>=0 and 活跃<len(可见):
                自身.选定模型(可见[活跃])
            return
        if 事件.key=='Tab':
            if getattr(事件,'shiftKey',False) is True:
                事件.preventDefault()
                if 自身.面板!='root' and 派生['当前选择'] is not None:
                    自身.返回根(自身.面板)
                else:
                    自身.关闭(True)
                return
            活动=自身.窗口().document.activeElement
            行=[]
            for 钮 in 自身.行引用:
                if 钮 is not None:
                    行.append(钮)
            if getattr(活动,'tagName',None)=='BUTTON' and 活动 in 行:
                事件.preventDefault()
                活动.click()
                return
            if 活动 is not 自身.触发:
                return
            事件.preventDefault()
            if 自身.面板=='model' and 显示搜索:
                自身.高亮下标=None
                if 自身.搜索框 is not None:
                    自身.搜索框.focus()
                自身.渲染()
                return
            选中=None
            if 自身.菜单 is not None:
                选中=自身.菜单.querySelector('[role="menuitemradio"][aria-checked="true"]:not([disabled])')
            if 选中 is None:
                for 钮 in 行:
                    if 钮.disabled is not True:
                        选中=钮
                        break
            if 选中 is not None:
                选中.focus()
            return
        if 事件.key in ('ArrowDown','ArrowUp'):
            事件.preventDefault()
            行=[]
            for 钮 in 自身.行引用:
                if 钮 is not None:
                    行.append(钮)
            if len(行)==0:
                return
            活动=自身.窗口().document.activeElement
            当前=-1
            序=0
            for 钮 in 行:
                if 钮 is 活动:
                    当前=序
                    break
                序+=1
            偏移=1 if 事件.key=='ArrowDown' else -1
            if 当前==-1:
                下一个=0 if 偏移>0 else len(行)-1
            else:
                下一个=(当前+偏移+len(行))%len(行)
            行[下一个].focus()

    def 失焦(自身,事件):
        '焦点离开触发器和菜单才关闭'
        相关=getattr(事件,'relatedTarget',None)
        if 相关 is not None:
            if 自身.根 is not None and 自身.根.contains(相关) is True:
                return
            if 自身.菜单 is not None and 自身.菜单.contains(相关) is True:
                return
        自身.关闭()

    def 按下(自身,事件):
        '按在按钮上时别先把焦点弄丢'
        目标=事件.target
        if hasattr(目标,'closest') and 目标.closest('button') is not None:
            事件.preventDefault()

    def 点外(自身,事件):
        '点在触发器和菜单外面就关闭'
        目标=事件.target
        if 自身.根 is not None and 自身.根.contains(目标) is True:
            return
        if 自身.菜单 is not None and 自身.菜单.contains(目标) is True:
            return
        自身.打开=False
        自身.渲染()

    def 点触发(自身,事件):
        '再点一次就关闭，否则打开'
        if 自身.打开:
            自身.关闭(True)
        else:
            自身.显示()

    def 触发模糊(自身,事件):
        '触发器失焦后恢复焦点环'
        自身.选定焦点=False
        if 自身.触发 is not None:
            自身.触发.removeAttribute('data-selection-focus')

    def 放置(自身,事件=None):
        '菜单固定在触发器上方，右缘对齐，并夹在视口里'
        if 自身.打开 is not True or 自身.触发 is None or 自身.菜单 is None:
            return
        矩形=自身.触发.getBoundingClientRect()
        if 矩形 is None:
            return
        边距=12
        宽=自身.菜单.offsetWidth or 0
        高=自身.菜单.offsetHeight or 0
        横=矩形['right']-宽
        纵=矩形['top']-8-高
        窗口=自身.窗口()
        if 宽>0:
            最大横=窗口.innerWidth-宽-边距
            if 横<边距:
                横=边距
            if 横>最大横:
                横=最大横
        if 高>0:
            最大纵=窗口.innerHeight-高-边距
            if 纵<边距:
                纵=边距
            if 纵>最大纵:
                纵=最大纵
        自身.菜单.style.visibility='visible'
        自身.菜单.style.left=str(横)+'px'
        自身.菜单.style.top=str(纵)+'px'

    def 摘点外(自身):
        '卸掉文档上的点外监听'
        if 自身.已听点外 is not True:
            return
        自身.窗口().document.removeEventListener('mousedown',自身.点外)
        自身.已听点外=False

    def 摘滚动(自身):
        '卸掉滚动和缩放监听'
        if 自身.已听滚动 is not True:
            return
        窗口=自身.窗口()
        窗口.removeEventListener('scroll',自身.放置,True)
        窗口.removeEventListener('resize',自身.放置)
        自身.已听滚动=False

    def 卸菜单(自身):
        '拆掉传送到 body 的菜单和粘性观察'
        if 自身.粘性拆除 is not None:
            自身.粘性拆除()
            自身.粘性拆除=None
        if 自身.菜单面 is not None:
            if 自身.菜单面.背板 is not None:
                自身.菜单面.背板.remove()
                自身.菜单面.背板=None
            if 自身.菜单面.根 is not None:
                自身.菜单面.根.remove()
                自身.菜单面.根=None
        自身.菜单=None
        自身.搜索框=None
        自身.分组视口=None
        自身.行引用=[]

    def 渲染(自身):
        '画出触发器。打开时把两级菜单传送到 body'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        完成=False
        try:
            if 自身.属性.get('available') is not True:
                自身.卸菜单()
                自身.摘点外()
                自身.摘滚动()
                if 自身.根 is not None:
                    自身.根.remove()
                    自身.根=None
                return None
            窗口=自身.窗口()
            文档=窗口.document
            注入模块样式文件(
                文档,
                '模型选择样式',
                os.path.join(os.path.dirname(__file__),'模型选择.module.css'),
                样式模块,
            )
            if 自身.根 is None:
                根=建(文档,'div','root')
                根.addEventListener('keydown',自身.按键)
                根.addEventListener('focusout',自身.失焦)
                根.addEventListener('mousedown',自身.按下)
                触发=建(文档,'button','trigger')
                触发.type='button'
                触发.addEventListener('click',自身.点触发)
                触发.addEventListener('blur',自身.触发模糊)
                根.appendChild(触发)
                自身.根=根
                自身.触发=触发
                if 'parent' in 自身.属性 and 自身.属性['parent'] is not None:
                    自身.属性['parent'].appendChild(根)
            状态=自身.读状态()
            if 自身.派生(状态)['显示搜索'] is not True:
                自身.查询=''
                自身.高亮下标=None
            派生=自身.派生(状态)
            当前=状态.get('current')
            忙=派生['忙']
            触发=自身.触发
            触发.setAttribute('aria-label',str(派生['触发读法']))
            触发.setAttribute('aria-haspopup','menu')
            触发.setAttribute('aria-expanded','true' if 自身.打开 else 'false')
            触发.setAttribute('aria-busy','true' if 忙 else 'false')
            触发.title=str(派生['触发文'])
            触发.disabled=自身.属性.get('locked') is True
            if 自身.打开:
                触发.setAttribute('aria-controls',自身.标识+'-menu')
            else:
                触发.removeAttribute('aria-controls')
            if 自身.选定焦点:
                触发.setAttribute('data-selection-focus','')
            else:
                触发.removeAttribute('data-selection-focus')
            while 触发.firstChild is not None:
                触发.firstChild.remove()
            图=数据图标({'window':窗口,'className':'triggerIcon','size':16})
            标样式模块(图,样式模块)
            触发.appendChild(图)
            名=建(文档,'span','triggerLabel')
            名.textContent='' if 派生['模型文'] is None else str(派生['模型文'])
            触发.appendChild(名)
            if 派生['力度文'] is not None:
                力度=建(文档,'span','triggerEffort')
                力度.textContent=str(派生['力度文'])
                触发.appendChild(力度)
            if 忙:
                触发.appendChild(处理状态点(窗口,{'state':'ongoing'}))
            else:
                箭头类='chevron chevronOpen' if 自身.打开 else 'chevron'
                箭头=图标下箭头描边常规({'window':窗口,'className':箭头类})
                标样式模块(箭头,样式模块)
                触发.appendChild(箭头)
            焦点=None
            活动=文档.activeElement
            if 自身.搜索框 is not None and 活动 is 自身.搜索框:
                焦点={'种类':'搜索','起':活动.selectionStart,'止':活动.selectionEnd}
            elif 活动 is 自身.触发:
                焦点={'种类':'触发'}
            else:
                序=0
                for 钮 in 自身.行引用:
                    if 钮 is 活动:
                        焦点={'种类':'行','序':序}
                        break
                    序+=1
            自身.卸菜单()
            if 自身.打开 is not True:
                自身.摘点外()
                自身.摘滚动()
            else:
                if 自身.菜单面 is None:
                    自身.菜单面=菜单表面()
                自身.菜单面.更新({
                    'window':窗口,
                    'className':'menu',
                    'role':'group' if 自身.面板=='model' else 'menu',
                    'parent':文档.body,
                })
                菜单=自身.菜单面.渲染()
                标样式模块(菜单,样式模块)
                菜单.id=自身.标识+'-menu'
                菜单.setAttribute('aria-label','模型与推理等级')
                加载中=状态.get('status')=='loading' or 忙
                菜单.setAttribute('aria-busy','true' if 加载中 else 'false')
                菜单.style.visibility='hidden'
                菜单.style.left='0px'
                菜单.style.top='0px'
                菜单.style.borderRadius='var(--dsw-radius-lg)'
                菜单.style.isolation='isolate'
                锚名=菜单.style.getPropertyValue('--dsh-menu-anchor')
                if isinstance(锚名,str) and 锚名!='':
                    菜单.style.setProperty('anchor-name',锚名)
                菜单.addEventListener('keydown',自身.按键)
                菜单.addEventListener('focusout',自身.失焦)
                自身.菜单=菜单
                自身.行引用=[]
                if 自身.面板=='root':
                    def 点模型行(事件):
                        '钻进模型列表'
                        自身.钻入('model')
                    模型行=建(文档,'button','cell')
                    模型行.type='button'
                    模型行.setAttribute('role','menuitem')
                    模型行.addEventListener('click',点模型行)
                    模型题=建(文档,'span','cellLabel')
                    模型题.textContent='模型'
                    模型值=建(文档,'span','cellValue')
                    模型值.textContent='' if 派生['模型文'] is None else str(派生['模型文'])
                    模型箭=右箭头图标({'window':窗口,'className':'cellChevron'})
                    标样式模块(模型箭,样式模块)
                    模型行.appendChild(模型题)
                    模型行.appendChild(模型值)
                    模型行.appendChild(模型箭)
                    自身.行引用.append(模型行)
                    菜单.appendChild(模型行)
                    if 派生['推理'] is not None:
                        def 点力度行(事件):
                            '钻进推理等级'
                            自身.钻入('effort')
                        力度行=建(文档,'button','cell')
                        力度行.type='button'
                        力度行.setAttribute('role','menuitem')
                        力度行.addEventListener('click',点力度行)
                        力度题=建(文档,'span','cellLabel')
                        力度题.textContent='推理等级'
                        力度值=建(文档,'span','cellValue')
                        力度值.textContent='' if 派生['力度文'] is None else str(派生['力度文'])
                        力度箭=右箭头图标({'window':窗口,'className':'cellChevron'})
                        标样式模块(力度箭,样式模块)
                        力度行.appendChild(力度题)
                        力度行.appendChild(力度值)
                        力度行.appendChild(力度箭)
                        自身.行引用.append(力度行)
                        菜单.appendChild(力度行)
                if 自身.面板=='model':
                    if 派生['显示搜索']:
                        搜索行=建(文档,'div','searchRow')
                        搜索类=拼类('search','searchWithQuery' if 自身.查询!='' else '')
                        搜索壳=处理输入(窗口,{
                            'className':搜索类,
                            'type':'text',
                            'placeholder':'搜索模型…',
                            'value':自身.查询,
                            'readOnly':忙,
                        })
                        标样式模块(搜索壳,样式模块)
                        框=搜索壳.querySelector('input')
                        if 框 is not None:
                            框.setAttribute('role','searchbox')
                            框.setAttribute('aria-label','搜索模型…')
                            框.setAttribute('aria-controls',自身.标识+'-models')
                            if 派生['活跃']<0:
                                框.removeAttribute('aria-activedescendant')
                            else:
                                框.setAttribute('aria-activedescendant',自身.标识+'-model-'+str(派生['活跃']))
                            def 输入了(事件):
                                '搜索框文字变了'
                                自身.改查询(框.value)
                            框.addEventListener('input',输入了)
                            自身.搜索框=框
                        搜索行.appendChild(搜索壳)
                        if 自身.查询!='':
                            清除=建(文档,'button','searchClear')
                            清除.type='button'
                            清除.setAttribute('aria-label','清除搜索')
                            清除.disabled=忙
                            def 点清除(事件):
                                '清空搜索并回到搜索框'
                                自身.改查询('')
                                if 自身.搜索框 is not None:
                                    自身.搜索框.focus()
                            清除.addEventListener('click',点清除)
                            叉=描边图标({'window':窗口},'0 0 16 16',[
                                'M3.5 3.5L12.5 12.5',
                                'M12.5 3.5L3.5 12.5',
                            ],14,常规描边)
                            清除.appendChild(叉)
                            搜索行.appendChild(清除)
                        菜单.appendChild(搜索行)
                    if 状态.get('status')=='loading':
                        状态行=建(文档,'div','status')
                        状态行.textContent='正在刷新模型列表…'
                        菜单.appendChild(状态行)
                    if 状态.get('error') is not None and 自身.上次动作=='load':
                        错行=建(文档,'div','error')
                        错字=文档.createElement('span')
                        错字.textContent='模型操作失败：'+str(状态.get('error'))
                        重试=建(文档,'button','retry')
                        重试.type='button'
                        重试.textContent='重试'
                        def 点重试(事件):
                            '再拉一次目录'
                            自身.重载()
                            自身.渲染()
                        重试.addEventListener('click',点重试)
                        错行.appendChild(错字)
                        错行.appendChild(重试)
                        菜单.appendChild(错行)
                    for 失败 in 状态.get('failures') or []:
                        警=建(文档,'div','warning')
                        名文='DeepSeek 账号' if 失败.get('id')=='deepseek-account' else 失败.get('name')
                        警字=文档.createElement('span')
                        警字.textContent=str(名文)+' 加载失败：'+str(失败.get('message'))
                        再试=建(文档,'button','retry')
                        再试.type='button'
                        再试.textContent='重试'
                        def 点再试(事件):
                            '分组失败后再拉一次'
                            自身.重载()
                            自身.渲染()
                        再试.addEventListener('click',点再试)
                        警.appendChild(警字)
                        警.appendChild(再试)
                        菜单.appendChild(警)
                    分组盒=建(文档,'div',拼类('groups','scrollable'))
                    分组盒.id=自身.标识+'-models'
                    分组盒.setAttribute('role','menu')
                    分组盒.setAttribute('aria-label','模型')
                    分组盒.hidden=len(派生['过滤'])==0
                    模型序=0
                    for 组 in 派生['过滤']:
                        按钮列=[]
                        组名='DeepSeek 账号' if 组.get('id')=='deepseek-account' else 组.get('name')
                        for 模型 in 组['models']:
                            下标=模型序
                            模型序+=1
                            选中=当前 is not None and 当前.get('provider')==组.get('id') and 当前.get('model')==模型.get('id')
                            行类=拼类(
                                'option','modelOption',
                                'selected' if 选中 else '',
                                'optionActive' if 下标==派生['活跃'] else '',
                            )
                            行=建(文档,'button',行类)
                            行.type='button'
                            行.setAttribute('role','menuitemradio')
                            行.setAttribute('aria-checked','true' if 选中 else 'false')
                            行.id=自身.标识+'-model-'+str(下标)
                            行.tabIndex=-1 if 派生['显示搜索'] else 0
                            if 下标==派生['活跃']:
                                行.setAttribute('data-highlighted','')
                            行.title='' if 模型.get('name') is None else str(模型.get('name'))
                            行.disabled=忙
                            文案=建(文档,'span','optionCopy')
                            模型名=建(文档,'span','modelName')
                            模型名.textContent='' if 模型.get('name') is None else str(模型.get('name'))
                            文案.appendChild(模型名)
                            勾格=建(文档,'span','check')
                            待定=状态.get('pending')
                            if 待定 is not None and 待定.get('provider')==组.get('id') and 待定.get('model')==模型.get('id'):
                                勾格.appendChild(处理状态点(窗口,{'state':'ongoing'}))
                            elif 选中:
                                勾=图标勾描边常规({'window':窗口})
                                标样式模块(勾,样式模块)
                                勾格.appendChild(勾)
                            行.appendChild(文案)
                            行.appendChild(勾格)
                            def 聚焦这个(事件,行下标=下标):
                                '高亮跟着键盘落到这一行'
                                if 自身.高亮下标==行下标:
                                    return
                                自身.高亮下标=行下标
                                自身.渲染()
                            def 移到这(事件,行下标=下标,要搜索=派生['显示搜索']):
                                '指针移到这一行'
                                if 要搜索:
                                    if 自身.高亮下标!=行下标:
                                        自身.高亮下标=行下标
                                        自身.渲染()
                                elif 行下标<len(自身.行引用) and 自身.行引用[行下标] is not None:
                                    自身.行引用[行下标].focus()
                            def 点这个(事件,提供方=组.get('id'),模型标识=模型.get('id')):
                                '选中这个模型'
                                自身.选定模型({'provider':提供方,'model':模型标识})
                            行.addEventListener('focus',聚焦这个)
                            if 忙 is not True and 下标!=派生['活跃']:
                                行.addEventListener('mousemove',移到这)
                            行.addEventListener('click',点这个)
                            自身.行引用.append(行)
                            按钮列.append(行)
                        分组=菜单组({'window':窗口,'label':组名,'children':按钮列})
                        分组盒.appendChild(分组.渲染())
                    自身.分组视口=分组盒
                    菜单.appendChild(分组盒)
                    if 状态.get('status')=='ready' and len(派生['过滤'])==0:
                        空=建(文档,'div','empty')
                        空.setAttribute('role','status')
                        if len(派生['选择'])==0:
                            空.textContent='暂无可用模型'
                        else:
                            空.textContent='没有匹配的模型。'
                        菜单.appendChild(空)
                if 自身.面板=='effort':
                    if 状态.get('error') is not None and 自身.上次动作=='load':
                        错行=建(文档,'div','error')
                        错字=文档.createElement('span')
                        错字.textContent='模型操作失败：'+str(状态.get('error'))
                        重试=建(文档,'button','retry')
                        重试.type='button'
                        重试.textContent='重新加载'
                        def 点重载(事件):
                            '推理面板上再拉一次目录'
                            自身.重载()
                            自身.渲染()
                        重试.addEventListener('click',点重载)
                        错行.appendChild(错字)
                        错行.appendChild(重试)
                        菜单.appendChild(错行)
                    if len(派生['力度选项'])==0:
                        空=建(文档,'div','empty')
                        空.textContent='当前模型未提供推理等级。'
                        菜单.appendChild(空)
                    else:
                        for 级 in 派生['力度选项']:
                            选中=派生['有效力度']==级['effort']
                            行=建(文档,'button',拼类('option','selected' if 选中 else ''))
                            行.type='button'
                            行.setAttribute('role','menuitemradio')
                            行.setAttribute('aria-checked','true' if 选中 else 'false')
                            行.disabled=忙
                            文案=建(文档,'span','optionCopy')
                            名格=建(文档,'span','modelName')
                            名格.textContent='' if 级['label'] is None else str(级['label'])
                            文案.appendChild(名格)
                            勾格=建(文档,'span','check')
                            待定=状态.get('pending')
                            在飞=待定 is not None and 当前 is not None and 待定.get('provider')==当前.get('provider') and 待定.get('model')==当前.get('model') and 待定.get('reasoningEffort')==级['effort']
                            if 在飞:
                                勾格.appendChild(处理状态点(窗口,{'state':'ongoing'}))
                            elif 选中:
                                勾=图标勾描边常规({'window':窗口})
                                标样式模块(勾,样式模块)
                                勾格.appendChild(勾)
                            行.appendChild(文案)
                            行.appendChild(勾格)
                            def 点等级(事件,力度=级['effort']):
                                '改推理等级。没变就只关闭'
                                现态=自身.读状态()
                                if 现态.get('current') is None:
                                    return
                                现派生=自身.派生(现态)
                                if 现派生['有效力度']==力度:
                                    自身.选定后关闭()
                                    return
                                现当前=现态['current']
                                选定={'provider':现当前['provider'],'model':现当前['model']}
                                if 力度 is not None:
                                    选定['reasoningEffort']=力度
                                自身.提交(选定)
                            行.addEventListener('click',点等级)
                            自身.行引用.append(行)
                            菜单.appendChild(行)
                if 自身.粘性拆除 is not None:
                    自身.粘性拆除()
                    自身.粘性拆除=None
                if 自身.分组视口 is not None:
                    自身.粘性拆除=观察粘性菜单组(自身.分组视口)
                自身.放置()
                if 自身.已听滚动 is not True:
                    窗口.addEventListener('scroll',自身.放置,True)
                    窗口.addEventListener('resize',自身.放置)
                    自身.已听滚动=True
                if 自身.已听点外 is not True:
                    文档.addEventListener('mousedown',自身.点外)
                    自身.已听点外=True
                变了=自身.上次显示搜索 is not 派生['显示搜索']
                自身.上次显示搜索=派生['显示搜索']
                意图=自身.面板焦点
                if 意图 is None and 变了 and 自身.面板=='model':
                    意图='drill'
                自身.面板焦点=None
                已移=False
                if 意图 is not None:
                    已移=True
                    if 意图=='drill':
                        if 自身.面板=='model' and 派生['显示搜索'] and 自身.搜索框 is not None:
                            自身.搜索框.focus()
                        else:
                            选中钮=菜单.querySelector('[role="menuitemradio"][aria-checked="true"]:not([disabled])')
                            if 选中钮 is None:
                                for 钮 in 自身.行引用:
                                    if 钮 is not None and 钮.disabled is not True:
                                        选中钮=钮
                                        break
                            if 选中钮 is None:
                                选中钮=自身.触发
                            if 选中钮 is not None:
                                选中钮.focus()
                    else:
                        下标=1 if 意图=='effort' else 0
                        格=自身.行引用[下标] if 下标<len(自身.行引用) else None
                        if 格 is not None and 格.disabled is not True:
                            格.focus()
                        elif 自身.触发 is not None:
                            自身.触发.focus()
                if 已移 is not True and isinstance(焦点,dict):
                    if 焦点['种类']=='搜索' and 自身.搜索框 is not None:
                        自身.搜索框.focus()
                        if type(焦点.get('起')) in (int,float) and type(焦点.get('止')) in (int,float):
                            自身.搜索框.setSelectionRange(int(焦点['起']),int(焦点['止']))
                    elif 焦点['种类']=='触发' and 自身.触发 is not None:
                        自身.触发.focus()
                    elif 焦点['种类']=='行':
                        序=焦点['序']
                        if 序<len(自身.行引用) and 自身.行引用[序] is not None:
                            自身.行引用[序].focus()
                if 自身.打开 and 自身.面板=='model' and 派生['活跃']>=0 and 派生['活跃']<len(自身.行引用):
                    自身.行引用[派生['活跃']].scrollIntoView({'block':'nearest'})
            if 自身.吐司 is None:
                if 自身.吐司节点 is not None:
                    自身.吐司节点.remove()
                    自身.吐司节点=None
                自身.吐司已画=None
            elif 自身.吐司已画!=自身.吐司['seq']:
                if 自身.吐司节点 is not None:
                    自身.吐司节点.remove()
                    自身.吐司节点=None
                锚=None
                if 自身.根 is not None and hasattr(自身.根,'closest'):
                    锚=自身.根.closest('[data-composer-card]')
                警图=描边图标({'window':窗口},'0 0 16 16',[
                    'M8 14.5C11.5899 14.5 14.5 11.5899 14.5 8C14.5 4.41015 11.5899 1.5 8 1.5C4.41015 1.5 1.5 4.41015 1.5 8C1.5 11.5899 4.41015 14.5 8 14.5Z',
                    'M8 4.29199V9.79199',
                    'M8 10.708V11.708',
                ],16,常规描边)
                def 吐司完():
                    '吐司播完就卸掉'
                    自身.吐司=None
                    if 自身.吐司节点 is not None:
                        自身.吐司节点.remove()
                        自身.吐司节点=None
                    自身.吐司已画=None
                自身.吐司节点=处理吐司(窗口,{
                    'text':自身.吐司['text'],
                    'icon':警图,
                    'anchor':锚,
                    'onDone':吐司完,
                })
                自身.吐司已画=自身.吐司['seq']
            完成=True
            return 自身.根
        finally:
            自身.绘制中=False
            if 完成 and 自身.待重画:
                自身.待重画=False
                return 自身.渲染()
