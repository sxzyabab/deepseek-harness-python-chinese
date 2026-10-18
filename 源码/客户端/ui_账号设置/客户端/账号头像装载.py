'侧栏和设置页共用这一次插件寿命里的头像加载'
from ...模块.客户端.通告 import 取握手窗口

__all__=['账号头像装载']

class 账号头像装载:
    '持有浏览器图片。地址换了或插件卸下之后不再回调'
    def __init__(自身,发布):
        '发布把图片状态写进账号快照'
        自身.发布=发布
        自身.快照=None
        自身.图片=None
        自身.已拆除=False

    def 设地址(自身,地址):
        '地址变了才加载一次。空地址清掉图片'
        if 自身.已拆除:
            return
        来源=地址 or None
        if isinstance(自身.快照,dict) and 自身.快照.get('url')==来源:
            return
        if 来源 is None:
            自身.拆开()
            自身.写入(None)
        else:
            自身.加载(来源)

    def 重试(自身):
        '只重试已经失败的图片'
        if 自身.已拆除 is not True and isinstance(自身.快照,dict) and 自身.快照.get('status')=='failed':
            自身.加载(自身.快照['url'])

    def 失败(自身,快照):
        '已经画出来的图片出错时，两边都回到缺省图标。过期的尝试忽略'
        if 自身.已拆除 or 自身.快照 is not 快照 or 快照.get('status')!='ready':
            return
        自身.拆开()
        自身.写入({'url':快照['url'],'status':'failed'})

    def 重置(自身):
        '放开图片但不发布。换账号帧时由业主自己清空头像'
        自身.拆开()
        自身.快照=None

    def 拆除(自身):
        '放开图片，之后不再加载或发布'
        自身.已拆除=True
        自身.重置()

    def 加载(自身,地址):
        '换成新的图片元素。旧元素的回调作废'
        自身.拆开()
        窗口=取握手窗口()
        图片=窗口.Image()
        自身.图片=图片
        图片.referrerPolicy='no-referrer'
        def 落定(状态):
            '只接受仍是当前这次加载的结果'
            if 自身.图片 is not 图片:
                return
            图片.onload=None
            图片.onerror=None
            自身.写入({'url':地址,'status':状态})
        def 载入(_事件=None):
            '加载成功'
            落定('ready')
        def 出错(_事件=None):
            '加载失败'
            落定('failed')
        图片.onload=载入
        图片.onerror=出错
        自身.写入({'url':地址,'status':'loading'})
        if 自身.图片 is 图片:
            图片.src=地址

    def 写入(自身,快照):
        '记下并交给账号快照'
        自身.快照=快照
        自身.发布(快照)

    def 拆开(自身):
        '卸下当前图片的回调和地址'
        图片=自身.图片
        自身.图片=None
        if 图片 is None:
            return
        图片.onload=None
        图片.onerror=None
        图片.removeAttribute('src')
