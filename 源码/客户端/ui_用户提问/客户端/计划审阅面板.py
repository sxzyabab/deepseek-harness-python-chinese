from .约定.槽位 import 提问错误#提问回执失败

__all__=['计划审阅面板','样式表']#仅中文公开名

样式表='''#对齐 PlanReviewPanel.module.css
.frame{display:flex;justify-content:center;padding:6px calc(var(--dsh-composer-side-clearance) + 16px) 10px}
.card{display:flex;overflow:hidden;flex-direction:column;width:100%;max-width:var(--dsh-chat-content-width);max-height:min(60vh,520px);border:1px solid var(--dsw-alias-state-warn-secondary);border-radius:20px;background:var(--dsw-specific-input-major);box-shadow:var(--dsw-shadow-lv2);color:var(--dsw-alias-label-primary);--dsh-scrollbar-thumb:var(--dsw-alias-scrollbar-bg-l2);--dsh-scrollbar-thumb-hover:var(--dsw-alias-scrollbar-hover-l2)}
.card,.card *{box-sizing:border-box}
.strip{display:flex;align-items:center;flex-shrink:0;gap:8px;padding:10px 16px;background:var(--dsw-alias-state-warn-tertiary);color:var(--dsw-alias-state-warn-primary);font-size:13px;line-height:18px}
.dot{width:8px;height:8px;border-radius:50%;background:var(--dsw-alias-state-warn-primary)}
.body{flex:1 1 auto;min-height:0;overflow-y:auto;overscroll-behavior:contain;padding:12px 16px 4px;font-size:14px;line-height:22px}
.footer{display:flex;align-items:center;justify-content:space-between;flex-shrink:0;gap:12px;padding:8px 16px 12px}
.feedback{min-height:16px;color:var(--dsw-alias-state-error-primary);font-size:11px;line-height:16px}
.actions{display:flex;align-items:center;flex-shrink:0;gap:8px}
.discuss{gap:6px;color:var(--dsw-alias-label-secondary)}
.discuss:hover:not(:disabled){color:var(--dsw-alias-label-primary)}
@media (max-width:720px){.card{border-radius:16px}.body{padding:10px 12px 4px}.footer{align-items:flex-end;padding:8px 12px 10px}}
'''#样式表结束

def 提示标题(说明):#可选 tooltip
    """选项描述有内容时返回 title 映射，否则空映射。"""
    if 说明 is None:#无描述
        return {}#不带 title
    return {'title':说明}#带上 tooltip

class 计划审阅面板:#计划审阅决策卡
    """把计划审阅渲染成决策卡；宿主 resolved 帧落地前二次点击不得重发。"""
    def __init__(自身,待答,审阅,翻译):#域面、收窄审阅与文案席
        """记下提问域面、收窄后的审阅与翻译函数。"""
        自身.待答=待答#提问域面
        自身.审阅=审阅#计划审阅
        自身.翻译=翻译#locale 翻译
        自身.忙碌=False#一次性闩
        自身.错误=None#失败文案

    def 结算(自身,发送):#带闩的发送
        """置忙碌、清错误；发送失败则重开闩并展示原因。answer/cancel 已在域面内等待。"""
        自身.忙碌=True#闩上
        自身.错误=None#清错误
        try:#投递
            发送()#域面已阻塞至回执
        except 提问错误 as 原因:#投递失败
            自身.忙碌=False#重开闩
            自身.错误=str(原因)#展示原因

    def 裁决(自身,标签):#用选项标签作答
        """以提问者提供的选项标签回答该审阅。"""
        标识=自身.审阅['id']#问题 id
        def 发送():#投递单选
            """把批准或拒绝标签编成答案。"""
            自身.待答.answer({'answers':[{'id':标识,'selected':[标签]}]})#投递单选答案
        自身.结算(发送)#带闩发送

    def 讨论(自身):#取消等待回到聊天
        """以取消拒绝等待，让撰写器归位。"""
        def 发送():#投递取消
            """关闭本次提问请求。"""
            自身.待答.cancel()#投递取消
        自身.结算(发送)#带闩发送

    def 渲染(自身):#决策卡结构树
        """返回计划审阅接管面的结构树。"""
        拒绝=自身.审阅['decline'] if 'decline' in 自身.审阅 else None#可选拒绝选项
        批准=自身.审阅['approve']#批准选项
        动作=[#动作行
            {'type':'button','variant':'ghost','class':'discuss','disabled':自身.忙碌,'onClick':'discuss','label':自身.翻译('plan.discuss')},#去聊天
        ]#动作起点
        if 拒绝 is not None:#有拒绝选项
            说明=拒绝['description'] if 'description' in 拒绝 else None#选项描述
            动作.append({#拒绝按钮
                'type':'button','variant':'outline','disabled':自身.忙碌,'onClick':'decline',#轮廓按钮
                'label':自身.翻译('plan.decline'),**提示标题(说明),#文案与 tooltip
            })#拒绝结束
        批准说明=批准['description'] if 'description' in 批准 else None#批准描述
        动作.append({#批准按钮
            'type':'button','variant':'primary','disabled':自身.忙碌,'onClick':'approve',#主按钮
            'label':自身.翻译('plan.approve'),**提示标题(批准说明),#文案与 tooltip
        })#批准结束
        错误子=[自身.错误] if 自身.错误 is not None else []#错误区子节点
        return {#结构树
            'type':'div','class':'frame','data-plan-review-key':自身.待答.key,#外框
            'children':[{#卡片
                'type':'section','class':'card','aria-label':自身.审阅['question'],#无障碍名用问题文本
                'children':[#卡片分区
                    {'type':'div','class':'strip','children':[{'type':'span','class':'dot'},自身.翻译('plan.header')]},#色带
                    {'type':'div','class':'body','data-plan-review-scroll':True,'children':[{'type':'MarkdownText','text':自身.审阅['plan']}]},#计划正文
                    {'type':'div','class':'footer','children':[#页脚
                        {'type':'div','class':'feedback','role':'status','children':错误子},#错误区
                        {'type':'div','class':'actions','children':动作},#动作行
                    ]},#页脚结束
                ],#分区结束
            }],#卡片结束
        }#结构树结束

    def 处理点击(自身,动作名):#按动作名分发
        """把结构树上的 onClick 名分发到裁决或讨论。"""
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
