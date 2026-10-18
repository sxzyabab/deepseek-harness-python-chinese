'把一次普通消息出现记成桌面产品事件'

__all__=['报告消息提交']

def 报告消息提交(上下文,提交):
    '不读更新的会话事实，只记这次发送'
    状态=提交.get('state')
    if 状态 is None:
        return
    模型=状态.get('model')
    属性={'run_mode':状态.get('runMode'),'msg_type':提交.get('mode') if 状态.get('running') else 'default'}
    if 状态.get('sessionId') is not None:
        属性['session_id']=状态['sessionId']
    if 模型 is not None:
        属性['model_name']=str(模型.get('provider'))+'/'+str(模型.get('name'))
        if 模型.get('effort') is not None:
            属性['thinking_effort']=模型['effort']
    分析=上下文.get('productAnalytics')
    if 分析 is None:
        return
    分析.track('send_button_click',属性,提交.get('timestamp'))
