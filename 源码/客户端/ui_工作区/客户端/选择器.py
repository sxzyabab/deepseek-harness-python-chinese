'挑选和添加工作区。挑选流给浏览区直接用，选择器只包一层给对话空态'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.按钮 import 按钮
from ...ui_基础界面组件.菜单 import 菜单
from ...ui_基础界面组件.模态 import 模态
from ...ui_基础界面组件.icons import 图标
from .会话动作.派生 import 换上
from .导航 import 取同步结果
from .文案 import 中文,取消,关闭,默认工作区名

__all__=['工作区挑选流','工作区选择器','工作区显示标题','工作区挑选流组件','工作区选择器组件']

添加令牌='::add-workspace'#添加项的内部号
默认目录名='default-workspace'#自动标题仍是这个目录名时，显示本地化默认名

def 确保样式(文档):
    '挑选流的错误框和加载句样式只插一次'
    注入模块样式文件(
        文档,
        '工作区选择器样式',
        os.path.join(os.path.dirname(__file__),'选择器.module.css'),
        'workspace-picker',
    )

def 工作区显示标题(标题,默认名):
    '还带着自动标题的工作区显示默认名，其余原样'
    if 标题==默认目录名:#自动标题
        return 默认名#本地化
    return 标题#原样

def 画图标(窗口,名,尺寸=None):
    '按图标表画。没有就空'
    属性={'window':窗口}#窗口
    if 尺寸 is not None:#边长
        属性['size']=尺寸#边长
    return 图标(名,属性)#图标

def 挂上(父,产出):
    '槽位交回的节点挂进父节点'
    if 产出 is None:#空
        return#不挂
    if isinstance(产出,dict):#包装
        for 键 in ('content','body'):#常见
            if hasattr(产出.get(键),'tagName'):#节点
                父.appendChild(产出[键])#挂
                return#完
        if 'items' in 产出:#列表
            挂上(父,产出['items'])#多项
        return#完
    if isinstance(产出,(list,tuple)):#多项
        for 项 in 产出:#逐项
            挂上(父,项)#挂
        return#完
    if hasattr(产出,'tagName'):#节点
        父.appendChild(产出)#挂

