import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['询问问题卡片']

样式模块='dsh-tool-ask-card'

def 确保样式(文档):
    '提问卡样式只插一次'
    注入模块样式文件(
        文档,
        'dsh-tool-ask-card',
        os.path.join(os.path.dirname(__file__),'询问问题卡片.module.css'),
        样式模块,
    )

def 元素(文档,标签,类名):
    '带官方类名和样式模块的节点'
    节点=文档.createElement(标签)
    节点.className=类名
    标样式模块(节点,样式模块)
    return 节点

class 询问问题卡片:
    '已回答或未回答的提问记录'
    def __new__(类,属性):
        '画出记录并返回节点'
        自身=object.__new__(类)
        自身.属性=属性 if isinstance(属性,dict) else {}
        return 自身.渲染()

    def 渲染(自身):
        '按 kind 画判定或问答'
        窗口=自身.属性['window']
        文档=窗口.document
        确保样式(文档)
        卡=自身.属性['card']
        if 卡['kind']=='unanswered':
            根=元素(文档,'div','card')
            判定=元素(文档,'p','verdict')
            判定.textContent=卡['verdict']
            根.appendChild(判定)
            列表=元素(文档,'ul','questionList')
            for 问题 in 卡['questions']:
                项=元素(文档,'li','unansweredQuestion')
                项.textContent=问题['question']
                列表.appendChild(项)
            根.appendChild(列表)
            return 根
        根=元素(文档,'dl','card')
        for 问题 in 卡['questions']:
            项=元素(文档,'div','item')
            问=元素(文档,'dt','question')
            问.textContent=问题['question']
            答=元素(文档,'dd','answer')
            if len(问题['answers'])==0:
                跳过=元素(文档,'span','skipped')
                跳过.textContent=卡['skippedLabel']
                答.appendChild(跳过)
            else:
                序=0
                for 答案 in 问题['answers']:
                    行=元素(文档,'span','answerLine')
                    行.textContent=答案
                    答.appendChild(行)
                    序=序+1
            项.appendChild(问)
            项.appendChild(答)
            根.appendChild(项)
        return 根
