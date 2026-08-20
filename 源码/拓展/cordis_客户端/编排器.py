"""页侧运行编排：审批、对账与活动图。

对齐上游 `cordis-client-runner/src/client/orchestrator.ts`。公开面仅中文名。
inFlight 按插件串行；orchestrate/drive 收尾在 finally 清活动；决议只走 answer/settle。
evaluate/Loader 真挂载仍属硬缺口，本叶不冒充 Function/React。
"""
from .运行时 import 可观察,错误字段#可观察与错误

__all__=[#仅中文公开名
    '活动阶段','失败原因','同一请求','运行编排器','说明',
]#公开面结束

说明='inFlight 串行；drive 收尾收敛；evaluate/Loader 真挂载仍欠 runner 硬缺口。'#说明

活动阶段=('awaiting-approval','orchestrating')#阶段
失败原因=('host-half-failed','client-half-failed')#失败半

def 同一请求(左,右):#请求是否同一份
    """对齐 sameRequest。"""
    if 左 is None:#无左
        return False#否
    return (左.get('requestId')==右.get('requestId')
            and 左.get('agentId')==右.get('agentId')
            and 左.get('pluginId')==右.get('pluginId')
            and 左.get('packageId')==右.get('packageId')
            and 左.get('mode')==右.get('mode')
            and 左.get('name')==右.get('name')
            and 左.get('purpose')==右.get('purpose')
            and 左.get('requiresApproval')==右.get('requiresApproval'))#全等

