from nicegui import ui as 界面
from ..异常 import 提问错误,页面失败文案#提问回执失败与页面失败句

__all__=['计划审阅面板','样式表']#仅中文公开名

样式表='''#对齐 PlanReviewPanel.module.css。类名加前缀，避免盖到提问卡
.plan-review{display:flex;justify-content:center;padding:6px calc(var(--dsh-composer-side-clearance) + 16px) 10px}
.plan-review-card{display:flex;overflow:hidden;flex-direction:column;width:100%;max-width:var(--dsh-chat-content-width);max-height:min(60vh,520px);border:1px solid var(--dsw-alias-state-warn-secondary);border-radius:20px;background:var(--dsw-specific-input-major);box-shadow:var(--dsw-shadow-lv2);color:var(--dsw-alias-label-primary);--dsh-scrollbar-thumb:var(--dsw-alias-scrollbar-bg-l2);--dsh-scrollbar-thumb-hover:var(--dsw-alias-scrollbar-hover-l2)}
.plan-review-card,.plan-review-card *{box-sizing:border-box}
.plan-review-strip{display:flex;align-items:center;flex-shrink:0;gap:8px;padding:10px 16px;background:var(--dsw-alias-state-warn-tertiary);color:var(--dsw-alias-state-warn-primary);font-size:13px;line-height:18px}
.plan-review-dot{width:8px;height:8px;border-radius:50%;background:var(--dsw-alias-state-warn-primary)}
.plan-review-body{flex:1 1 auto;min-height:0;overflow-y:auto;overscroll-behavior:contain;padding:12px 16px 4px;font-size:14px;line-height:22px}
.plan-review-footer{display:flex;align-items:center;justify-content:space-between;flex-shrink:0;gap:12px;padding:8px 16px 12px}
.plan-review-feedback{min-height:16px;color:var(--dsw-alias-state-error-primary);font-size:11px;line-height:16px}
.plan-review-actions{display:flex;align-items:center;flex-shrink:0;gap:8px}
.plan-review-discuss{gap:6px;color:var(--dsw-alias-label-secondary)}
.plan-review-discuss:hover:not(:disabled){color:var(--dsw-alias-label-primary)}
@media (max-width:720px){.plan-review-card{border-radius:16px}.plan-review-body{padding:10px 12px 4px}.plan-review-footer{align-items:flex-end;padding:8px 12px 10px}}
'''#样式表结束
界面.add_css(样式表,shared=True)

def 提示标题(说明):#可选 tooltip
    '选项描述有内容时返回 title 映射，否则空映射'
    if 说明 is None:#无描述
        return {}#不带 title
    return {'title':说明}#带上 tooltip

