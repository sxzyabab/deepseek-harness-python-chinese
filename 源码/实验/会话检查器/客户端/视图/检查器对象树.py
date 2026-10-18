'JSON 详情和运行时对象共用的一层展开。已登记的对象可以跳过去'

import json#JSON 树解析
import os#样式
import pywebbridge#窗口
from .....客户端.ui_对话.异常 import 注入模块样式文件,模块节点,标样式模块#样式
from .对象值 import 检查器对象值#一层预览

样式模块='session-inspector'#检查器样式
页大小=50#运行时对象每次多显示的字段数
种类文案={
    'node':'Node',
    'nodeData':'Node Data',
    'group':'Group',
    'groupData':'Group Data',
    'turn':'Turn',
    'turnData':'Turn Data',
    'step':'Step',
    'stepData':'Step Data',
}#对象种类用中文表里的原文

def 确保样式(文档):
    '对象树和 JSON 树共用检查器样式'
    注入模块样式文件(文档,'dsh-session-inspector',os.path.join(os.path.dirname(__file__),'检查器.module.css'),样式模块)#只插一次

class 对象分支:
    '树上的一行。根和 JSON 默认展开，其余等用户打开'
    def __init__(自身,属性):
        '记下值、路径和导航'
        自身.属性=属性#属性
        自身.根=None#这一行
        自身.展开=属性.get('root') is True or 属性.get('json') is True#默认是否展开
        自身.上限=float('inf') if 属性.get('json') is True else 页大小#JSON 不分页
        自身.渲染()#画出

    def 更新(自身,属性):
        '值或修订变了就用新属性，展开状态留在这一支上'
        自身.属性=属性#新属性

    def 拆除(自身):
        '卸掉这一行'
        if 自身.根 is not None:#还在
            自身.根.remove()#拿掉
        自身.根=None#清空

    def 渲染(自身):
        '画出字段名、链接或子列表。读取失败停在这一行'
        属性=自身.属性#当前
        窗口=属性['window']#窗口
        文档=窗口.document#文档
        确保样式(文档)#样式
        值=属性.get('value')#原值
        名=属性.get('name') or ''#字段名
        路径=属性.get('path') or '$'#路径
        祖先=属性.get('ancestors') or {}#已经走过的对象
        导航=属性.get('navigation')#对象导航
        是json=导航 is None#JSON 树没有导航
        旧=自身.根#上一行
        父=旧.parentNode if 旧 is not None else 属性.get('parent')#挂点
        if 旧 is not None:#拆旧行
            旧.remove()#拿掉
        行=文档.createElement('li')#一行
        字段=模块节点(文档,'span',样式模块,'objectField')#字段名
        字段.textContent=名+': '#名字
        try:#这一层的读取
            引用=None#命名引用
            if not 属性.get('root') and 值 is not None and not isinstance(值,(str,int,float,bool)) and 导航 is not None:#子对象才查引用
                引用=导航['objects']['reference'](值)#弱索引
            循环=None#祖先路径
            if 值 is not None and not isinstance(值,(str,int,float,bool)):#对象才可能循环
                循环=祖先.get(id(值))#走过的路径
            内联=引用 is None or 引用.get('kind')=='nodeData'#节点数据仍展开
            显示=None#一层预览
            if 内联 and 循环 is None and not 属性.get('accessor'):#不是取值器或循环
                显示=检查器对象值(值)#标签
            条目=[]#子项
            if 自身.展开 and 显示 is not None and 显示.可展开:#展开才枚举
                for 一项 in 显示.条目():#一层
                    if 是json and 一项.get('properties'):#JSON 不显示合成的其他属性
                        continue#跳过
                    条目.append(一项)#留下
                    if len(条目)>自身.上限:#多留一个用来显示更多
                        break#停
            内容={'reference':引用,'circular':循环,'display':显示,'entries':条目,'error':None}#这一层
        except Exception as 错误:#读取失败
            内容={'error':str(错误)}#停在错误
        if 内容.get('error') is not None:#失败
            行.setAttribute('role','alert')#警告
            行.appendChild(字段)#字段名
            行.appendChild(文档.createTextNode(内容['error']))#错误
        elif 属性.get('absent') is True:#空槽
            行.appendChild(字段)#字段名
            淡=模块节点(文档,'span',样式模块,'objectMuted')#淡色
            淡.textContent='[空槽]'#中文
            行.appendChild(淡)#放入
        elif 属性.get('accessor') is True:#取值器
            行.appendChild(字段)#字段名
            淡=模块节点(文档,'span',样式模块,'objectMuted')#淡色
            淡.textContent='[Getter / Setter，未执行]'#中文
            行.appendChild(淡)#放入
        else:#普通值
            引用=内容.get('reference')#引用
            链接=None#跳转按钮
            if 引用 is not None and 导航 is not None:#可以跳
                链接=模块节点(文档,'button',样式模块,'objectReference')#链接
                链接.setAttribute('type','button')#按钮
                链接.textContent='↗ '+种类文案.get(引用.get('kind'),引用.get('kind') or '')+' · '+str(引用.get('identity'))#种类和身份
                def 点链接(事件,引用值=引用,去=导航['navigate']):
                    '跳到这个对象，不展开这一行'
                    事件.preventDefault()#不提交
                    事件.stopPropagation()#不切换展开
                    去(引用值)#导航
                链接.addEventListener('click',点链接)#点击
            if 引用 is not None and (引用.get('kind')!='nodeData' or 内容.get('circular') is not None):#只显示链接
                行.appendChild(字段)#字段名
                if 链接 is not None:#有链接
                    行.appendChild(链接)#放入
            elif 内容.get('circular') is not None:#循环
                行.appendChild(字段)#字段名
                淡=模块节点(文档,'span',样式模块,'objectMuted')#淡色
                淡.textContent='↩ '+str(内容['circular'])#回到的路径
                行.appendChild(淡)#放入
            else:#就地展开或标量
                显示=内容.get('display')#预览
                if 显示 is None or not 显示.可展开:#标量
                    行.appendChild(字段)#字段名
                    值节=模块节点(文档,'span',样式模块,'objectValue')#值
                    值节.textContent='' if 显示 is None else 显示.标签#标签
                    行.appendChild(值节)#放入
                else:#容器
                    细节=文档.createElement('details')#可展开
                    if 自身.展开:#当前开着
                        细节.setAttribute('open','')#打开
                    def 切换(事件):
                        '跟着 details 的开合'
                        自身.展开=事件.currentTarget.open#新状态
                        自身.渲染()#重画子项
                    细节.addEventListener('toggle',切换)#切换
                    摘要=文档.createElement('summary')#标题
                    摘要.appendChild(字段)#字段名
                    if 链接 is not None:#节点数据也能跳
                        摘要.appendChild(链接)#链接
                        摘要.appendChild(文档.createTextNode(' '))#空格
                    淡=模块节点(文档,'span',样式模块,'objectMuted')#类型
                    淡.textContent=显示.标签#Array、Object 等
                    摘要.appendChild(淡)#放入
                    细节.appendChild(摘要)#标题
                    if 自身.展开:#开着才列子项
                        列表=文档.createElement('ul')#子列表
                        下一代=dict(祖先)#拷贝祖先
                        if 值 is not None and not isinstance(值,(str,int,float,bool)):#对象入栈
                            下一代[id(值)]=路径#这一层的路径
                        树=属性.get('tree')#值树
                        可见=内容['entries'][:自身.上限] if 自身.上限!=float('inf') else 内容['entries']#这一页
                        for 一项 in 可见:#子项
                            子名='其他属性' if 一项.get('properties') else 一项.get('name')#合成属性用中文
                            子路径=路径 if 一项.get('properties') else 路径+'.'+str(一项.get('name'))#路径
                            子属性={'window':窗口,'value':一项.get('value'),'name':子名,'path':子路径,'ancestors':下一代,'navigation':导航,'json':是json,'accessor':一项.get('accessor'),'absent':一项.get('absent'),'tree':树}#子分支
                            if 树 is None:#没有树就自己造
                                子=对象分支(子属性)#新分支
                            else:#树按路径复用展开状态
                                子=树.取分支(子路径,子属性)#复用
                            子节点=子.渲染()#画出
                            if 子节点 is not None:#有行
                                列表.appendChild(子节点)#放入
                        if len(内容['entries'])==0:#没有字段
                            空=模块节点(文档,'li',样式模块,'objectMuted')#空
                            空.textContent='空'#中文
                            列表.appendChild(空)#放入
                        if len(内容['entries'])>自身.上限:#还有
                            更多行=文档.createElement('li')#更多
                            更多=模块节点(文档,'button',样式模块,'objectReference')#按钮
                            更多.setAttribute('type','button')#按钮
                            更多.textContent='显示更多'#中文
                            def 更多点(事件):
                                '再显示一页'
                                自身.上限=自身.上限+页大小#加大
                                自身.渲染()#重画
                            更多.addEventListener('click',更多点)#点击
                            更多行.appendChild(更多)#放入
                            列表.appendChild(更多行)#放入
                        细节.appendChild(列表)#子列表
                    行.appendChild(细节)#整支
        自身.根=行#记住
        if 父 is not None and 行.parentNode is not 父:#挂回
            父.appendChild(行)#挂上
        return 行#这一行

