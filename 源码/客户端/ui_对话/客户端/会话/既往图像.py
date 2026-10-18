'会话范围内的耐久图片地址缓存'
import base64
from ...异常 import 对话错误

__all__=['既往图像缓存']

class 既往图像缓存:
    '同一会话里的目标共用一次读取和同一个浏览器地址'
    def __init__(自身,上下文,会话面):
        '纤程结束时撤销地址'
        自身.会话面=会话面
        自身.条目={}
        自身.地址=set()
        自身.已拆=False
        def 清理():
            '拆掉全部地址'
            def 拆():
                '标记已拆并撤销'
                自身.拆掉()
            return 拆
        上下文.effect(清理,'ui-conversation historical image cache')

    def 解析(自身,会话标识,附件):
        '读耐久字节并做成可显示的地址'
        if 自身.已拆:
            raise 对话错误('ui-conversation image cache is disposed')
        绑定=自身.会话面.binding(会话标识)
        if 绑定 is None:
            raise 对话错误('ui-conversation: unknown session "'+str(会话标识)+'"')
        键=附件['attachmentId']
        表=自身.条目.get(id(绑定))
        if 表 is None:
            表={}
            自身.条目[id(绑定)]=表
        if 键 in 表 and 表[键].get('current') is not None:
            return 表[键]['current']
        结果=绑定.session.readAttachment(键)
        if not 结果.get('ok'):
            raise 对话错误(结果['error']['code']+': '+结果['error']['message'])
        媒体=结果['value']['attachment']['mediaType']
        数据=结果['value']['data']
        if isinstance(数据,str):
            编码=数据
        else:
            编码=base64.b64encode(bytes(数据)).decode('ascii')
        地址='data:'+媒体+';base64,'+编码
        表[键]={'current':地址}
        自身.地址.add(地址)
        return 地址

    def 窥视(自身,会话标识,附件):
        '有缓存才返回，不发起读取'
        绑定=自身.会话面.binding(会话标识)
        if 绑定 is None:
            return None
        表=自身.条目.get(id(绑定))
        if 表 is None:
            return None
        项=表.get(附件['attachmentId'])
        if 项 is None:
            return None
        return 项.get('current')

    def 播种(自身,会话标识,附件,地址):
        '先收下预览。已有条目就不再抢'
        if 自身.已拆:
            return False
        绑定=自身.会话面.binding(会话标识)
        if 绑定 is None:
            return False
        表=自身.条目.get(id(绑定))
        if 表 is None:
            表={}
            自身.条目[id(绑定)]=表
        键=附件['attachmentId']
        if 键 in 表:
            return False
        表[键]={'current':地址}
        自身.地址.add(地址)
        return True

    def 拆掉(自身):
        '撤销 blob 地址'
        if 自身.已拆:
            return
        自身.已拆=True
        for 地址 in list(自身.地址):
            if isinstance(地址,str) and 地址.startswith('blob:'):
                try:
                    URL.revokeObjectURL(地址)
                except NameError:
                    pass
        自身.地址.clear()
        自身.条目.clear()
