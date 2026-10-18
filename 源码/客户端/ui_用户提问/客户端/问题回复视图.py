'右侧的迟到回复气泡。读不懂的正文退回模型看到的文本'
import os
from ...ui_对话.异常 import 注入模块样式文件,模块节点,标样式模块#样式模块
from ...ui_基础界面组件.剪贴板 import 写剪贴板#复制
from ...ui_基础界面组件.提示泡 import 提示泡#复制提示
from ...ui_基础界面组件.icons import 图标勾描边常规,图标复制描边常规,图标下箭头描边常规,图标右chevron14#展开和复制
from .问题回复 import 回复答案值#一道题的答案

__all__=['问题回复视图','问题回复气泡']

样式路径=os.path.join(os.path.dirname(__file__),'问题回复视图.module.css')#本目录样式
样式模块='QuestionReplyView'#与样式表对应的模块名


def 设类(节点,*类名):
    '挂上官方类名，让模块样式生效'
    节点.className=' '.join(类名)#类名保持原文
    return 标样式模块(节点,样式模块)#模块属性


class 问题回复气泡:
    '一条已结算回复。同一节点复用展开和已复制'
    实例表={}#节点键到气泡

    @classmethod
    def 呈现(类,属性):
        '根还在页面上就更新，卸下之后按当前数据重新画'
        键=属性['node']['key']#节点键
        已有=类.实例表[键] if 键 in 类.实例表 else None#已有
        if 已有 is not None and 已有.根 is not None and 已有.根.parentNode is not None:#还挂着
            已有.属性=属性#换属性
            return 已有.渲染()#更新
        已有=object.__new__(类)#新气泡
        类.实例表[键]=已有#记住
        已有.建立(属性)#初始化
        return 已有.渲染()#画出

    def 建立(自身,属性):
        '先记下数据和开关，节点等渲染时再造'
        自身.属性=属性#槽位属性
        自身.展开=False#默认收起
        自身.已复制=False#复制反馈
        自身.定时=None#恢复图标
        自身.根=None#整行
        自身.指纹=None#上次画过的事实

    def 数据(自身):
        '聊天节点上的回复数据'
        return 自身.属性['node']['data']#展示数据

    def 渲染(自身):
        '第一次造整行。展开、复制或数据变了就重画气泡'
        窗口=自身.属性['window']#浏览器窗口
        文档=窗口.document#文档
        数据=自身.数据()#当前数据
        指纹=(数据.get('callId'),数据.get('text'),自身.展开,自身.已复制,数据.get('time'))#会改画面的事实
        if 自身.根 is None:#第一次
            根=模块节点(文档,'div',样式模块,'row')#整行
            根.setAttribute('data-question-reply',str(数据.get('callId')))#调用
            根.setAttribute('data-reply-outcome',str(数据.get('outcome')))#结果
            根.setAttribute('role','group')#一组
            根.setAttribute('aria-label','回答先前等待中的问题')#无障碍名
            泡=模块节点(文档,'div',样式模块,'bubble')#气泡
            根.appendChild(泡)#气泡进行
            动作=模块节点(文档,'div',样式模块,'actions')#时间与复制
            时间=模块节点(文档,'span',样式模块,'time')#时间
            动作.appendChild(时间)#时间
            复制钮=文档.createElement('button')#复制
            复制钮.type='button'#按钮
            设类(复制钮,'action')#复制按钮
            动作.appendChild(复制钮)#复制
            根.appendChild(动作)#动作进行
            注入模块样式文件(文档,'问题回复视图样式',样式路径,样式模块)#样式
            自身.根=根#留下
            自身.泡=泡#留下
            自身.时间=时间#留下
            自身.复制钮=复制钮#留下
            自身.复制钮.addEventListener('click',自身.点复制)#复制
            自身.提示=提示泡({'window':窗口,'label':'复制','side':'bottom','children':复制钮})#提示挂在按钮上
            自身.提示.渲染()#按钮仍是锚
        if 指纹!=自身.指纹 or 自身.泡.childNodes.length==0:#需要重画
            自身.指纹=指纹#记下
            自身.画气泡(窗口,文档,数据)#气泡
            自身.画动作(窗口,数据)#时间和复制
        if 'parent' in 自身.属性 and 自身.根.parentNode is not 自身.属性['parent']:#指定了父节点
            自身.属性['parent'].appendChild(自身.根)#挂上
        return 自身.根#节点

    def 画气泡(自身,窗口,文档,数据):
        '收起时只留标签和摘要。展开后列出每道题'
        while 自身.泡.firstChild is not None:#清掉旧内容
            自身.泡.removeChild(自身.泡.firstChild)#摘掉
        标签='回答先前等待中的问题'#气泡名
        开关文='收起问题详情' if 自身.展开 else '展开问题详情'#开关
        钮=文档.createElement('button')#开关
        钮.type='button'#按钮
        设类(钮,'toggle')#开关
        钮.setAttribute('aria-expanded','true' if 自身.展开 else 'false')#展开态
        钮.setAttribute('aria-label',标签+' · '+开关文)#无障碍名
        钮.addEventListener('click',自身.点开关)#切换
        行=模块节点(文档,'span',样式模块,'labelRow')#标签行
        尖=模块节点(文档,'span',样式模块,'caret')#箭头
        尖.setAttribute('aria-hidden','true')#不读
        if 自身.展开:#展开用下箭头
            尖.appendChild(图标下箭头描边常规({'window':窗口}))#下
        else:#收起用右箭头
            尖.appendChild(图标右chevron14({'window':窗口}))#右
        行.appendChild(尖)#箭头
        名=模块节点(文档,'span',样式模块,'label')#名称
        名.textContent=标签#名称
        行.appendChild(名)#名称
        钮.appendChild(行)#标签行
        if not 自身.展开:#收起时给摘要
            摘要值=[]#答案
            for 问题 in 数据.get('questions') or []:#逐题
                摘要值.extend(回复答案值(数据,问题.get('id')))#这题的值
            摘要文=', '.join(摘要值)#拼起来
            if 摘要文=='':#没有答案
                摘要文='已跳过'#跳过
            摘要=模块节点(文档,'span',样式模块,'summary')#摘要
            摘要.textContent=摘要文#摘要
            钮.appendChild(摘要)#摘要
        自身.泡.appendChild(钮)#开关
        if not 自身.展开:#收起就不列详情
            return
        问题表=数据.get('questions') or []#问题
        if len(问题表)==0:#读不懂
            文=文档.createElement('p')#原文
            设类(文,'text')#原文
            文.textContent=数据.get('text') or ''#模型文本
            自身.泡.appendChild(文)#原文
            return
        列表=文档.createElement('dl')#详情
        设类(列表,'details')#详情
        for 问题 in 问题表:#逐题
            块=文档.createElement('div')#一题
            标样式模块(块,样式模块)#模块
            题=文档.createElement('dt')#问题
            设类(题,'question')#问题
            眉=问题.get('header')#眉题
            if isinstance(眉,str) and 眉!='' and 眉!=问题.get('question'):#眉题和题干不同
                眉节=模块节点(文档,'span',样式模块,'header')#眉题
                眉节.textContent=眉#眉题
                题.appendChild(眉节)#眉题
            题干=模块节点(文档,'span',样式模块,'questionText')#题干
            题干.textContent=问题.get('question') or ''#题干
            题.appendChild(题干)#题干
            if isinstance(问题.get('detail'),str) and 问题['detail']!='':#有细节
                细节=模块节点(文档,'span',样式模块,'detail')#细节
                细节.textContent=问题['detail']#细节
                题.appendChild(细节)#细节
            选项=问题.get('options')#选项
            if isinstance(选项,list) and len(选项)>0:#有选项
                单=文档.createElement('ul')#选项
                设类(单,'options')#选项
                for 选项项 in 选项:#逐项
                    条=文档.createElement('li')#一项
                    标样式模块(条,样式模块)#模块
                    说明=选项项.get('description')#说明
                    if isinstance(说明,str) and 说明!='':#有说明
                        条.textContent=选项项.get('label','')+' — '+说明#标签和说明
                    else:#只有标签
                        条.textContent=选项项.get('label','')#标签
                    单.appendChild(条)#一项
                题.appendChild(单)#选项
            块.appendChild(题)#问题
            答=文档.createElement('dd')#答案
            设类(答,'answer')#答案
            答标=模块节点(文档,'span',样式模块,'answerLabel')#答案标签
            答标.textContent='回答：'#标签
            答.appendChild(答标)#标签
            值=回复答案值(数据,问题.get('id'))#这题的值
            if len(值)==0:#跳过
                答.appendChild(文档.createTextNode('已跳过'))#跳过
            else:#有答案
                答.appendChild(文档.createTextNode(', '.join(值)))#答案
            块.appendChild(答)#答案
            列表.appendChild(块)#一题
        自身.泡.appendChild(列表)#详情

    def 画动作(自身,窗口,数据):
        '时间和复制。已复制时换成勾和「复制成功」'
        格式=窗口.Intl.DateTimeFormat(窗口.navigator.language,{'hour':'2-digit','minute':'2-digit','hour12':False})#时分
        自身.时间.textContent=格式.format(数据.get('time'))#时间
        文案='复制成功' if 自身.已复制 else '复制'#提示
        while 自身.复制钮.firstChild is not None:#清掉旧图标
            自身.复制钮.removeChild(自身.复制钮.firstChild)#摘掉
        if 自身.已复制:#已复制
            自身.复制钮.appendChild(图标勾描边常规({'window':窗口}))#勾
        else:#还没复制
            自身.复制钮.appendChild(图标复制描边常规({'window':窗口}))#复制
        自身.复制钮.setAttribute('aria-label',文案)#无障碍名
        自身.提示.属性['label']=文案#悬停时再读

    def 点开关(自身,_事件=None):
        '展开或收起详情'
        自身.展开=not 自身.展开#反过来
        自身.指纹=None#强制重画
        自身.渲染()#重画

    def 点复制(自身,_事件=None):
        '把每道题和答案写入剪贴板。气泡开没开都不影响文本'
        if 自身.已复制:#这一秒里不再写
            return
        数据=自身.数据()#当前数据
        问题表=数据.get('questions') or []#问题
        if len(问题表)==0:#读不懂
            文本=数据.get('text') or ''#模型文本
        else:#按展开后的样子
            块表=[]#每题一块
            for 问题 in 问题表:#逐题
                值=回复答案值(数据,问题.get('id'))#答案
                眉=问题.get('header')#眉题
                if isinstance(眉,str) and 眉!='' and 眉!=问题.get('question'):#眉题和题干不同
                    标题=眉+' — '+str(问题.get('question') or '')#眉题加题干
                else:#只用题干
                    标题=str(问题.get('question') or '')#题干
                if len(值)==0:#跳过
                    答案='已跳过'#跳过
                else:#有答案
                    答案='回答：'+', '.join(值)#标签加答案
                块表.append(标题+'\n'+答案)#一块
            文本='\n\n'.join(块表)#题与题之间空行
        if 写剪贴板(文本) is not True:#宿主没接受
            return
        自身.已复制=True#换成勾
        自身.指纹=None#重画复制钮
        自身.渲染()#重画
        窗口=自身.属性['window']#窗口
        if 自身.定时 is not None:#清掉上一次
            窗口.clearTimeout(自身.定时)#清掉
        def 恢复():
            '一秒后回到复制图标'
            自身.已复制=False#恢复
            自身.定时=None#清掉
            自身.指纹=None#重画
            自身.渲染()#重画
        自身.定时=窗口.setTimeout(恢复,1000)#一秒


class 问题回复视图:
    '聊天节点上的迟到回复。画面由气泡负责'
    def __new__(类,属性=None):
        '槽位调用时直接交出气泡节点'
        return 问题回复气泡.呈现(属性)#气泡
