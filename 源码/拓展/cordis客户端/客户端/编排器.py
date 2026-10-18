from ....客户端.模块.客户端.通告 import 取握手窗口
from .运行时 import 错误字段#保住 message 与 stack
from .运行时 import 快照源#活动图和失败图


__all__=['运行编排器']


class 运行编排器:
    '审批和直接运行。宿主半先于客户端半。同一插件的进行中运行串行'
    def __init__(自身,环境):
        '环境里是页面加载器和折好的宿主操作'
        自身.环境=环境#runner 与 host
        自身.请求={}#审批标识到请求
        自身.活动={}#插件标识到活动
        自身.失败={}#插件标识到最近失败
        自身.进行中=set()#正在编排的插件
        自身._听=set()#订阅者
        自身._活动缓存=None#两次提交之间不变
        自身._失败缓存=None#两次提交之间不变
        def 读活动():
            '活动图'
            if 自身._活动缓存 is None:#还没拍
                自身._活动缓存=dict(自身.活动)#拍一份
            return 自身._活动缓存
        def 读失败():
            '失败图'
            if 自身._失败缓存 is None:#还没拍
                自身._失败缓存=dict(自身.失败)#拍一份
            return 自身._失败缓存
        自身.activeRuns=快照源(读活动,自身.观察)#进行中的运行
        自身.lastRunError=快照源(读失败,自身.观察)#本页最近失败

    def 打开(自身,请求):
        '登记。已授权则立刻编排，失败只记日志'
        自身.请求[请求['requestId']]=请求#记下
        if not 请求['requiresApproval']:#不用审批
            try:#自动编排
                自身.编排({#计划
                    'agentId':请求['agentId'],
                    'pluginId':请求['pluginId'],
                    'packageId':请求['packageId'],
                    'mode':请求['mode'],
                    'requestId':请求['requestId'],
                    'hasClientHalf':True,
                })
            except Exception as 原因:#自动失败只记日志
                取握手窗口().console.error(
                    '[cordis-client-runner] automatic activation '+请求['requestId']+' failed:',原因,
                )
            return
        当前=自身.活动.get(请求['pluginId'])#当前活动
        if 当前 is None or 当前.get('phase')!='orchestrating':#没有正在编排
            自身.活动[请求['pluginId']]={#等审批
                'phase':'awaiting-approval',
                'requestId':请求['requestId'],
                'agentId':请求['agentId'],
                'packageId':请求['packageId'],
                'mode':请求['mode'],
                'name':请求['name'],
                'purpose':请求['purpose'],
            }
        自身.提交()#通知

    def 对账审批(自身,行列表):
        '按宿主清单重建还没落定的审批'
        期望={}#应该还在的请求
        for 行 in 行列表:#逐行
            尝试=行.get('latestRun')#最近一次运行
            if 尝试 is None or 尝试.get('approvalRequestId') is None:#没有审批
                continue
            if 尝试.get('status') not in ('awaiting-approval','starting-host','client-pending'):#不是挂起
                continue
            包=None#对应包
            for 候选 in 行.get('packages') or []:#找包
                if 候选.get('packageId')==尝试.get('packageId'):#同一份
                    包=候选#命中
                    break
            if 包 is None:#清单里没有这个包
                continue
            需要审批=尝试.get('requiresApproval')#清单上的标记
            if 需要审批 is None:#没有标记就看状态
                需要审批=尝试.get('status')=='awaiting-approval'
            期望[尝试['approvalRequestId']]={#重建请求
                'requestId':尝试['approvalRequestId'],
                'agentId':行['agentId'],
                'pluginId':行['pluginId'],
                'packageId':尝试['packageId'],
                'mode':尝试['mode'],
                'name':包['name'],
                'purpose':包['purpose'],
                'requiresApproval':需要审批,
            }
        变了=False#要不要通知
        for 请求标识,请求 in list(自身.请求.items()):#清掉清单里没有的
            if 请求标识 in 期望:#还在
                continue
            del 自身.请求[请求标识]#摘掉
            当前=自身.活动.get(请求['pluginId'])#当前活动
            if 当前 is not None and 当前.get('phase')=='awaiting-approval' and 当前.get('requestId')==请求标识:#是这一份等待
                del 自身.活动[请求['pluginId']]#摘掉等待
            变了=True#要通知
        for 请求标识,请求 in 期望.items():#补上或更新
            先前=自身.请求.get(请求标识)#已有请求
            当前=自身.活动.get(请求['pluginId'])#当前活动
            if not 请求['requiresApproval'] and 当前 is not None and 当前.get('phase')=='orchestrating':#正在编排
                continue
            if 请求['requiresApproval'] and 先前 is not None and 先前.get('requestId')==请求.get('requestId') and 先前.get('agentId')==请求.get('agentId') and 先前.get('pluginId')==请求.get('pluginId') and 先前.get('packageId')==请求.get('packageId') and 先前.get('mode')==请求.get('mode') and 先前.get('name')==请求.get('name') and 先前.get('purpose')==请求.get('purpose') and 先前.get('requiresApproval')==请求.get('requiresApproval') and 当前 is not None and 当前.get('phase')=='awaiting-approval' and 当前.get('requestId')==请求标识:#没有变化
                continue
            if not 请求['requiresApproval']:#该自动跑
                自身.打开(请求)#走打开
                变了=True#要通知
                continue
            自身.请求[请求标识]=请求#更新请求
            if 当前 is None or 当前.get('phase')!='orchestrating':#没有正在编排
                自身.活动[请求['pluginId']]={#等审批
                    'phase':'awaiting-approval',
                    'requestId':请求标识,
                    'agentId':请求['agentId'],
                    'packageId':请求['packageId'],
                    'mode':请求['mode'],
                    'name':请求['name'],
                    'purpose':请求['purpose'],
                }
            变了=True#要通知
        if 变了:#有变化
            自身.提交()#通知

    def 关闭(自身,请求标识):
        '别的页落定或取消。未知标识是空操作'
        请求=自身.请求.get(请求标识)#本页的请求
        if 请求 is None:#没有
            return
        del 自身.请求[请求标识]#摘掉
        当前=自身.活动.get(请求['pluginId'])#当前活动
        if 当前 is not None and 当前.get('phase')=='awaiting-approval' and 当前.get('requestId')==请求标识:#是这一份等待
            del 自身.活动[请求['pluginId']]#摘掉等待
        自身.提交()#通知

    def 批准(自身,请求标识,批后续):
        '批准并编排。未知或已落定是空操作'
        请求=自身.请求.get(请求标识)#本页的请求
        if 请求 is None or not 请求['requiresApproval']:#不能批
            return None
        return 自身.编排({#进入编排
            'agentId':请求['agentId'],
            'pluginId':请求['pluginId'],
            'packageId':请求['packageId'],
            'mode':请求['mode'],
            'requestId':请求标识,
            'approveFutureVersions':批后续,
            'hasClientHalf':True,
        })

    def 拒绝(自身,请求标识):
        '拒绝。不跑任何一半。未知或已落定是空操作'
        请求=自身.请求.get(请求标识)#本页的请求
        if 请求 is None or not 请求['requiresApproval']:#不能拒
            return
        当前=自身.活动.get(请求['pluginId'])#当前活动
        if 当前 is None or 当前.get('phase')!='awaiting-approval' or 当前.get('requestId')!=请求标识:#不是这一份等待
            return
        del 自身.请求[请求标识]#摘掉
        del 自身.活动[请求['pluginId']]#摘掉等待
        自身.提交()#通知
        自身.回答(请求标识,{'ok':False,'reason':'rejected'})#回答宿主

    def 启动用户运行(自身,请求):
        '用户自己启动。手势就是授权'
        return 自身.编排(请求)#编排

    def 观察(自身,函数):
        '订阅。返回退订'
        自身._听.add(函数)#记下
        def 退订():
            '拿掉这个订阅'
            自身._听.discard(函数)#摘掉
        return 退订

    def 提交(自身):
        '作废缓存并通知'
        自身._活动缓存=None#下次重拍
        自身._失败缓存=None#下次重拍
        for 函数 in list(自身._听):#复制后再通知
            函数()#通知

    def 编排(自身,计划):
        '同一插件复用进行中的那次。结束时清进行中和 orchestrating'
        if 计划['pluginId'] in 自身.进行中:#已经在编排
            return None
        自身.进行中.add(计划['pluginId'])#占住
        自身.活动[计划['pluginId']]={#编排中
            'phase':'orchestrating',
            'agentId':计划['agentId'],
            'packageId':计划['packageId'],
            'mode':计划['mode'],
        }
        自身.失败.pop(计划['pluginId'],None)#清掉旧失败
        if 计划.get('requestId') is not None:#有审批
            自身.请求.pop(计划['requestId'],None)#离开审批表
        自身.提交()#通知
        try:#驱动
            自身.驱动(计划)#宿主然后客户端
        finally:#无论成败
            自身.进行中.discard(计划['pluginId'])#放开
            自身.活动.pop(计划['pluginId'],None)#离开编排
            自身.提交()#通知
        return None

    def 驱动(自身,计划):
        '宿主半、取码、加载，然后回答或落定'
        启动=自身.启动宿主(计划)#宿主半
        if not 启动['ok']:#宿主失败
            自身.记下失败(计划,'host-half-failed',启动)#记下
            if 计划.get('requestId') is not None:#模型路径
                回答=dict(启动)#带上失败字段
                回答['reason']='host-half-failed'#原因
                自身.回答(计划['requestId'],回答)#回答
            return
        if not 计划['hasClientHalf']:#只有宿主半
            return
        try:#取浏览器半源码
            源=自身.环境['host']['getClientCode'](计划['agentId'],计划['pluginId'],启动['pluginRunId'])#源码
        except Exception as 原因:#取码失败
            自身.客户端失败收尾(计划,启动['pluginRunId'],启动['startedHere'],错误字段(原因),原因)#收尾
            return
        try:#加载到本页
            已加载=自身.环境['runner'].load({#半边
                'pluginId':源['pluginId'],
                'packageId':源['packageId'],
                'pluginRunId':源['pluginRunId'],
                'agentId':计划['agentId'],
                'name':源['name'],
                'code':源['code'],
            })
        except Exception as 原因:#加载抛错当成求值失败
            字段=错误字段(原因)#消息和栈
            已加载={'ok':False,'cause':'evaluate','error':原因}#失败结果
            已加载.update(字段)#叠上字段
        if not 已加载['ok']:#客户端半失败
            失败={'message':已加载['cause']+': '+已加载['message']}#阶段加消息
            if 'stack' in 已加载:#有栈
                失败['stack']=已加载['stack']#带上
            自身.客户端失败收尾(计划,启动['pluginRunId'],启动['startedHere'],失败,已加载.get('error'))#收尾
            return
        决议={'ok':True,'pluginRunId':已加载['pluginRunId']}#成功
        if 'waitingFor' in 已加载:#还在等服务
            决议['waitingFor']=已加载['waitingFor']#带上
        if 计划.get('requestId') is not None:#模型路径
            自身.回答(计划['requestId'],决议)#回答
            return
        自身.落定面板(计划,决议)#面板路径

    def 启动宿主(自身,计划):
        '跑宿主半。接缝抛错折成失败结果'
        try:#调用
            return 自身.环境['host']['runHostHalf'](#宿主半
                计划['agentId'],计划['pluginId'],计划['packageId'],计划['mode'],
                计划['requestId'] if 计划.get('requestId') is not None else None,
                计划['approveFutureVersions'] if 计划.get('approveFutureVersions') is not None else False,
            )
        except Exception as 原因:#折成失败
            结果={'ok':False}#失败
            结果.update(错误字段(原因))#消息和栈
            return 结果

    def 客户端失败收尾(自身,计划,运行标识,本页启动,失败,原始错误=None):
        '记下客户端失败，并按模型或面板路径回答'
        取握手窗口().console.error(#留在控制台
            '[cordis-client-runner] Client activation '+计划['pluginId']+'/'+计划['packageId']+' ('+str(运行标识)+') failed:',
            原始错误 if 原始错误 is not None else 失败,
        )
        自身.记下失败(计划,'client-half-failed',失败)#记下
        决议={'ok':False,'reason':'client-half-failed','pluginRunId':运行标识,'startedHere':本页启动}#决议
        决议.update(失败)#消息和栈
        if 计划.get('requestId') is not None:#模型路径
            自身.回答(计划['requestId'],决议)#回答
            return
        自身.落定面板(计划,决议)#面板路径

    def 落定面板(自身,计划,决议):
        '落定面板运行。宿主拒绝或抛错记成客户端半失败'
        try:#调用
            响应=自身.环境['host']['settleUserRun'](计划['agentId'],计划['pluginId'],决议)#落定
            if not 响应['ok']:#宿主拒绝
                自身.记下失败(计划,'client-half-failed',响应)#记下
        except Exception as 原因:#抛错也记
            自身.记下失败(计划,'client-half-failed',错误字段(原因))#记下

    def 回答(自身,请求标识,决议):
        '回答审批。失败只记日志'
        try:#调用
            自身.环境['host']['resolveRequestRun'](请求标识,决议)#回答
        except Exception as 原因:#回答失败不外抛
            取握手窗口().console.error(
                '[cordis-client-runner] answering run request '+str(请求标识)+' failed:',原因,
            )

    def 记下失败(自身,计划,原因,失败):
        '记下本页失败并通知'
        记录={'packageId':计划['packageId'],'reason':原因}#原因
        记录.update(失败)#消息和栈
        自身.失败[计划['pluginId']]=记录#写下
        自身.提交()#通知