class 值树:
    '一棵对象树。分支按路径复用，避免重画时合上'
    def __init__(自身,属性):
        '空的分支表'
        自身.属性=属性#属性
        自身.分支={}#路径到分支
        自身.根=None#ul

    def 更新(自身,属性):
        '换成新的值和导航'
        自身.属性=属性#新属性

    def 取分支(自身,路径,属性):
        '同一路径留着展开状态'
        已有=自身.分支.get(路径)#已有分支
        if 已有 is None:#第一次
            已有=对象分支(属性)#新建
            自身.分支[路径]=已有#留下
        else:#还在
            已有.更新(属性)#换值
        return 已有#分支

    def 拆除(自身):
        '卸掉整棵树'
        for 分支 in 自身.分支.values():#每一支
            分支.拆除()#卸
        自身.分支.clear()#清空
        if 自身.根 is not None:#根还在
            自身.根.remove()#拿掉
        自身.根=None#清空

    def 渲染(自身):
        '根名叫 $，JSON 和对象导航都从这里开始'
        属性=自身.属性#当前
        窗口=属性['window']#窗口
        文档=窗口.document#文档
        确保样式(文档)#样式
        旧=自身.根#上一棵
        父=旧.parentNode if 旧 is not None else 属性.get('parent')#挂点
        if 旧 is not None:#拆旧树
            旧.remove()#拿掉
        根=模块节点(文档,'ul',样式模块,'objectTree')#树
        子属性={'window':窗口,'value':属性.get('value'),'name':'$','path':'$','ancestors':{},'navigation':属性.get('navigation'),'json':属性.get('navigation') is None,'root':True,'tree':自身}#根分支
        根支=自身.取分支('$',子属性)#根
        根行=根支.渲染()#画出
        if 根行 is not None:#有行
            根.appendChild(根行)#放入
        自身.根=根#记住
        if 父 is not None and 根.parentNode is not 父:#挂回
            父.appendChild(根)#挂上
        return 根#树