class 运行编排器:#CordisRunOrchestrator
    """活动/失败图、打开审批、对账、关闭、批准、拒绝；inFlight 按插件串行。"""
    def __init__(自身,环境=None):#构造
        """env：runner + host（runHostHalf/getClientCode/resolveRequestRun/settleUserRun）。"""
        自身.环境=环境 or {}#环境
        自身.请求={}#requestId → 请求
        自身.活动={}#pluginId → 活动
        自身.失败={}#pluginId → 失败
        自身.进行中={}#pluginId → attempt 盒（inFlight）
        自身._听=set()#订阅
        自身._活动缓存=None#快照缓存
        自身._失败缓存=None#失败快照

    def observe(自身,函数):#订阅
        """退订器。"""
        自身._听.add(函数)#加
        def 退():#退
            """拿掉。"""
            自身._听.discard(函数)#删
        return 退#器

    def commit(自身):#通知
        """作废缓存并广播。"""
        自身._活动缓存=None#失效
        自身._失败缓存=None#失效
        for 函数 in list(自身._听):#逐个
            函数()#唤

    @property
    def activeRuns(自身):#活动可观察
        """活动图。"""
        def 读():#惰性
            """拷贝。"""
            if 自身._活动缓存 is None:#惰性
                自身._活动缓存=dict(自身.活动)#拷
            return 自身._活动缓存#缓存
        return 可观察(读)#图

    @property
    def lastRunError(自身):#失败可观察
        """失败图。"""
        def 读():#惰性
            """拷贝。"""
            if 自身._失败缓存 is None:#惰性
                自身._失败缓存=dict(自身.失败)#拷
            return 自身._失败缓存#缓存
        return 可观察(读)#图

    def open(自身,请求):#打开请求
        """登记；已授权则立刻编排（对齐 void orchestrate().catch）。"""
        自身.请求[请求['requestId']]=请求#记下
        if not 请求.get('requiresApproval'):#已授权
            计划={#立刻编排
                'agentId':请求['agentId'],'pluginId':请求['pluginId'],
                'packageId':请求['packageId'],'mode':请求['mode'],
                'requestId':请求['requestId'],'hasClientHalf':True,
            }#计划
            try:#自动激活失败只记日志
                自身._编排(计划)#串行
            except Exception as 错误:#对齐 .catch(console.error)
                print('[cordis-client-runner] automatic activation',请求['requestId'],'failed:',错误)#日志
            return#已启动
        现=自身.活动.get(请求['pluginId'])#当前
        if 现 is None or 现.get('phase')!='orchestrating':#没在编排
            自身.活动[请求['pluginId']]={#等待审批
                'phase':'awaiting-approval','requestId':请求['requestId'],
                'agentId':请求['agentId'],'packageId':请求['packageId'],
                'mode':请求['mode'],'name':请求['name'],'purpose':请求['purpose'],
            }#结束
        自身.commit()#通知

    def close(自身,请求标识):#关闭请求
        """他页落定或取消。"""
        请求=自身.请求.pop(请求标识,None)#拿掉
        if 请求 is None:#没有
            return#停
        现=自身.活动.get(请求['pluginId'])#当前
        if 现 and 现.get('phase')=='awaiting-approval' and 现.get('requestId')==请求标识:#正等
            自身.活动.pop(请求['pluginId'],None)#清
        自身.commit()#通知

    def reconcileApprovals(自身,行们):#对账审批
        """从权威库存重建挂起审批。"""
        期望={}#应有
        for 行 in 行们 or []:#每行
            尝试=行.get('latestRun')#最近
            if 尝试 is None:#无
                continue#跳
            批=尝试.get('approvalRequestId')#审批 id
            态=尝试.get('status')#状态
            if 批 is None or 态 not in ('awaiting-approval','starting-host','client-pending'):#无关
                continue#跳
            包=None#对应包
            for 候选 in 行.get('packages') or []:#找
                if 候选.get('packageId')==尝试.get('packageId'):#命中
                    包=候选#记下
                    break#停
            if 包 is None:#包没了
                continue#跳
            期望[批]={#重建
                'requestId':批,'agentId':行.get('agentId'),'pluginId':行.get('pluginId'),
                'packageId':尝试.get('packageId'),'mode':尝试.get('mode'),
                'name':包.get('name'),'purpose':包.get('purpose'),
                'requiresApproval':尝试.get('requiresApproval',态=='awaiting-approval'),
            }#结束
        变了=False#变更
        for 标识,请求 in list(自身.请求.items()):#本地
            if 标识 in 期望:#仍有
                continue#跳
            自身.请求.pop(标识,None)#过期
            现=自身.活动.get(请求['pluginId'])#活动
            if 现 and 现.get('phase')=='awaiting-approval' and 现.get('requestId')==标识:#正等
                自身.活动.pop(请求['pluginId'],None)#清
            变了=True#变
        for 标识,请求 in 期望.items():#应有
            旧=自身.请求.get(标识)#旧
            现=自身.活动.get(请求['pluginId'])#活动
            if not 请求.get('requiresApproval') and 现 and 现.get('phase')=='orchestrating':#已编排
                continue#跳
            if (请求.get('requiresApproval') and 同一请求(旧,请求)
                and 现 and 现.get('phase')=='awaiting-approval' and 现.get('requestId')==标识):#未变
                continue#跳
            if not 请求.get('requiresApproval'):#自动
                自身.open(请求)#打开
                变了=True#变
                continue#下
            自身.请求[标识]=请求#写入
            if 现 is None or 现.get('phase')!='orchestrating':#展示审批
                自身.活动[请求['pluginId']]={#等待
                    'phase':'awaiting-approval','requestId':标识,
                    'agentId':请求['agentId'],'packageId':请求['packageId'],
                    'mode':请求['mode'],'name':请求['name'],'purpose':请求['purpose'],
                }#结束
            变了=True#变
        if 变了:#有变更
            自身.commit()#通知

    def approve(自身,请求标识,批后续=False):#批准
        """进入编排串行；对齐 Promise<void>。"""
        请求=自身.请求.get(请求标识)#取出
        if 请求 is None or not 请求.get('requiresApproval'):#不可答或已授权路径
            return#空
        计划={#编排计划
            'agentId':请求['agentId'],'pluginId':请求['pluginId'],
            'packageId':请求['packageId'],'mode':请求['mode'],
            'requestId':请求标识,'approveFutureVersions':批后续,'hasClientHalf':True,
        }#计划
        自身._编排(计划)#串行

    def decline(自身,请求标识):#拒绝
        """清活动并经 host.resolveRequestRun 回答。"""
        请求=自身.请求.get(请求标识)#取出
        if 请求 is None or not 请求.get('requiresApproval'):#不可答
            return#空
        现=自身.活动.get(请求['pluginId'])#活动
        if 现 is None or 现.get('phase')!='awaiting-approval' or 现.get('requestId')!=请求标识:#不是这条
            return#空
        自身.请求.pop(请求标识,None)#拿掉
        自身.活动.pop(请求['pluginId'],None)#清
        自身.commit()#通知
        自身._回答(请求标识,{'ok':False,'reason':'rejected'})#告诉宿主拒绝

    def startUserRun(自身,请求):#用户启动
        """编排串行；手势即授权。"""
        计划=dict(请求)#浅拷
        if 'hasClientHalf' not in 计划:#缺省
            计划['hasClientHalf']=True#有半
        自身._编排(计划)#串行

    def _编排(自身,计划):#orchestrate：inFlight 串行；收尾在 finally
        """同插件复用进行中 attempt；结束必清 inFlight + orchestrating。"""
        插件=计划['pluginId']#插件
        飞=自身.进行中.get(插件)#已在飞
        if 飞 is not None:#对齐 return running
            return 飞#复用同一次（不启第二趟）
        盒={'done':False}#attempt 盒（同步 Promise 占位）
        自身.进行中[插件]=盒#记下进行中
        自身.活动[插件]={#标编排中
            'phase':'orchestrating','agentId':计划['agentId'],
            'packageId':计划['packageId'],'mode':计划['mode'],
        }#结束
        自身.失败.pop(插件,None)#清旧失败
        if 计划.get('requestId') is not None:#审批进入执行
            自身.请求.pop(计划['requestId'],None)#拿掉
        自身.commit()#通知
        try:#驱动两半
            自身._驱动(计划)#drive（void）
        finally:#对齐 attempt.finally
            盒['done']=True#落定
            自身.进行中.pop(插件,None)#拿掉进行中
            自身.活动.pop(插件,None)#清 orchestrating
            自身.commit()#通知
        return 盒#本次 attempt

    def _取宿主(自身):#env.host 接缝
        """折好的宿主 RPC 操作表。"""
        宿主=自身.环境.get('host') if isinstance(自身.环境,dict) else None#接缝
        return 宿主 if isinstance(宿主,dict) else {}#表

    def _取运行器(自身):#env.runner
        """页本地客户端加载器。"""
        return 自身.环境.get('runner') if isinstance(自身.环境,dict) else None#运行器

    def _启动宿主(自身,计划):#startHost
        """调用 host.runHostHalf；接缝抛错折成 {ok:false,...错误字段}。"""
        跑=自身._取宿主().get('runHostHalf')#动词
        try:#远程启动
            return 跑(#对齐六参；无审批 id 传 None
                计划['agentId'],计划['pluginId'],计划['packageId'],计划['mode'],
                计划.get('requestId'),计划.get('approveFutureVersions',False),
            )#结束
        except Exception as 错误:#接缝抛错（含缺动词）
            return {'ok':False,**错误字段(错误)}#折成失败

    def _回答(自身,请求标识,决议):#answer
        """调用 host.resolveRequestRun；失败只记日志不外抛。"""
        落定=自身._取宿主().get('resolveRequestRun')#宿主动词
        try:#远程落定
            落定(请求标识,决议)#应答
        except Exception as 错误:#失败只记日志
            print('[cordis-client-runner] answering run request',请求标识,'failed:',错误)#日志

    def _落定面板(自身,计划,决议):#settleDirect
        """调用 host.settleUserRun；宿主拒绝或抛错记 client-half-failed。"""
        落定=自身._取宿主().get('settleUserRun')#动词
        try:#远程落定
            响应=落定(计划['agentId'],计划['pluginId'],决议)#落定
            if isinstance(响应,dict) and not 响应.get('ok'):#宿主拒绝
                自身.fail(计划,'client-half-failed',响应)#记失败
        except Exception as 错误:#接缝抛错
            自身.fail(计划,'client-half-failed',错误字段(错误))#记下

    def _客户端失败收尾(自身,计划,运行标识,本页启动,失败,原始错误=None):#finishClientFailure
        """记失败并按模型/面板路径回答或落定。"""
        print(#对齐 console.error
            '[cordis-client-runner] Client activation',
            计划.get('pluginId'),'/',计划.get('packageId'),'(',运行标识,') failed:',
            原始错误 if 原始错误 is not None else 失败,
        )#日志
        自身.fail(计划,'client-half-failed',失败)#页侧失败
        决议={#失败决议
            'ok':False,'reason':'client-half-failed',
            'pluginRunId':运行标识,'startedHere':本页启动,
            **失败,#消息与栈
        }#结束
        if 计划.get('requestId') is not None:#模型路径
            自身._回答(计划['requestId'],决议)#回答审批
        else:#面板路径
            自身._落定面板(计划,决议)#落定

    def _驱动(自身,计划):#drive：宿主 → 取码 → load → answer/settle；void
        """对齐上游 drive；决议只走 answer/settle，不向外抛返回值当契约。"""
        已启动=自身._启动宿主(计划)#先宿主半
        if not isinstance(已启动,dict) or not 已启动.get('ok'):#宿主半失败
            自身.fail(计划,'host-half-failed',已启动 if isinstance(已启动,dict) else 错误字段(已启动))#记下
            if 计划.get('requestId') is not None:#模型路径要回答
                决议=dict(已启动) if isinstance(已启动,dict) else {'ok':False,**错误字段(已启动)}#基
                决议['reason']='host-half-failed'#带原因
                自身._回答(计划['requestId'],决议)#回答
            return#停
        if not 计划.get('hasClientHalf'):#仅宿主半
            return#结束
        运行标识=已启动.get('pluginRunId')#精确激活
        本页启动=bool(已启动.get('startedHere'))#是否本页启动
        取码=自身._取宿主().get('getClientCode')#取浏览器半
        try:#取码
            源码=取码(计划['agentId'],计划['pluginId'],运行标识)#按运行 id 取
        except Exception as 错误:#取码失败（含缺动词）
            自身._客户端失败收尾(计划,运行标识,本页启动,错误字段(错误),错误)#收尾
            return#停
        运行器=自身._取运行器()#页本地加载器
        try:#加载浏览器半
            半边={#对齐 load 入参
                'pluginId':源码.get('pluginId') if isinstance(源码,dict) else getattr(源码,'pluginId',None),
                'packageId':源码.get('packageId') if isinstance(源码,dict) else getattr(源码,'packageId',None),
                'pluginRunId':源码.get('pluginRunId') if isinstance(源码,dict) else getattr(源码,'pluginRunId',None),
                'agentId':计划['agentId'],#会话
                'name':源码.get('name') if isinstance(源码,dict) else getattr(源码,'name',None),
                'code':源码.get('code') if isinstance(源码,dict) else getattr(源码,'code',None),
            }#半边结束
            加载=运行器.load(半边)#加载
        except Exception as 错误:#求值/加载抛错 → evaluate 阶段失败形
            加载={'ok':False,'cause':'evaluate',**错误字段(错误),'error':错误}#折
        if not isinstance(加载,dict) or not 加载.get('ok'):#加载失败
            原因=加载.get('cause','evaluate') if isinstance(加载,dict) else 'evaluate'#阶段
            消息=加载.get('message','') if isinstance(加载,dict) else str(加载)#消息
            失败={'message':str(原因)+': '+str(消息)}#阶段加消息
            if isinstance(加载,dict) and isinstance(加载.get('stack'),str):#有栈
                失败['stack']=加载['stack']#带
            原始=加载.get('error') if isinstance(加载,dict) else 加载#原始
            自身._客户端失败收尾(计划,运行标识,本页启动,失败,原始)#收尾
            return#停
        决议={'ok':True,'pluginRunId':加载.get('pluginRunId')}#成功决议
        if 加载.get('waitingFor') is not None:#停等
            决议['waitingFor']=加载['waitingFor']#带
        if 计划.get('requestId') is not None:#模型路径
            自身._回答(计划['requestId'],决议)#回答审批
            return#停
        自身._落定面板(计划,决议)#面板路径落定

    def fail(自身,计划,原因,失败):#记下失败
        """页侧失败。"""
        字段=错误字段(失败) if not isinstance(失败,dict) or 'message' not in 失败 else 失败#字段
        自身.失败[计划['pluginId']]={'packageId':计划['packageId'],'reason':原因,**字段}#写
        自身.commit()#通知