class 计划审阅面板:#计划审阅决策卡
    '把计划审阅渲染成决策卡；宿主 resolved 帧落地前二次点击不得重发'
    def __init__(自身,待答,审阅,翻译,渲染槽=None):#域面、收窄审阅、文案席与动作槽
        '记下提问域面、收窄后的审阅与翻译函数。父撰写器调用渲染，构造时不画'
        自身.待答=待答#提问域面
        自身.审阅=审阅#计划审阅
        自身.翻译=翻译#locale 翻译
        自身.渲染槽=渲染槽#计划动作槽
        自身.忙碌=False#一次性闩
        自身.错误=None#失败文案
        自身.画面=None#可反复清空的容器
        自身.画面失败=None

    def 结算(自身,发送):#带闩的发送
        '置忙碌、清错误；发送失败则重开闩并展示原因。answer/cancel 已在域面内等待'
        自身.忙碌=True#闩上
        自身.错误=None#清错误
        try:#投递
            发送()#域面已阻塞至回执
        except 提问错误 as 原因:#投递失败
            自身.忙碌=False#重开闩
            自身.错误=页面失败文案(原因)#展示原因，不带路径、用户名或环境变量

    def 裁决(自身,标签):#用选项标签作答
        '以提问者提供的选项标签回答该审阅'
        标识=自身.审阅['id']#问题 id
        def 发送():#投递单选
            '把批准或拒绝标签编成答案'
            自身.待答.answer({'answers':[{'id':标识,'selected':[标签]}]})#投递单选答案
        自身.结算(发送)#带闩发送

    def 讨论(自身):#取消等待回到聊天
        '以取消拒绝等待，让撰写器归位'
        def 发送():#投递取消
            '关闭本次提问请求'
            自身.待答.cancel()#投递取消
        自身.结算(发送)#带闩发送

    def 摘要(自身,计划):#标题与首段
        '取第一行作标题，其后第一段作说明'
        行列表=[]#非空行
        for 行 in str(计划).splitlines():#逐行
            文=行.strip()#去空白
            if 文.startswith('#'):#标题标记
                文=文.lstrip('#').strip()#去标记
            if 文!='':#有内容
                行列表.append(文)#收下
        if len(行列表)==0:#空计划
            return {'title':'','description':''}#空
        标题=行列表[0]#首行
        说明=''#首段
        if len(行列表)>1 and 行列表[1]!=标题:#次行且不重复
            说明=行列表[1]#说明
        return {'title':标题,'description':说明}#摘要

    def 渲染(自身):#决策卡
        '画出状态点、摘要、动作槽和决策按钮'
        拒绝=自身.审阅['decline'] if 'decline' in 自身.审阅 else None#可选拒绝选项
        批准=自身.审阅['approve']#批准选项
        摘要=自身.摘要(自身.审阅['plan'])#摘要
        旧=getattr(自身,'画面',None)#已有容器
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:#父级清掉容器后，把失败留在页面上
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('plan-review')#根
        自身.画面.clear()#再清一次
        def 讨论():
            '回到聊天后重画'
            自身.处理点击('discuss')#讨论
            自身.渲染()#重画
        def 拒绝本题():
            '拒绝计划后重画'
            自身.处理点击('decline')#拒绝
            自身.渲染()#重画
        def 批准本题():
            '批准计划后重画'
            自身.处理点击('approve')#批准
            自身.渲染()#重画
        with 自身.画面:#根
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            with 界面.column().classes('plan-review-card'):
                with 界面.row().classes('plan-review-strip'):#条
                    if 自身.忙碌 is True:#进行中
                        界面.spinner(size='sm')#进行中圆点
                    else:#待审
                        界面.html('<span class="plan-review-dot"></span>',sanitize=False)#警告圆点
                    界面.label(自身.翻译('plan.header'))#标题
                    if 自身.渲染槽 is not None:#动作槽自己在构造里画，这里不再调用渲染
                        自身.渲染槽('conversation.plan-review.actions',{'review':自身.审阅,'requestKey':自身.待答.key})
                with 界面.column().classes('plan-review-body'):
                    if 摘要['title']!='':#摘要标题
                        界面.label(摘要['title'])#标题
                    if 摘要['description']!='':#摘要说明
                        界面.label(摘要['description'])#说明
                    界面.markdown(自身.审阅['plan'])#计划正文
                with 界面.row().classes('plan-review-footer'):
                    if isinstance(自身.错误,str) and 自身.错误!='':#错误
                        界面.label(自身.错误).classes('plan-review-feedback')#错误
                    with 界面.row().classes('plan-review-actions'):
                        讨论钮=界面.button(自身.翻译('plan.discuss'), on_click=讨论).classes('plan-review-discuss')#要求修改
                        if 自身.忙碌 is True:#忙碌
                            讨论钮.disable()#禁
                        if 拒绝 is not None:#有拒绝
                            拒钮=界面.button(自身.翻译('plan.decline'), on_click=拒绝本题)#拒绝
                            说明=拒绝['description'] if 'description' in 拒绝 else None#说明
                            if isinstance(说明,str) and 说明!='':
                                拒钮.tooltip(说明)#提示
                            if 自身.忙碌 is True:#忙碌
                                拒钮.disable()#禁
                        准钮=界面.button(自身.翻译('plan.approve'), on_click=批准本题)#批准
                        批准说明=批准['description'] if 'description' in 批准 else None#说明
                        if isinstance(批准说明,str) and 批准说明!='':
                            准钮.tooltip(批准说明)#提示
                        if 自身.忙碌 is True:#忙碌
                            准钮.disable()#禁

    def 处理点击(自身,动作名):#按动作名分发
        '把结构树上的 onClick 名分发到裁决或讨论'
        if 动作名=='discuss':#去聊天
            自身.讨论()#取消
            return#已处理
        if 动作名=='decline':#拒绝
            拒绝=自身.审阅['decline'] if 'decline' in 自身.审阅 else None#拒绝选项
            if 拒绝 is not None:#仍有拒绝
                自身.裁决(拒绝['label'])#用拒绝标签作答
            return#已处理
        if 动作名=='approve':#批准
            自身.裁决(自身.审阅['approve']['label'])#用批准标签作答
