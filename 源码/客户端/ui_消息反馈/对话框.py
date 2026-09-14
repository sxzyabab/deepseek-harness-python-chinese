from ...客户端.存储 import 创建快照存储#快照存储

__all__=['反馈对话框控制器','关闭草稿']#仅中文公开名

关闭草稿={'target':None,'category':None,'text':'','submitting':False,'failure':None}#关闭草稿（无 toast）

class 反馈对话框控制器:#按会话对话框控制器
    """一份实例支撑覆盖层入口与每个消息控件。"""
    def __init__(自身,提交):
        """提交接收 (目标, 条目) 并返回动作结果 dict。"""
        自身._提交=提交#提交函数
        初始=dict(关闭草稿)#拷贝
        初始['toast']=0#无轻提示
        自身.状态=创建快照存储(初始)#状态存储
        自身._代数=0#代数
        自身._轻提示序号=0#轻提示序号

    def 打开(自身,目标):#打开
        """以空草稿打开，替换任何已打开草稿。"""
        自身._代数+=1#换代
        下一=dict(关闭草稿)#空草稿
        下一['target']=目标#目标
        下一['toast']=自身.状态.getSnapshot()['toast']#保留 toast
        自身.状态.set(下一)#发布

    def 关闭(自身):#关闭
        """关闭对话框并丢弃草稿；屏幕上的轻提示保留。"""
        自身._代数+=1#换代
        下一=dict(关闭草稿)#空草稿
        下一['toast']=自身.状态.getSnapshot()['toast']#保留 toast
        自身.状态.set(下一)#发布

    def 编辑(自身,草稿):#编辑
        """在可编辑时替换草稿的一部分。草稿为 dict。"""
        当前=自身.状态.getSnapshot()#当前
        if 当前['target'] is None or 当前['submitting']:#关闭或提交中
            return#忽略
        下一=dict(当前)#拷贝
        下一.update(草稿)#合并
        自身.状态.set(下一)#发布

    def 提交草稿(自身):#提交草稿
        """提交草稿；空草稿也合法。成功关闭并拉起轻提示。"""
        当前=自身.状态.getSnapshot()#当前
        if 当前['target'] is None or 当前['submitting']:#关闭或提交中
            return#忽略
        代数=自身._代数#记下代数
        下一=dict(当前)#拷贝
        下一['submitting']=True#提交中
        下一['failure']=None#清失败
        自身.状态.set(下一)#发布
        正文=当前['text'].strip()#规范化
        条目={}#记录
        if len(正文)>0:#有正文
            条目['text']=正文#正文
        if 当前['category'] is not None:#有类别
            条目['category']=当前['category']#类别
        结果=自身._提交(当前['target'],条目)#提交
        if 'ok' in 结果 and 结果['ok']:#成功
            if 代数==自身._代数:#同代才关闭
                自身.关闭()#关闭
            自身.确认()#轻提示
            return#结束
        if 代数!=自身._代数:#草稿已换代
            return#遗弃
        现=dict(自身.状态.getSnapshot())#现状态
        现['submitting']=False#结束提交
        错误=结果['error'] if 'error' in 结果 else {}#错误
        现['failure']=错误['code'] if 'code' in 错误 else None#失败码
        现['toast']=0#清确认 toast
        自身.状态.set(现)#发布

    def 关掉失败(自身):#关掉失败提示
        """清掉当前失败轻提示，不关闭草稿。"""
        现=dict(自身.状态.getSnapshot())#现
        现['failure']=None#清失败
        自身.状态.set(现)#发布

    def 确认(自身):#确认轻提示
        """显示确认轻提示；已有则重启。"""
        自身._轻提示序号+=1#递增
        现=dict(自身.状态.getSnapshot())#现
        现['toast']=自身._轻提示序号#序号
        自身.状态.set(现)#发布

    def 退役轻提示(自身,序号):#退役轻提示
        """轻提示淡出后退役一份。"""
        现=自身.状态.getSnapshot()#现
        if 现['toast']==序号:#同序号
            下一=dict(现)#拷贝
            下一['toast']=0#清
            自身.状态.set(下一)#发布

    def 拆除(自身):#拆除
        """丢掉草稿与轻提示。"""
        自身._代数+=1#换代
        下一=dict(关闭草稿)#空
        下一['toast']=0#清 toast
        自身.状态.set(下一)#发布