class 检查器json树:
    '序列化成功的 JSON。容器一开始都展开，没有对象链接'
    def __init__(自身,属性):
        '解析文本并画出树'
        自身.属性=属性#属性
        自身.文本=None#已解析的文本
        自身.值=None#解析结果
        自身.树=None#值树
        自身.渲染()#画出

    def 更新(自身,属性):
        '文本变了就重新解析'
        自身.属性=属性#新属性

    def 拆除(自身):
        '卸掉树'
        if 自身.树 is not None:#有树
            自身.树.拆除()#卸
        自身.树=None#清空

    def 渲染(自身):
        '空文本表示没有值'
        文本=自身.属性.get('text') or ''#JSON 文本
        if 文本!=自身.文本:#变了
            自身.文本=文本#记下
            自身.值=None if 文本=='' else json.loads(文本)#空文本是没有值
            自身.拆除()#旧树作废
        if 自身.树 is None:#还没有
            自身.树=值树({'window':自身.属性['window'],'value':自身.值,'parent':自身.属性.get('parent')})#纯 JSON
        else:#还在
            自身.树.更新({'window':自身.属性['window'],'value':自身.值,'parent':自身.属性.get('parent')})#换值
        return 自身.树.渲染()#树

class 检查器对象树:
    '根和嵌套的节点数据就地展开，其他已登记对象只做链接'
    def __init__(自身,属性):
        '订阅对话发布，发布变了就重画'
        自身.属性=属性#属性
        自身.树=None#值树
        自身.退订=None#发布订阅
        自身.修订=None#最近一次发布
        自身.渲染()#画出

    def 更新(自身,属性):
        '换成新的值和导航'
        自身.属性=属性#新属性

    def 拆除(自身):
        '卸掉订阅和树'
        if 自身.退订 is not None:#订过
            自身.退订()#拆
        自身.退订=None#清空
        if 自身.树 is not None:#有树
            自身.树.拆除()#卸
        自身.树=None#清空

    def 渲染(自身):
        '用对象表的 updates 当修订。修订变了才重算已展开的字段'
        属性=自身.属性#当前
        更新=属性['objects']['updates']#对话发布
        修订=更新.getSnapshot()#当前发布
        自身.修订=修订#记下
        if 自身.退订 is None:#还没订
            def 变更():
                '发布变了就重画'
                自身.渲染()#重画
            自身.退订=更新.subscribe(变更)#订
        导航={'objects':属性['objects'],'navigate':属性['navigate'],'revision':修订}#导航
        树属性={'window':属性['window'],'value':属性.get('value'),'navigation':导航,'parent':属性.get('parent')}#树
        if 自身.树 is None:#第一次
            自身.树=值树(树属性)#新建
        else:#还在
            自身.树.更新(树属性)#换值
        return 自身.树.渲染()#树