class 工作区挑选流:
    '菜单加上采纳失败对话框。目录交互本身由槽位里的占用者负责'
    def __init__(自身,属性):
        '记下属性。错误和流的开关留在这一份上'
        自身.属性=属性#属性
        自身.错误开=False#错误框
        自身.模态错误=None#错误句
        自身.流开=False#目录流开着
        自身.正在挑选=False#正在采纳
        自身.上次忙=None#上次告诉过的忙
        自身.正在画=False#防止重入
        自身.根=None#节点

    def 采纳目录(自身,路径):
        '采纳失败就打开文件夹错误框，重新选择会再开流'
        try:#创建
            工作区=取同步结果(自身.属性['createWorkspace']({'path':路径}))#工作区
            自身.流开=False#关掉流
            自身.属性['onPick'](工作区['workspaceId'])#选中
        except Exception as 原因:#失败
            自身.模态错误=原因.args[0] if isinstance(原因,BaseException) and len(原因.args)>0 else str(原因)#说明
            自身.流开=False#关掉流
            自身.错误开=True#打开错误
        自身.正在挑选=False#结束采纳
        自身.渲染()#重画

    def 打开目录流(自身):
        '关掉菜单和错误，打开目录流'
        自身.属性['onClose']()#关菜单
        自身.错误开=False#关错误
        自身.模态错误=None#清说明
        自身.流开=True#开流

    def 渲染(自身):
        '菜单、加载、目录流和错误框'
        if 自身.正在画:#重入
            return 自身.根#当前
        自身.正在画=True#画
        try:#画完再放开
            return 自身.画出()#节点
        finally:#放开
            自身.正在画=False#结束

    def 画出(自身):
        '按当前开关组出节点'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        文档=窗口.document#文档
        确保样式(文档)#样式
        def 原样(状态):
            '快照本身'
            return 状态#原样
        快照=属性['useWorkspaces'](原样)#工作区快照
        工作区列=快照.get('items') or []#列表
        def 是否占用(占用):
            '洞里有没有人'
            return 占用 is True#占用
        流可用=属性['useDirectoryFlow'](是否占用)#可添加
        忙=自身.流开 or 自身.正在挑选#流或采纳进行中
        if 忙!=自身.上次忙:#忙变了
            自身.上次忙=忙#记下
            if 属性.get('onBusyChange') is not None:#要报告
                属性['onBusyChange'](忙)#报告
        if 自身.流开 and not 流可用:#占用者卸了
            自身.流开=False#撤回
            忙=自身.正在挑选#只剩采纳
        只添加=属性.get('addOnly') is True#只要添加
        添加项=[]#添加条目
        if 流可用:#有占用者
            添加项=[{
                'id':添加令牌,
                'label':中文['menu.addWorkspace'],
                'icon':画图标(窗口,'plus-16',16),
                'disabled':忙,
            }]#添加
        钉住添加=(not 只添加) and len(工作区列)>0#添加钉在下面
        if 钉住添加:#列出已有工作区
            条目=[]#工作区
            for 工作区 in 工作区列:#逐个
                条目.append({
                    'id':工作区['workspaceId'],
                    'label':工作区显示标题(工作区.get('title'),默认工作区名),
                    'icon':画图标(窗口,'folder-close-16',16),
                    'disabled':忙,
                })#一项
        else:#添加就是菜单
            条目=添加项#添加
        菜单空=len(条目)==0#没有可选项
        列表已定=只添加 or 快照.get('phase')=='ready'#列表定了
        添加是唯一=(not 钉住添加) and 列表已定 and len(添加项)==1#唯一动作
        打开=属性.get('open') is True#菜单请求开着
        if 打开 and 添加是唯一 and not 忙:#手势就是添加
            自身.打开目录流()#直接开流
            打开=False#菜单不再开
        def 关闭错误():
            '关掉错误框'
            自身.错误开=False#关
            自身.模态错误=None#清
            自身.渲染()#重画
        def 选中(标识):
            '添加则开流，否则选这个工作区'
            if 标识==添加令牌:#添加
                自身.打开目录流()#开流
                自身.渲染()#重画
                return#停
            属性['onPick'](标识)#选中
        def 锚矩形():
            '用调用方给的按钮量位置'
            引用=属性.get('anchorRef')#按钮
            元素=引用.get('current') if isinstance(引用,dict) else getattr(引用,'current',None)#元素
            if 元素 is None:#没有
                return None#不量
            return 元素.getBoundingClientRect()#矩形
        菜单属性={
            'window':窗口,
            'open':打开 and (not 添加是唯一) and (not 菜单空),
            'anchor':None,
            'items':条目,
            'selectedId':属性.get('selectedId'),
            'onSelect':选中,
            'onClose':属性['onClose'],
            'side':属性.get('side') or 'bottom',
            'portal':True,
            'getAnchorRect':锚矩形,
        }#菜单
        if 钉住添加:#添加钉在脚
            菜单属性['footer']=添加项#脚
        根=文档.createElement('div')#包裹
        菜单节点=菜单(菜单属性).渲染()#菜单
        if 菜单节点 is not None:#有
            根.appendChild(菜单节点)#放入
        if 打开 and (not 添加是唯一) and (not 菜单空) and 快照.get('phase')=='pending':#还在加载
            状=文档.createElement('div')#状态
            状.className='menuStatus'#上游类名
            标样式模块(状,'workspace-picker')#模块
            状.setAttribute('role','status')#状态
            状.textContent=中文['picker.loading']#正在加载
            根.appendChild(状)#放入
        def 选了(路径):
            '采纳期间流保持忙'
            自身.正在挑选=True#忙
            自身.采纳目录(路径)#采纳
        def 取消流():
            '关掉流'
            自身.流开=False#关
            自身.渲染()#重画
        def 流出错(消息):
            '交互自己失败'
            自身.流开=False#关
            自身.模态错误=消息#说明
            自身.错误开=True#开错误
            自身.渲染()#重画
        流主={
            'open':自身.流开,
            'busy':自身.正在挑选,
            'onPicked':选了,
            'onCancel':取消流,
            'onError':流出错,
        }#交给占用者
        流盒=文档.createElement('div')#流
        挂上(流盒,属性['renderDirectoryFlow'](流主))#占用者
        根.appendChild(流盒)#放入
        def 重试():
            '重新选择'
            自身.打开目录流()#开流
            自身.渲染()#重画
        取消钮=按钮({'window':窗口,'variant':'outline','className':'modalAction','onClick':关闭错误,'children':取消})#取消
        重试钮=按钮({
            'window':窗口,
            'variant':'primary',
            'className':'modalAction',
            'disabled':not 流可用,
            'onClick':重试,
            'children':中文['folderError.retry'],
        })#重新选择
        错误体=文档.createElement('div')#说明
        错误体.className='modalError'#上游类名
        标样式模块(错误体,'workspace-picker')#模块
        错误体.setAttribute('role','alert')#提示
        错误体.textContent='' if 自身.模态错误 is None else str(自身.模态错误)#句子
        框=模态({
            'window':窗口,
            'open':自身.错误开,
            'onClose':关闭错误,
            'closeLabel':关闭,
            'title':中文['folderError.title'],
            'footer':[取消钮,重试钮],
            'children':错误体,
        })#错误框
        框节点=框.渲染()#画
        if 框节点 is not None:#开着
            根.appendChild(框节点)#放入
        return 换上(自身,根)#节点

class 工作区选择器:
    '对话空态。状态都在挑选流里'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.流=None#挑选流
        自身.根=None#节点

    def 渲染(自身):
        '把空态属性收成挑选流'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        def 画流(流主):
            '英雄上的目录流洞'
            return 属性['renderSlot']('conversation.hero.workspace.directoryFlow',流主)#洞
        流属性={
            'window':窗口,
            'open':属性.get('open'),
            'anchorRef':属性.get('anchorRef'),
            'useWorkspaces':属性['useWorkspaces'],
            'createWorkspace':属性['createWorkspace'],
            'useDirectoryFlow':属性['useDirectoryFlow'],
            'renderDirectoryFlow':画流,
            'selectedId':属性.get('selectedId'),
            'onPick':属性['onPick'],
            'onClose':属性['onClose'],
        }#流
        if 自身.流 is None:#第一次
            自身.流=工作区挑选流(流属性)#创建
        else:#更新
            自身.流.属性=流属性#换属性
        return 换上(自身,自身.流.渲染())#节点

def 工作区挑选流组件(属性):
    '浏览区自己持有实例，这个函数给需要函数的登记用'
    return 工作区挑选流(属性).渲染()#节点

def 工作区选择器组件(属性):
    '同一登记只留一份选择器'
    if not hasattr(工作区选择器组件,'实例'):#第一次
        工作区选择器组件.实例=工作区选择器(属性)#创建
    else:#再来
        工作区选择器组件.实例.属性=属性#更新
    return 工作区选择器组件.实例.渲染()#节点
