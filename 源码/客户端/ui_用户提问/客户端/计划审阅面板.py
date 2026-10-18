'计划待审卡片。正文留在侧栏，这里只做决定'
import os
from ...ui_对话.异常 import 注入模块样式文件,模块节点,标样式模块#样式模块
from ...ui_基础界面组件.按钮 import 按钮#决定按钮
from ...ui_基础界面组件.状态点 import 状态点#等待或进行中
from ...ui_基础界面组件.icons import 图标编辑16#要求修改
from ...ui_基础界面组件.markdown.纯文本 import 抽取Markdown纯文本#标题和摘要

__all__=['计划审阅面板']

样式路径=os.path.join(os.path.dirname(__file__),'计划审阅面板.module.css')#本目录样式
样式模块='PlanReviewPanel'#与样式表对应的模块名


def 设类(节点,*类名):
    '挂上官方类名，让模块样式生效'
    节点.className=' '.join(类名)#类名保持原文
    return 标样式模块(节点,样式模块)#模块属性


class 计划审阅面板:
    '一次计划决定。同一条请求复用忙态和错误'
    实例表={}#请求键到面板

    def __new__(类,属性=None):
        '槽位调用时交出卡片节点'
        return 类.呈现(属性)#卡片

    @classmethod
    def 呈现(类,属性):
        '根还在页面上就更新，卸下之后重新画'
        待=属性['matched']#这一条提问
        键=待.key#请求键
        已有=类.实例表[键] if 键 in 类.实例表 else None#已有
        if 已有 is not None and 已有.根 is not None and 已有.根.parentNode is not None:#还挂着
            已有.属性=属性#换属性
            return 已有.渲染()#更新
        已有=object.__new__(类)#新面板
        类.实例表[键]=已有#记住
        已有.建立(属性)#初始化
        return 已有.渲染()#画出

    def 建立(自身,属性):
        '先记下请求，节点等渲染时再造'
        自身.属性=属性#槽位属性
        自身.忙=False#正在送出
        自身.错误=None#失败句
        自身.根=None#外层
        自身.点=None#状态点
        自身.点态=None#当前点态

    def 审阅(自身):
        '撰写器已经收窄好的计划'
        if 'review' in 自身.属性 and 自身.属性['review'] is not None:#直接带来
            return 自身.属性['review']#审阅
        return None#没有

    def 渲染(自身):
        '第一次造卡片。之后只改摘要、忙态、错误和动作槽'
        窗口=自身.属性['window']#浏览器窗口
        文档=窗口.document#文档
        待=自身.属性['matched']#提问
        审阅=自身.审阅()#计划
        if 自身.根 is None:#第一次
            根=模块节点(文档,'div',样式模块,'frame')#外层
            根.setAttribute('data-plan-review-key',待.key)#请求键
            卡=模块节点(文档,'section',样式模块,'card')#卡片
            卡.setAttribute('aria-label',审阅['question'])#无障碍名
            条=模块节点(文档,'div',样式模块,'strip')#色条
            自身.点=状态点({'window':窗口,'state':'warning'})#未作答
            自身.点态='warning'#当前
            条.appendChild(自身.点.渲染())#点
            条.appendChild(文档.createTextNode('计划待审'))#标题
            动作位=模块节点(文档,'div',样式模块,'previewActions')#侧栏动作
            条.appendChild(动作位)#动作
            卡.appendChild(条)#色条
            摘要=模块节点(文档,'div',样式模块,'summary')#摘要
            题=模块节点(文档,'h3',样式模块,'title')#标题
            说明=模块节点(文档,'p',样式模块,'description')#说明
            摘要.appendChild(题)#标题
            摘要.appendChild(说明)#说明
            卡.appendChild(摘要)#摘要
            脚=模块节点(文档,'div',样式模块,'footer')#页脚
            反馈=模块节点(文档,'div',样式模块,'feedback')#错误
            反馈.setAttribute('role','status')#状态
            行=模块节点(文档,'div',样式模块,'actions')#按钮
            改=按钮({#要求修改
                'window':窗口,
                'variant':'outline',
                'className':'discuss',
                'disabled':False,
                'onClick':自身.点修改,
                'children':'要求修改',
            })
            改钮=改.渲染()#按钮
            标样式模块(改钮,样式模块)#讨论样式
            图=图标编辑16({'window':窗口,'size':14})#铅笔
            改钮.insertBefore(图,改钮.firstChild)#图标在前
            行.appendChild(改钮)#修改
            同意=按钮({#同意执行
                'window':窗口,
                'variant':'primary',
                'disabled':False,
                'onClick':自身.点同意,
                'children':'同意执行',
            })
            同意钮=同意.渲染()#按钮
            说明文=审阅['approve'].get('description')#选项说明
            if isinstance(说明文,str):#有说明才给提示
                同意钮.title=说明文#悬停说明
            行.appendChild(同意钮)#同意
            脚.appendChild(反馈)#错误
            脚.appendChild(行)#按钮
            卡.appendChild(脚)#页脚
            根.appendChild(卡)#卡片
            注入模块样式文件(文档,'计划审阅面板样式',样式路径,样式模块)#样式
            自身.根=根#留下
            自身.卡=卡#留下
            自身.条=条#留下
            自身.动作位=动作位#留下
            自身.题=题#留下
            自身.说明=说明#留下
            自身.反馈=反馈#留下
            自身.改钮=改钮#留下
            自身.同意钮=同意钮#留下
        标题=抽取Markdown纯文本(审阅['plan'],{'mode':'first-line'})#首行
        段落=抽取Markdown纯文本(审阅['plan'],{'mode':'first-paragraph'})#首段
        if 段落==标题:#和标题相同就不重复
            段落=''#不显示
        自身.题.textContent=标题#标题
        自身.说明.textContent=段落#说明
        if 段落=='':#没有说明
            自身.说明.style.display='none'#藏起
        else:#有说明
            自身.说明.style.display=''#显示
        自身.反馈.textContent='' if 自身.错误 is None else 自身.错误#错误
        自身.卡.setAttribute('aria-busy','true' if 自身.忙 else 'false')#忙态
        自身.改钮.disabled=自身.忙#修改
        自身.同意钮.disabled=自身.忙#同意
        态='ongoing' if 自身.忙 else 'warning'#点的状态
        if 自身.点态!=态:#需要换点
            自身.点态=态#记下
            自身.点.更新({'window':窗口,'state':态})#换状态
            新点=自身.点.渲染()#新点
            自身.条.insertBefore(新点,自身.条.firstChild)#放回条首
        while 自身.动作位.firstChild is not None:#清掉旧动作
            自身.动作位.removeChild(自身.动作位.firstChild)#摘掉
        槽=自身.属性['renderSlot']('conversation.plan-review.actions',{#计划动作
            'review':审阅,#这份计划
            'requestKey':待.key,#请求键
            'window':窗口,#子界面造节点
        })
        节点=槽#可能是节点或包装
        见过=[]#防止自己套自己
        while 节点 is not None and 节点 not in 见过:#往下找节点
            见过.append(节点)#记过
            if hasattr(节点,'tagName'):#已经是节点
                break#停
            根=getattr(节点,'根',None)#组件根
            if 根 is not None and hasattr(根,'tagName'):#有根
                节点=根#用根
                break
            if isinstance(节点,dict):#包装
                下一项=None#往下
                for 键名 in ('content','body','elected','tree'):#常见包装
                    if 键名 in 节点 and 节点[键名] is not None:#有
                        下一项=节点[键名]#往下
                        break
                节点=下一项#继续
                continue
            节点=None#不是能挂的
            break
        if 节点 is not None and hasattr(节点,'tagName'):#能挂
            自身.动作位.appendChild(节点)#放进色条
        if 'parent' in 自身.属性 and 自身.根.parentNode is not 自身.属性['parent']:#指定了父节点
            自身.属性['parent'].appendChild(自身.根)#挂上
        return 自身.根#节点

    def 结算(自身,送出,远程=False):
        '先禁用。远程成功后再收起面板。失败则恢复并显示原因'
        自身.忙=True#先锁
        自身.错误=None#清掉旧错误
        自身.渲染()#写到页面
        try:#送出
            送出()#作答或收起
        except Exception as 原因:#失败
            自身.忙=False#恢复
            自身.错误=str(原因)#原因原样
            自身.渲染()#写回
            return
        if not 远程:#瀑布成功就保持禁用
            return
        自身.忙=False#远程已经收下
        自身.渲染()#恢复按钮，准备收起
        try:#收起面板
            自身.属性['matched'].收起()#离开座位
        except Exception:#面板没关上
            自身.错误='回答已发送；面板未能关闭。'#中文表原文
            自身.渲染()#留下这句

    def 决定(自身,标签):
        '把这个选项当作整份答案送出'
        待=自身.属性['matched']#提问
        审阅=自身.审阅()#计划
        远程=待.getSnapshot()['channel']=='rpc'#已经继续
        def 送出():
            '送出这一条选择'
            待.作答({'answers':[{'id':审阅['id'],'selected':[标签]}]})#答案
        自身.结算(送出,远程)#送出

    def 点修改(自身,_事件=None):
        '收起审阅，回到输入框改计划'
        待=自身.属性['matched']#提问
        def 送出():
            '只收起，不送答案'
            待.收起()#收起
        自身.结算(送出)#收起

    def 点同意(自身,_事件=None):
        '同意执行'
        审阅=自身.审阅()#计划
        自身.决定(审阅['approve']['label'])#同意标签
