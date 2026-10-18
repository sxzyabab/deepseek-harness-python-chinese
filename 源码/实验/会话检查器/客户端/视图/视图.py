'侧栏里的一份检查器。展示形式只在这里切换，不另注册对话视图'

import os#样式
import pywebbridge#窗口
from .....客户端.ui_对话.异常 import 注入模块样式文件,模块节点,标样式模块#样式
from .检查器表格 import 检查器表格#共用表格
from .聊天节点.定位 import 检查器聊天定位器#主对话闪框

样式模块='session-inspector'#检查器样式

class 会话检查器视图:
    '一张表，工具栏里切换原始数据和对话分组'
    def __init__(自身,属性):
        '默认先看原始数据'
        自身.属性=属性#槽位属性
        自身.根=None#表格根，选择器算表格的一部分
        自身.模式='session-log'#当前展示
        自身.选取中=False#正在点选
        自身.选取失败=False#点不上或没有对话
        自身.已选取行=None#点到的行
        自身.选取钮=None#选取按钮
        自身.选择器=None#展示形式
        自身.停选取=None#这一次选取的拆除
        自身.选取代=None#避免每次重画都重开选取
        自身.定位器=检查器聊天定位器(属性.get('chatRoot'))#主对话定位
        自身.表格=None#当前表
        自身.表格模式=None#表对应的展示
        自身.渲染()#画出

    def 更新(自身,属性):
        '换成新的会话钩子。主对话根换了才重做定位器'
        旧根=自身.属性.get('chatRoot')#上一份根函数
        自身.属性=属性#新属性
        if 属性.get('chatRoot') is not 旧根:#根函数换了
            自身.定位器.拆除()#取消上一次
            自身.定位器=检查器聊天定位器(属性.get('chatRoot'))#新的定位器

    def 拆除(自身):
        '拆选取、定位和表格'
        if 自身.停选取 is not None:#还在选
            自身.停选取()#拆罩子
        自身.停选取=None#清空
        自身.定位器.拆除()#取消闪框
        if 自身.表格 is not None:#有表
            自身.表格.拆除()#卸
        自身.表格=None#清空

    def 渲染(自身):
        '按当前展示把对应的行交给表格'
        属性=自身.属性#当前
        窗口=属性['window']#窗口
        文档=窗口.document#文档
        注入模块样式文件(文档,'dsh-session-inspector',os.path.join(os.path.dirname(__file__),'检查器.module.css'),样式模块)#样式
        是对话=自身.模式=='chat-node'#对话分组
        if 自身.选择器 is None:#第一次建选择器
            盒=模块节点(文档,'span',样式模块,'modeControls')#选择和选取
            选择=模块节点(文档,'select',样式模块,'modeSelector')#展示形式
            选择.setAttribute('aria-label','展示形式')#中文
            原始=文档.createElement('option')#原始数据
            原始.value='session-log'#值
            原始.textContent='原始数据'#中文
            对话=文档.createElement('option')#对话分组
            对话.value='chat-node'#值
            对话.textContent='对话分组'#中文
            选择.appendChild(原始)#放入
            选择.appendChild(对话)#放入
            def 改展示(事件):
                '换展示时取消选取和点选'
                自身.选取中=False#停止选取
                自身.选取失败=False#清失败
                自身.已选取行=None#清点选
                值=事件.currentTarget.value#新值
                自身.模式='chat-node' if 值=='chat-node' else 'session-log'#只接受这两种
                自身.渲染()#换表
            选择.addEventListener('change',改展示)#变更
            盒.appendChild(选择)#放入
            钮=模块节点(文档,'button',样式模块,'pickButton')#选取
            钮.setAttribute('type','button')#按钮
            钮.setAttribute('aria-label','在对话面板中选取元素')#中文
            def 点选取(事件):
                '再点一次就取消'
                自身.选取失败=False#重试
                自身.选取中=not 自身.选取中#切换
                自身.渲染()#装或拆罩子
            钮.addEventListener('click',点选取)#点击
            图形=文档.createElementNS('http://www.w3.org/2000/svg','svg')#准星
            图形.setAttribute('width','16')#宽
            图形.setAttribute('height','16')#高
            图形.setAttribute('viewBox','0 0 16 16')#视框
            图形.setAttribute('fill','none')#不填
            图形.setAttribute('stroke','currentColor')#当前颜色
            图形.setAttribute('stroke-width','1.3')#线宽
            图形.setAttribute('aria-hidden','true')#装饰
            圆=文档.createElementNS('http://www.w3.org/2000/svg','circle')#圆
            圆.setAttribute('cx','8')#心
            圆.setAttribute('cy','8')#心
            圆.setAttribute('r','4.5')#半径
            路径=文档.createElementNS('http://www.w3.org/2000/svg','path')#十字
            路径.setAttribute('d','M8 0v5M8 11v5M0 8h5M11 8h5')#四向
            图形.appendChild(圆)#放入
            图形.appendChild(路径)#放入
            钮.appendChild(图形)#图标
            盒.appendChild(钮)#放入
            自身.选择器=盒#记住
            自身.选取钮=钮#记住
            自身.展示选择=选择#记住
        自身.展示选择.value=自身.模式#同步选中
        自身.选取钮.setAttribute('aria-pressed','true' if 自身.选取中 else 'false')#是否在选
        自身.选取钮.setAttribute('title','取消选取 (Esc)' if 自身.选取中 else '在对话面板中选取元素')#中文提示
        代=(自身.选取中,自身.模式)#选取是否该重开
        if 代!=自身.选取代:#状态变了
            if 自身.停选取 is not None:#旧的还在
                自身.停选取()#拆
            自身.停选取=None#清空
            自身.选取代=代#记下
            if 自身.选取中 and 自身.选取钮 is not None:#开始选取
                自身.定位器.拆除()#选取时不闪
                def 已选(目标):
                    '对上表格行才结束选取'
                    键=属性['pickRow'](目标,自身.模式)#当前表里的行
                    if 键 is None:#没有
                        自身.选取失败=True#提示没有匹配
                        自身.渲染()#更新说明
                        return False#继续选
                    自身.已选取行={'key':键}#交给表格
                    自身.选取中=False#结束
                    自身.选取失败=False#清失败
                    自身.选取代=None#让下一轮拆罩子
                    自身.渲染()#表格去滚
                    return True#选取器可以拆
                def 已取消():
                    'Esc 或失焦'
                    自身.选取中=False#结束
                    自身.选取失败=False#不清成失败
                    自身.选取代=None#下一轮不再启动
                    自身.渲染()#更新按钮
                停止=属性['pickChat'](自身.选取钮,已选,已取消)#装罩子
                if 停止 is None:#没有对话或插件已卸
                    自身.选取中=False#停
                    自身.选取失败=True#提示先打开对话
                    自身.选取代=(False,自身.模式)#避免立刻再进
                else:#开始了
                    自身.停选取=停止#留下拆除
        if 自身.选取中:#正在选
            说明='当前表格没有匹配记录，请选择其他元素或按 Esc 取消。' if 自身.选取失败 else '在左侧 Chat 中悬停预览，点击选取；Esc 取消。'#中文
        elif 自身.选取失败:#没能开始
            说明='请先在主区域打开当前 Session 的 Chat。'#中文
        else:#平常
            说明=None#不显示
        def 类型于(键,模式=自身.模式):
            '当前行的原始类型'
            return 属性['recordType'](键,模式)#不额外订阅
        def 定位(目标):
            '先解析精确和附近坐标，再闪'
            自身.定位器.定位(属性['resolveChatTargets'](目标))#定位
        def 对话目标(键):
            '对话行在对象表里的坐标'
            引用=属性['objects']['row'](键)#这一行的引用
            if 引用 is None:#没有
                return None#不定位
            return 引用.get('target')#坐标
        导航={
            'reveal':定位,#闪对话
            'target':对话目标 if 是对话 else 属性['logChatTarget'],#这一行的坐标
        }#表格导航
        表属性={
            'window':窗口,'parent':属性.get('parent'),
            'title':'对话分组' if 是对话 else '原始数据',#中文标题
            'modeSelector':自身.选择器,#工具栏里的选择器
            'pickedRow':自身.已选取行,#点到的行
            'notice':说明,#选取说明
            'useRows':属性['useChatRows'] if 是对话 else 属性['useLogRows'],#行顺序
            'useRecord':属性['useChatRecord'] if 是对话 else 属性['useLogRecord'],#单行记录
            'useSession':属性['useSession'],#翻页状态
            'loadOlder':属性['loadOlder'],#加载更早
            'typeOf':类型于,#筛选读类型
            'flash':是对话,#对话新行才闪
            'showTime':not 是对话,#日志才有时间
            'navigation':导航,#定位
        }#表格属性
        if 是对话:#对话分组才有对象树
            表属性['objects']=属性['objects']#对象表
        if 自身.表格 is None or 自身.表格模式!=自身.模式:#换了展示就换一张表
            if 自身.表格 is not None:#旧表
                自身.表格.拆除()#卸
            自身.表格=检查器表格(表属性)#新表
            自身.表格模式=自身.模式#记下
            自身.根=自身.表格.根#表格的根
        else:#同一张表
            自身.表格.更新(表属性)#新属性
            自身.根=自身.表格.渲染()#重画
        return 自身.根#表格
