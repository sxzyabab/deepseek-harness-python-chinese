'锚定的类型筛选。候选同步算完，Enter、确认或点候选才生效'

import os#样式
import pywebbridge#窗口
from .....客户端.ui_对话.异常 import 注入模块样式文件,模块节点,标样式模块#样式
from .....客户端.ui_基础界面组件.菜单表面 import 菜单表面#筛选面板
from .....客户端.ui_基础界面组件.锚定位置 import 使用锚定位置#跟着按钮

样式模块='session-inspector'#检查器样式
序号=0#筛选编号

class 类型筛选器:
    '编辑类型片段。没确认之前不筛选表格'
    def __init__(自身,属性):
        '记下已确认的查询、候选函数和确认回调'
        自身.属性=属性#属性
        自身.根=None#按钮
        自身.打开=False#面板是否打开
        自身.草稿=''#正在输入
        自身.活动=-1#键盘选中的候选
        自身.结果=None#最近一次候选
        自身.表面=None#菜单表面
        自身.拆锚定=None#位置跟踪
        自身.面板=None#面板节点
        自身.输入=None#输入框
        global 序号
        序号=序号+1#下一份
        自身.编号='session-inspector-filter-'+str(序号)#候选编号
        自身.渲染()#画出按钮

    def 更新(自身,属性):
        '换成新的查询或回调'
        自身.属性=属性#新属性

    def 拆除(自身):
        '关掉面板并卸掉按钮'
        自身.关闭(False)#不把焦点还回去
        if 自身.根 is not None:#还在
            自身.根.remove()#拿掉
        自身.根=None#清空

    def 关闭(自身,还焦):
        '合上面板。需要时把焦点还给按钮'
        自身.打开=False#合上
        if 自身.拆锚定 is not None:#还在跟
            自身.拆锚定()#停
        自身.拆锚定=None#清空
        if 自身.表面 is not None:#有表面
            if 自身.表面.根 is not None:#面板
                自身.表面.根.remove()#拿掉
            if 自身.表面.背板 is not None:#背板
                自身.表面.背板.remove()#拿掉
        自身.表面=None#清空
        自身.面板=None#清空
        自身.输入=None#清空
        窗口=自身.属性['window']#窗口
        窗口.removeEventListener('pointerdown',自身.点外,True)#点外面
        窗口.removeEventListener('blur',自身.失焦)#窗口失焦
        if 还焦 and 自身.根 is not None:#把焦点还回去
            自身.根.focus({'preventScroll':True})#不滚动

    def 确认(自身,查询):
        '交给表格并合上'
        自身.属性['apply'](查询)#确认筛选
        自身.关闭(True)#还焦

    def 点外(自身,事件):
        '点在面板和按钮外面就合上，不还焦'
        目标=事件.target#点中的节点
        if 自身.面板 is not None and 自身.面板.contains(目标):#在面板里
            return#不关
        if 自身.根 is not None and 自身.根.contains(目标):#在按钮上
            return#按钮自己处理
        自身.关闭(False)#合上

    def 失焦(自身,事件=None):
        '窗口失焦就合上'
        自身.关闭(False)#不还焦

    def 算候选(自身):
        '同步取候选。失败留在结果里，不让旧结果盖住新查询'
        try:#候选函数自己的失败
            项=自身.属性['suggest'](自身.草稿)#同步列表
            自身.结果={'query':自身.草稿,'items':list(项)}#成功
        except Exception as 错误:#取候选失败
            自身.结果={'query':自身.草稿,'items':[],'error':str(错误)}#错误文本
        自身.活动=-1#选中回到没有

    def 渲染(自身):
        '按钮始终在，面板只在打开时挂到 body'
        属性=自身.属性#当前
        窗口=属性['window']#窗口
        文档=窗口.document#文档
        注入模块样式文件(文档,'dsh-session-inspector',os.path.join(os.path.dirname(__file__),'检查器.module.css'),样式模块)#样式
        值=属性.get('value') or ''#已确认查询
        if 自身.根 is None:#第一次
            按钮=模块节点(文档,'button',样式模块,'typeFilterButton')#筛选按钮
            按钮.setAttribute('type','button')#按钮
            按钮.setAttribute('aria-label','筛选类型')#名称
            按钮.setAttribute('aria-haspopup','dialog')#会打开对话框
            def 点按钮(事件):
                '再点一次就合上，否则用已确认的查询打开'
                if 自身.打开:#已经开着
                    自身.关闭(True)#合上并还焦
                    return#停
                自身.草稿=自身.属性.get('value') or ''#从已确认的查询开始
                自身.结果=None#先空
                自身.活动=-1#没有选中
                自身.打开=True#打开
                自身.渲染()#画出面板
            按钮.addEventListener('click',点按钮)#点击
            图形=文档.createElementNS('http://www.w3.org/2000/svg','svg')#漏斗
            图形.setAttribute('width','13')#宽
            图形.setAttribute('height','13')#高
            图形.setAttribute('viewBox','0 0 16 16')#视框
            图形.setAttribute('fill','none')#不填
            图形.setAttribute('stroke','currentColor')#用当前颜色
            图形.setAttribute('stroke-width','1.3')#线宽
            图形.setAttribute('aria-hidden','true')#装饰
            路径=文档.createElementNS('http://www.w3.org/2000/svg','path')#漏斗路径
            路径.setAttribute('d','M2 3h12L9.5 8v5l-3-1.5V8L2 3Z')#形状
            图形.appendChild(路径)#放入
            按钮.appendChild(图形)#图标
            自身.根=按钮#记住
            if 属性.get('parent') is not None:#有挂点
                属性['parent'].appendChild(按钮)#挂上
        提示='筛选类型' if 值=='' else '筛选类型: *'+值+'*'#空查询只显示标题
        自身.根.setAttribute('title',提示)#提示
        自身.根.setAttribute('aria-expanded','true' if 自身.打开 else 'false')#是否展开
        自身.根.setAttribute('aria-pressed','true' if 值!='' else 'false')#是否已筛选
        if not 自身.打开:#只要按钮
            return 自身.根#按钮
        if 自身.表面 is not None:#重画前先拿掉上一份面板
            if 自身.拆锚定 is not None:#位置跟踪
                自身.拆锚定()#停
            自身.拆锚定=None#清空
            if 自身.表面.根 is not None:#面板
                自身.表面.根.remove()#拿掉
            if 自身.表面.背板 is not None:#背板
                自身.表面.背板.remove()#拿掉
            自身.表面=None#清空
            窗口.removeEventListener('pointerdown',自身.点外,True)#避免重复听
            窗口.removeEventListener('blur',自身.失焦)#避免重复听
        自身.算候选()#同步候选
        当前=自身.结果 if 自身.结果 is not None and 自身.结果.get('query')==自身.草稿 else None#对得上的结果
        项=() if 当前 is None else 当前.get('items') or ()#候选
        选中=自身.活动 if 0<=自身.活动<len(项) else -1#有效下标
        表面=菜单表面({'window':窗口,'compact':True,'className':'typeFilterPanel','role':'dialog','parent':文档.body})#面板
        面板=表面.渲染()#画出
        面板.setAttribute('aria-label','筛选类型')#名称
        自身.表面=表面#记住
        自身.面板=面板#记住
        def 面板键(事件):
            'Esc 合上并且不冒泡'
            if 事件.key!='Escape':#不是取消
                return#不管
            事件.preventDefault()#不默认
            事件.stopPropagation()#不冒泡
            自身.关闭(True)#还焦
        面板.addEventListener('keydown',面板键)#按键
        def 面板糊(事件):
            '焦点离开面板和按钮就合上'
            相关=事件.relatedTarget#新焦点
            if 相关 is not None and 面板.contains(相关):#还在面板
                return#不关
            if 自身.根 is not None and 相关 is not None and 自身.根.contains(相关):#回到按钮
                return#不关
            自身.关闭(False)#合上
        面板.addEventListener('blur',面板糊)#失焦
        盒=文档.createElement('div')#内容
        输入=文档.createElement('input')#查询
        输入.className='typeFilterInput'#输入类名
        标样式模块(输入,样式模块)#模块
        输入.value=自身.草稿#草稿
        输入.setAttribute('role','combobox')#组合框
        输入.setAttribute('aria-label','类型关键词')#名称
        输入.setAttribute('aria-autocomplete','list')#列表补全
        输入.setAttribute('aria-expanded','true')#展开
        输入.setAttribute('aria-controls',自身.编号+'-types')#候选列表
        输入.setAttribute('placeholder','输入类型片段，如 delta')#占位
        if 选中>=0:#有选中
            输入.setAttribute('aria-activedescendant',自身.编号+'-option-'+str(选中))#当前项
        def 输入变了(事件):
            '改草稿并清掉键盘选中'
            自身.草稿=事件.currentTarget.value#新草稿
            自身.活动=-1#没有选中
            自身.渲染()#重算候选
        输入.addEventListener('input',输入变了)#输入
        def 输入键(事件):
            '上下移动候选，Enter 确认。输入法确认不拦截'
            原生=事件#桥上的事件
            if getattr(原生,'isComposing',False) or getattr(原生,'keyCode',0)==229:#输入法
                return#不处理
            现在=自身.结果.get('items') if 自身.结果 is not None and 自身.结果.get('query')==自身.草稿 else []#当前候选
            当前选=自身.活动 if 0<=自身.活动<len(现在) else -1#有效选中
            if 事件.key in ('ArrowDown','ArrowUp'):#移动
                事件.preventDefault()#不滚页面
                if len(现在)==0:#没有候选
                    自身.活动=-1#保持没有
                elif 当前选<0:#还没选
                    自身.活动=0 if 事件.key=='ArrowDown' else len(现在)-1#第一或最后
                else:#循环
                    步=1 if 事件.key=='ArrowDown' else -1#方向
                    自身.活动=(当前选+步+len(现在))%len(现在)#环绕
                自身.渲染()#更新选中
            elif 事件.key=='Enter':#确认
                事件.preventDefault()#不提交别的表单
                用=自身.草稿#默认草稿
                if 0<=当前选<len(现在):#有选中候选
                    用=现在[当前选]#用候选
                自身.确认(用)#生效
        输入.addEventListener('keydown',输入键)#键盘
        盒.appendChild(输入)#输入
        自身.输入=输入#记住
        帮助=模块节点(文档,'div',样式模块,'typeFilterHelp')#说明
        帮助.textContent='默认包含匹配（*关键词*）；Enter 确认，Esc 取消。'#中文说明
        盒.appendChild(帮助)#放入
        列表=模块节点(文档,'div',样式模块,'typeFilterOptions')#候选
        列表.id=自身.编号+'-types'#供输入指向
        列表.setAttribute('role','listbox')#列表
        列表.setAttribute('aria-label','类型候选')#名称
        列表.setAttribute('aria-busy','true' if 当前 is None else 'false')#是否还在算
        for 下标,类型 in enumerate(项):#每个候选
            候选=文档.createElement('button')#一项
            候选.id=自身.编号+'-option-'+str(下标)#编号
            候选.setAttribute('type','button')#按钮
            候选.setAttribute('role','option')#选项
            候选.setAttribute('aria-selected','true' if 选中==下标 else 'false')#是否选中
            候选.setAttribute('tabindex','-1')#不单独停焦
            候选.setAttribute('title',类型)#完整类型
            候选.textContent=类型#类型原文
            def 按下项(事件,类型名=类型):
                '按下时别让输入框失焦'
                事件.preventDefault()#保持焦点
            def 点项(事件,类型名=类型):
                '用这个类型确认'
                自身.确认(类型名)#生效
            候选.addEventListener('pointerdown',按下项)#按下
            候选.addEventListener('click',点项)#点击
            列表.appendChild(候选)#放入
        盒.appendChild(列表)#候选
        if 当前 is None:#还没有结果
            状态=文档.createElement('div')#状态
            状态.setAttribute('role','status')#状态
            状态.textContent='正在查找候选…'#中文
            盒.appendChild(状态)#放入
        elif 当前.get('error') is not None:#失败
            警告=文档.createElement('div')#警告
            警告.setAttribute('role','alert')#警告
            警告.textContent='无法获取类型候选。 '+当前['error']#中文加错误
            盒.appendChild(警告)#放入
        elif len(项)==0:#没有候选
            状态=文档.createElement('div')#状态
            状态.setAttribute('role','status')#状态
            状态.textContent='没有匹配候选，仍可确认当前关键词。'#中文
            盒.appendChild(状态)#放入
        动作=模块节点(文档,'div',样式模块,'typeFilterActions')#按钮行
        def 加动作(文案,动作函数):
            '底部的一个按钮'
            钮=文档.createElement('button')#按钮
            钮.setAttribute('type','button')#按钮
            钮.textContent=文案#中文
            钮.addEventListener('click',动作函数)#点击
            动作.appendChild(钮)#放入
            return 钮#按钮
        def 清空(事件):
            '清草稿并回到输入框'
            自身.草稿=''#空
            自身.活动=-1#没有选中
            自身.渲染()#重画
            if 自身.输入 is not None:#还在
                自身.输入.focus()#焦点
        def 取消(事件):
            '不改已确认的查询'
            自身.关闭(True)#还焦
        def 应用(事件):
            '用当前草稿确认'
            自身.确认(自身.草稿)#生效
        加动作('清空',清空)#清空
        加动作('取消',取消)#取消
        加动作('确认筛选',应用)#确认
        盒.appendChild(动作)#按钮行
        面板.appendChild(盒)#内容
        if 自身.拆锚定 is not None:#旧的跟踪
            自身.拆锚定()#停
        自身.拆锚定=使用锚定位置({'open':True,'anchor':自身.根,'panel':面板,'window':窗口,'gap':4,'margin':12})#跟着按钮
        窗口.addEventListener('pointerdown',自身.点外,True)#点外面
        窗口.addEventListener('blur',自身.失焦)#失焦
        输入.focus({'preventScroll':True})#打开就聚焦
        输入.select()#选中已有草稿
        if 选中>=0:#键盘选中
            选项=面板.querySelectorAll('[role="option"]')#全部选项
            if 选中<len(选项):#还在
                选项[选中].scrollIntoView({'block':'nearest'})#滚进视图
        return 自身.根#按钮仍是这块界面的根
