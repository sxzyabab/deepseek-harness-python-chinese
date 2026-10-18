'有序的偏好写入，以及关掉设置面板后仍在的提示'
from ...存储 import 创建快照存储

__all__=['上传偏好']

class 上传偏好:
    '写入宿主设置，不先乐观改上传状态'
    def __init__(自身,表单):
        '记下宿主配置表单'
        自身.表单=表单
        自身.状态=创建快照存储({'busy':False,'notice':None,'sequence':0})

    def 设置启用(自身,启用):
        '持久化开关。拒绝或传输失败时仍显示已接受的值。'
        if 自身.状态.getSnapshot()['busy']:
            return
        def 开始(状态):
            '标忙并清掉旧提示'
            状态['busy']=True
            状态['notice']=None
        自身.状态.update(开始)
        已接受=False
        try:
            已接受=自身.表单.set('enabled',启用).等待()
        except Exception as 写入错误:
            '壳层提示报告失败写入，表单仍保留已接受的值'
            已接受=写入错误 is None
        def 结束(状态):
            '记下保存结果并抬高序号'
            状态['busy']=False
            if 已接受:
                状态['notice']='saved'
            else:
                状态['notice']='failed'
            状态['sequence']+=1
        自身.状态.update(结束)

    def 关掉提示(自身):
        '清掉正在显示的写入提示'
        def 清掉(状态):
            '去掉提示'
            状态['notice']=None
        自身.状态.update(清掉)
