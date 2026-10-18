'撰写区里的一次审批：理由、可选详情、拒绝和允许一次'
import os
from ...ui_基础界面组件.按钮 import 按钮#拒绝与允许
from ...ui_基础界面组件.状态点 import 状态点#等待或进行中
from ...ui_对话.异常 import 注入模块样式文件,模块节点,标样式模块#样式模块

__all__=['审批面板']

样式路径=os.path.join(os.path.dirname(__file__),'审批面板.module.css')#本目录样式
样式模块='ApprovalPanel'#与样式表对应的模块名
输入框选择器='input, textarea, select, [contenteditable="true"], [contenteditable=""]'#不接管的输入
按钮选择器='button, a[href], [role="button"]'#Enter 留给控件自己


class 审批流:
    '一条审批的卡片。同一条再次渲染时留下作答和输入法状态'
    def __init__(自身,待处理):
        '先记下待处理面，节点等渲染时再造'
        自身.待处理=待处理#这一条审批
        自身.窗口=None#浏览器窗口
        自身.理由=None#已经解析好的展示句
        自身.详情=None#详情槽交回的节点或树
        自身.已答=False#按钮是否先禁用
        自身.等待中=False#这一次作答还没结束
        自身.活跃=True#卸下后不再恢复按钮
        自身.组合中=False#输入法正在组合
        自身.组合已结束=False#组合刚结束的那一下仍忽略
        自身.根=None#最外层节点
        自身.条=None#等待条
        自身.体=None#理由和详情
        自身.题=None#标题
        自身.命令=None#详情容器
        自身.点=None#状态点
        自身.点态=None#当前点的状态
        自身.拒钮=None#拒绝按钮
        自身.准钮=None#允许一次按钮

    def 标题文(自身):
        '有展示句用展示句。没有就用越权执行这句中文'
        if 自身.理由 is not None:
            return 自身.理由#请求方或审计理由
        工具名=str(自身.待处理.工具名)#插进标题
        return '工具 {toolName} 请求越权执行'.replace('{toolName}',工具名)#中文表原文

    def 渲染(自身,窗口,理由,详情):
        '第一次造卡片，之后只改标题、详情和作答态'
        自身.窗口=窗口#当前窗口
        自身.理由=理由#展示句
        自身.详情=详情#详情槽结果
        if 自身.根 is None:
            窗口=自身.窗口#浏览器窗口
            文档=窗口.document#文档
            根=模块节点(文档,'div',样式模块,'root')#外层
            根.setAttribute('data-approval-key',自身.待处理.key)#这一条的键
            根.setAttribute('aria-busy','false')#还没作答
            根.addEventListener('keydown',自身.按下键)#冒泡阶段
            根.addEventListener('keyup',自身.键抬起,True)#捕获阶段清组合标记
            根.addEventListener('compositionstart',自身.组合开始,True)#捕获阶段
            根.addEventListener('compositionend',自身.组合结束,True)#捕获阶段
            卡=模块节点(文档,'div',样式模块,'card')#卡片
            条=模块节点(文档,'div',样式模块,'strip')#等待条
            自身.点=状态点({'window':窗口,'state':'warning'})#未作答是警告点
            自身.点态='warning'#当前点态
            条.appendChild(自身.点.渲染())#点
            条.appendChild(文档.createTextNode('等待审批'))#等待文案
            卡.appendChild(条)#条进卡片
            体=模块节点(文档,'div',样式模块,'body')#理由区
            体.setAttribute('data-approval-scroll','')#滚动区标记
            体.tabIndex=0#可聚焦
            体.setAttribute('role','group')#一组
            体.setAttribute('aria-label','审批详情')#无障碍名
            题=模块节点(文档,'div',样式模块,'headline')#标题
            题.textContent=自身.标题文()#标题文字
            体.appendChild(题)#标题进正文
            卡.appendChild(体)#正文进卡片
            行=模块节点(文档,'div',样式模块,'actionRow')#按钮行
            拒=按钮({
                'window':窗口,
                'variant':'outline',
                'className':'reject',
                'disabled':False,
                'onClick':自身.点拒绝,
                'children':'拒绝',
            })#拒绝
            自身.拒钮=拒.渲染()#拒绝按钮节点
            标样式模块(自身.拒钮,样式模块)#让拒绝的悬停样式生效
            行.appendChild(自身.拒钮)#拒绝进按钮行
            准=按钮({
                'window':窗口,
                'variant':'primary',
                'disabled':False,
                'onClick':自身.点允许,
                'children':'允许一次',
            })#允许一次
            自身.准钮=准.渲染()#允许按钮节点
            行.appendChild(自身.准钮)#允许进按钮行
            卡.appendChild(行)#按钮行进卡片
            根.appendChild(卡)#卡片进外层
            注入模块样式文件(文档,'审批面板样式',样式路径,样式模块)#样式放在按钮样式之后
            自身.根=根#留下外层
            自身.条=条#留下等待条
            自身.体=体#留下正文
            自身.题=题#留下标题
            自身.放详情()#有详情再挂
        else:
            自身.题.textContent=自身.标题文()#换标题
            自身.放详情()#换详情
        自身.刷新作答态()#按钮和点
        return 自身.根#节点

    def 放详情(自身):
        '没有可挂的节点就不留命令区'
        if 自身.命令 is not None:
            自身.命令.remove()#拆掉旧详情
            自身.命令=None#清空
        节点=自身.详情#槽位交回的结果
        见过=[]#防止树自己套自己
        while 节点 is not None and 节点 not in 见过:
            见过.append(节点)#记过
            if hasattr(节点,'tagName'):
                break#已经是节点
            根=getattr(节点,'根',None)#组件的根
            if 根 is not None and hasattr(根,'tagName'):
                节点=根#用组件根
                break
            if isinstance(节点,dict):
                下一项=None#往下拆
                for 键 in ('content','body','elected','tree'):
                    if 键 in 节点 and 节点[键] is not None:
                        下一项=节点[键]#先拆到内容
                        break
                节点=下一项#继续
                continue
            节点=None#不是能挂的东西
            break
        if 节点 is None or not hasattr(节点,'tagName'):
            return#没有详情
        文档=自身.窗口.document#文档
        命令=模块节点(文档,'div',样式模块,'command')#详情容器
        命令.appendChild(节点)#放进容器
        自身.体.appendChild(命令)#容器跟在标题后
        自身.命令=命令#留下容器

    def 刷新作答态(自身):
        '忙态、状态点和两个按钮跟这次是否已作答'
        if 自身.根 is None:
            return#还没画出
        自身.根.setAttribute('aria-busy','true' if 自身.已答 else 'false')#忙态
        自身.拒钮.disabled=自身.已答#拒绝
        自身.准钮.disabled=自身.已答#允许
        态='ongoing' if 自身.已答 else 'warning'#点的状态
        if 自身.点态==态:
            return#点不用换
        自身.点态=态#记下
        自身.点.更新({'window':自身.窗口,'state':态})#换状态
        新点=自身.点.渲染()#新点
        自身.条.insertBefore(新点,自身.条.firstChild)#放回条首

    def 提交(自身,结果):
        '同一时刻只接受一次。失败且仍可作答时恢复按钮'
        if 自身.等待中 or not 自身.待处理.可作答:
            return#已经在等，或请求已经结束
        自身.等待中=True#先锁住
        自身.已答=True#先禁用
        自身.刷新作答态()#马上写到页面上
        try:
            返回=自身.待处理.作答(结果)#结算
        except Exception:
            自身.失败恢复()#同步失败
            return
        if 返回 is None or not callable(getattr(返回,'then',None)):
            return#同步成功就保持禁用
        def 成功(_值=None):
            '成功后保持禁用'
            return None
        def 失败(_错误=None):
            '期约拒绝后，界面还在且仍可作答才恢复'
            自身.失败恢复()#恢复
        返回.then(成功,失败)#等这次作答的期约

    def 失败恢复(自身):
        '迟到的失败不再改已经卸下的卡片，也不能改已经结束的请求'
        if not 自身.活跃 or not 自身.待处理.可作答:
            return#卸下了，或请求已经结束
        自身.等待中=False#允许再点
        自身.已答=False#按钮恢复
        自身.刷新作答态()#写回页面

    def 点拒绝(自身):
        '拒绝'
        自身.提交('rejected')#拒绝

    def 点允许(自身):
        '允许一次'
        自身.提交('allowed-once')#仅这一次

    def 按下键(自身,事件):
        'Enter 允许一次，Escape 拒绝。输入框、按钮和输入法组合不接管'
        元素=事件.target#事件起点
        文档=自身.窗口.document#用来看焦点
        if 事件.defaultPrevented or not 事件.currentTarget.contains(文档.activeElement):
            return#已经处理过，或焦点不在卡片里
        if 元素.closest(输入框选择器) is not None:
            return#留给输入框
        键=事件.key#键名
        if 键!='Enter' and 键!='Escape':
            return#只认这两个
        if 键=='Enter' and 元素.closest(按钮选择器) is not None:
            return#按钮上的 Enter 留给点击
        if 事件.ctrlKey or 事件.metaKey or 事件.altKey or 事件.shiftKey:
            return#带修饰键不接管
        事件.preventDefault()#不再交给页面
        事件.stopPropagation()#不再往上冒
        if 事件.repeat or 自身.组合中 or 自身.组合已结束 or 事件.isComposing or 事件.keyCode==229:
            return#重复键和输入法候选不提交
        if 键=='Enter':
            自身.提交('allowed-once')#允许一次
            return
        自身.提交('rejected')#拒绝

    def 键抬起(自身,_事件):
        '组合结束标记在键抬起时清掉'
        自身.组合已结束=False#下一键可以提交

    def 组合开始(自身,_事件):
        '输入法组合开始'
        自身.组合中=True#组合期间不提交

    def 组合结束(自身,_事件):
        '输入法组合结束。紧跟着的那一下按键仍忽略'
        自身.组合中=False#组合结束
        自身.组合已结束=True#这一下仍忽略


