'一次登录里的赠金通知：同时只显示一张，一次只确认一笔'
from ...模块.客户端.通告 import 取握手窗口

__all__=['已过期','创建赠金须知控制器']

def 已过期(到期于,时刻):
    '解析不了的时间不算过期，通知仍然显示'
    窗口=取握手窗口()
    到期=窗口.Date.parse(到期于)
    if 到期!=到期:
        return False
    return 到期<=时刻

def 创建赠金须知控制器(选项):
    '读、显示和确认赠金。账号插件在登录和刷新时驱动它'
    范围盒={'当前':None}
    当前盒={'通知':None}
    读代盒={'值':0}
    定时盒={'值':None}
    确认中盒={'值':False}
    延迟盒={'值':选项['ackRetryDelayMs']}
    已报告=set()
    def 清定时():
        '清掉还没触发的确认'
        if 定时盒['值'] is not None:
            取握手窗口().clearTimeout(定时盒['值'])
            定时盒['值']=None
    def 设当前(通知):
        '同一笔订单和文案不重复发布。换订单就清掉已报告'
        现在=当前盒['通知']
        if 通知 is None and 现在 is None:
            return
        新单=通知.get('orderId') if isinstance(通知,dict) else None
        旧单=现在.get('orderId') if isinstance(现在,dict) else None
        新文=通知.get('message') if isinstance(通知,dict) else None
        旧文=现在.get('message') if isinstance(现在,dict) else None
        新期=通知.get('expiresAt') if isinstance(通知,dict) else None
        旧期=现在.get('expiresAt') if isinstance(现在,dict) else None
        if 新单==旧单 and 新文==旧文 and 新期==旧期:
            return
        if 新单!=旧单:
            已报告.clear()
        当前盒['通知']=通知
        选项['publish'](通知)
    def 安排确认(延迟):
        '到点再确认队首'
        清定时()
        def 到时():
            '定时到了就跑确认'
            跑确认()
        定时盒['值']=取握手窗口().setTimeout(到时,延迟)
    def 重置确认():
        '换账号或结束时丢掉上一轮确认'
        清定时()
        确认中盒['值']=False
        延迟盒['值']=选项['ackRetryDelayMs']
    def 开始确认():
        '有待确认的订单就立刻排一次'
        范围=范围盒['当前']
        if 范围 is not None and len(范围['pending'])>0:
            安排确认(0)
    def 应用(读时范围,批):
        '新订单换掉卡片。空批次只撤掉还没展示过的卡片'
        if 读时范围.get('accountId')!=批.get('accountId'):
            读时范围['accountId']=批.get('accountId')
            读时范围['pending'].clear()
            重置确认()
            设当前(None)
        候选=None
        赠金=批.get('bonuses') or []
        if len(赠金)>0:
            候选=赠金[0]
        if 候选 is None:
            现在=当前盒['通知']
            if 现在 is not None and 现在['orderId'] not in 已报告:
                设当前(None)
            return
        现在=当前盒['通知']
        if isinstance(现在,dict) and 候选.get('orderId')==现在.get('orderId'):
            设当前({
                'orderId':候选['orderId'],
                'message':候选['message'],
                'expiresAt':候选['expiresAt'],
            })
            return
        if 已过期(候选['expiresAt'],取握手窗口().Date.now()):
            return
        设当前({
            'orderId':候选['orderId'],
            'message':候选['message'],
            'expiresAt':候选['expiresAt'],
        })
    def 跑读取(读时范围):
        '只采用最新一次读取。失败不改现有卡片'
        读代盒['值']+=1
        代=读代盒['值']
        批=None
        try:
            批=选项['read']()
        except Exception:
            批=None
        if 范围盒['当前'] is not 读时范围 or 代!=读代盒['值']:
            return
        if 批 is not None:
            应用(读时范围,批)
    def 跑确认():
        '一笔一笔确认。协议失败就退避重试，明确拒绝则这轮不再试'
        读时范围=范围盒['当前']
        if 读时范围 is None or 确认中盒['值']:
            return
        账号标识=读时范围.get('accountId')
        待确认=读时范围['pending']
        订单标识=待确认[0] if len(待确认)>0 else None
        if 账号标识 is None or 订单标识 is None:
            return
        确认中盒['值']=True
        def 仍拥有():
            '这次调用还是不是当时的账号'
            return 范围盒['当前'] is 读时范围 and 读时范围.get('accountId')==账号标识
        try:
            已确认=选项['acknowledge'](账号标识,订单标识)
        except Exception:
            if 仍拥有() is not True:
                return
            确认中盒['值']=False
            安排确认(延迟盒['值'])
            延迟盒['值']=min(延迟盒['值']*2,选项['ackRetryMaxDelayMs'])
            return
        if 仍拥有() is not True:
            return
        确认中盒['值']=False
        if len(读时范围['pending'])>0 and 读时范围['pending'][0]==订单标识:
            读时范围['pending'].pop(0)
        延迟盒['值']=选项['ackRetryDelayMs']
        if 已确认 and len(读时范围['pending'])>0:
            安排确认(0)
        else:
            清定时()
    def 报告(订单标识):
        '展示过的订单放进确认队列'
        读时范围=范围盒['当前']
        现在=当前盒['通知']
        if 读时范围 is None or not isinstance(现在,dict) or 现在.get('orderId')!=订单标识 or 订单标识 in 已报告:
            return
        已报告.add(订单标识)
        if 订单标识 not in 读时范围['pending']:
            读时范围['pending'].append(订单标识)
        延迟盒['值']=选项['ackRetryDelayMs']
        安排确认(0)
    def 结束():
        '退出登录或卸下时丢掉卡片和确认'
        if 范围盒['当前'] is None:
            return
        重置确认()
        范围盒['当前']=None
        已报告.clear()
        设当前(None)
    def 开始():
        '同一轮登录再进入时保留卡片，并重新读一次'
        if 范围盒['当前'] is None:
            范围盒['当前']={'pending':[]}
        跑读取(范围盒['当前'])
    def 刷新():
        '设置页进入时再读一次。没有登录范围就直接结束'
        if 范围盒['当前'] is None:
            return
        开始确认()
        跑读取(范围盒['当前'])
    def 已展示(订单标识):
        '卡片画出一帧且还没过期才算展示'
        现在=当前盒['通知']
        if not isinstance(现在,dict) or 现在.get('orderId')!=订单标识:
            return
        if 已过期(现在['expiresAt'],取握手窗口().Date.now()):
            return
        报告(订单标识)
    def 关闭(订单标识):
        '用户关掉也算看过，先排队确认再撤下'
        现在=当前盒['通知']
        if not isinstance(现在,dict) or 现在.get('orderId')!=订单标识:
            return
        报告(订单标识)
        设当前(None)
    return {
        'begin':开始,
        'end':结束,
        'refresh':刷新,
        'shown':已展示,
        'dismiss':关闭,
    }