class 审批面板:
    '渲染一条待处理审批，以及它可选的工具详情'
    def __init__(自身,属性=None):
        '记下槽位交来的属性。键齐了就画'
        自身.属性=属性 if isinstance(属性,dict) else {}#槽位属性
        自身.流=None#当前卡片
        自身.根=None#卡片外层
        if 'window' in 自身.属性 and 'matched' in 自身.属性:
            自身.渲染()#构造时画出

    def 渲染(自身):
        '同一条审批复用卡片。换成另一条时，旧卡片不再接受迟到的失败'
        属性=自身.属性#当前属性
        窗口=属性['window']#浏览器窗口
        待=属性['matched']#选中的审批
        if 待.展示理由 is None:
            理由=待.理由#没有展示文案就用审计理由
        else:
            理由=属性['resolveReason'](待.展示理由)#按当前语言解析
        详情=None#默认没有详情
        if 待.调用 is not None:
            详情=属性['renderSlot']('conversation.approval.detail',{
                'callId':待.调用,#详情槽的主人数据
                'window':窗口,#子界面造节点用
            })#详情槽
        旧根=自身.根#上一张卡片
        if 自身.流 is not None and 自身.流.待处理 is not 待:
            自身.流.活跃=False#旧卡片卸下
        已有=getattr(待,'_审批流',None)#同一条再次渲染
        if 已有 is None:
            已有=审批流(待)#新的一条
            待._审批流=已有#下次复用
        自身.流=已有#当前卡片
        新根=自身.流.渲染(窗口,理由,详情)#画出或更新
        if 旧根 is not None and 旧根 is not 新根 and 旧根.parentNode is not None:
            旧根.parentNode.replaceChild(新根,旧根)#换掉旧卡片
        elif 'parent' in 属性 and 新根.parentNode is not 属性['parent']:
            属性['parent'].appendChild(新根)#挂到指定父节点
        自身.根=新根#留下外层
        return 新根#节点

    def __call__(自身,属性=None):
        '槽位再次交给这块界面时刷新'
        if 属性 is not None:
            自身.属性=属性 if isinstance(属性,dict) else {}#换属性
        return 自身.渲染()#重画
