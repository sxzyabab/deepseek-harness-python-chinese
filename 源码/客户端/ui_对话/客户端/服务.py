'按作用域发送、取消，并持有草稿附件'
import uuid
from ....依赖.cordis.服务 import 服务
from ...存储 import 创建快照存储
from ....工具.加密 import 字节转base64
from ..异常 import 不支持图片媒体类型,对话错误

__all__=['会话控制器','是图片媒体类型']

图片类型=('image/png','image/jpeg','image/webp','image/gif')

def 是图片媒体类型(值):
    '浏览器声明的类型是不是接受的图片'
    return 值 in 图片类型

def 图片媒体类型(值):
    '不是四种图片就抛不支持'
    if 值 not in 图片类型:
        raise 不支持图片媒体类型(值)
    return 值

def 浏览器草稿附件(文件):
    '只把标识放进输入状态。预览用对象地址'
    标识=str(uuid.uuid4())
    地址=''
    if hasattr(URL,'createObjectURL'):
        地址=URL.createObjectURL(文件)
    return {'kind':'image','id':标识,'previewUrl':地址,'file':文件}

def 探尺寸(附件):
    '浏览器解析出图片头之后补上宽高。没有 Image 构造器就跳过'
    try:
        图=Image()
    except NameError:
        return
    def 载入(事件):
        '记下固有宽高'
        附件['width']=图.naturalWidth
        附件['height']=图.naturalHeight
    图.onload=载入
    图.src=附件['previewUrl']

def 撤销预览(地址):
    'blob 地址用完就撤销'
    if isinstance(地址,str) and 地址.startswith('blob:') and hasattr(URL,'revokeObjectURL'):
        URL.revokeObjectURL(地址)

def 读取字节(文件):
    '精确字节或类文件整读'
    if isinstance(文件,(bytes,bytearray,memoryview)):
        return bytes(文件)
    if hasattr(文件,'read'):
        块=文件.read()
        if isinstance(块,str):
            return 块.encode('utf-8')
        return bytes(块)
    raise 对话错误('conversation: image read failed')

class 会话控制器(服务):
    '根上的 conversation 服务。方法按调用方作用域找会话'
    提供服务名='conversation'
    def __init__(自身,上下文,配置):
        '接上输入枢纽、阻断表和并发上传数'
        super().__init__(上下文,'conversation')
        自身.input=配置['input']
        自身.blocks=配置['blocks']
        自身.fileUploads=创建快照存储({})
        自身.草稿附件={}
        自身.上传操作={}
        自身.上传队列=[]
        自身.活动上传=0
        自身.最大并发=配置['maxConcurrentFileUploads']
        def 清理():
            '纤程结束时中止上传并撤销预览'
            def 拆():
                '清掉草稿附件'
                for 操作 in list(自身.上传操作.values()):
                    操作['controller'].abort()
                自身.上传操作.clear()
                自身.上传队列.clear()
                for 附件 in list(自身.草稿附件.values()):
                    if 附件['kind']=='image':
                        撤销预览(附件['previewUrl'])
                自身.草稿附件.clear()
                自身.fileUploads.set({})
            return 拆
        上下文.effect(清理,'conversation draft attachments')

    def send(自身,文本):
        '把纯文本按排队送进当前作用域'
        会话=自身.作用域会话('send')
        结果=会话.prompt([{'type':'text','text':文本}],'queue')
        if not 结果.get('ok'):
            错误=结果['error']
            raise 对话错误('conversation.send failed: '+错误['code']+': '+错误['message'])

    def sendSession(自身,会话,文本,附件标识,方式,信号=None):
        '一次宿主接纳。失败时附件仍留在登记表里'
        附件=自身.resolveDraftAttachments(附件标识)
        if len(附件)!=len(附件标识):
            raise 对话错误('conversation.sendSession: one or more draft attachments are no longer available')
        上传=自身.fileUploads.getSnapshot()
        def 文件上传(项):
            '必须已经就绪'
            状态=上传.get(项['id'])
            if 状态 is None or 状态.get('status')!='ready':
                raise 对话错误('conversation.sendSession: one or more files have not finished uploading')
            return 状态
        待定=[]
        for 项 in 附件:
            if 项['kind']=='image':
                值={'previewUrl':项['previewUrl']}
                if 项['file'].name!='':
                    值['name']=项['file'].name
                if 项.get('width') is not None:
                    值['width']=项['width']
                if 项.get('height') is not None:
                    值['height']=项['height']
                待定.append({'type':'image','value':值})
            else:
                待定.append({'type':'file','value':文件上传(项)['file']})
        内容=[]
        for 项 in 附件:
            if 项['kind']=='image':
                内容.append({'type':'image',**自身.编码图片(项['file'])})
            else:
                内容.append({'type':'file','receiptId':文件上传(项)['receiptId']})
        if 文本!='':
            内容.append({'type':'text','text':文本})
        句柄=会话.beginSubmission({
            'mode':方式,
            'text':文本,
            'attachments':待定,
            'onRetire':lambda 结算:自身.结算附件(会话.sessionId,附件,结算),
        })
        结果=会话.prompt(内容,方式,信号,句柄['requestId'])
        if not 结果.get('ok'):
            return {'kind':'error'}
        return {'kind':'success'}

    def createDrafts(自身,会话标识,文件列):
        '图片留在浏览器，其他文件马上开始上传'
        出=[]
        for 文件 in 文件列:
            if 是图片媒体类型(getattr(文件,'type','')):
                附件=浏览器草稿附件(文件)
                自身.草稿附件[附件['id']]=附件
                探尺寸(附件)
                出.append(附件)
                continue
            附件={'kind':'file','id':str(uuid.uuid4()),'file':文件}
            自身.草稿附件[附件['id']]=附件
            自身.开始文件上传(会话标识,附件)
            出.append(附件)
        return 出

    def retryFileUpload(自身,会话标识,标识):
        '只重试失败了的文件'
        附件=自身.草稿附件.get(标识)
        if 附件 is None or 附件['kind']!='file':
            return
        if 自身.fileUploads.getSnapshot().get(标识,{}).get('status')!='error':
            return
        自身.开始文件上传(会话标识,附件)

    def rebindDraftFiles(自身,会话标识,标识列):
        '工作区切换后给带走的文件重新上传'
        for 标识 in 标识列:
            附件=自身.草稿附件.get(标识)
            if 附件 is not None and 附件['kind']=='file':
                自身.开始文件上传(会话标识,附件)

    def 开始文件上传(自身,会话标识,附件):
        '排队上传，受并发上限'
        旧=自身.上传操作.get(附件['id'])
        if 旧 is not None:
            旧['controller'].abort()
        控制器=AbortController()
        自身.fileUploads.update(lambda 草稿,标识=附件['id']:草稿.__setitem__(标识,{'status':'uploading','loaded':0}))
        自身.上传操作[附件['id']]={'controller':控制器}
        def 跑():
            '传到 fileUpload。失败写成 error'
            try:
                if 控制器.signal.aborted:
                    return
                if 自身.上传操作.get(附件['id'],{}).get('controller') is not 控制器:
                    return
                名=附件['file'].name if 附件['file'].name!='' else None
                def 进度(进展):
                    '还是这一次才更新进度'
                    if 自身.上传操作.get(附件['id'],{}).get('controller') is not 控制器:
                        return
                    def 写(草稿):
                        '写上传中'
                        if 附件['id'] not in 草稿:
                            return
                        项={'status':'uploading','loaded':进展['loaded']}
                        if 进展.get('total') is not None:
                            项['total']=进展['total']
                        草稿[附件['id']]=项
                    自身.fileUploads.update(写)
                结果=自身.ctx.fileUpload.上传(会话标识,附件['file'],名,控制器.signal,进度)
                if 自身.上传操作.get(附件['id'],{}).get('controller') is not 控制器:
                    return
                def 写完(草稿,结果=结果):
                    '就绪或错误'
                    if 附件['id'] not in 草稿:
                        return
                    if 结果.get('ok'):
                        草稿[附件['id']]={'status':'ready','receiptId':结果['value']['receiptId'],'file':结果['value']['file']}
                    else:
                        草稿[附件['id']]={'status':'error','message':结果['error']['message']}
                自身.fileUploads.update(写完)
            except Exception as 错误:
                if 自身.上传操作.get(附件['id'],{}).get('controller') is not 控制器:
                    return
                def 写错(草稿,错误=错误):
                    '异常收成错误状态'
                    if 附件['id'] not in 草稿:
                        return
                    草稿[附件['id']]={'status':'error','message':str(错误)}
                自身.fileUploads.update(写错)
            finally:
                if 自身.上传操作.get(附件['id'],{}).get('controller') is 控制器:
                    del 自身.上传操作[附件['id']]
        自身.上传队列.append(跑)
        自身.抽上传()

    def 抽上传(自身):
        '并发没满就再启动一个'
        while 自身.活动上传<自身.最大并发 and len(自身.上传队列)>0:
            任务=自身.上传队列.pop(0)
            自身.活动上传+=1
            try:
                任务()
            finally:
                自身.活动上传-=1

    def resolveDraftAttachments(自身,标识列):
        '还活着的草稿附件，按请求顺序'
        出=[]
        for 标识 in 标识列:
            附件=自身.草稿附件.get(标识)
            if 附件 is not None:
                出.append(附件)
        return 出

    def releaseDraftAttachment(自身,标识):
        '中止上传并撤销图片预览'
        附件=自身.草稿附件.get(标识)
        if 附件 is None:
            return
        操作=自身.上传操作.get(标识)
        if 标识 in 自身.上传操作:
            del 自身.上传操作[标识]
        if 操作 is not None:
            操作['controller'].abort()
        del 自身.草稿附件[标识]
        if 附件['kind']=='image':
            撤销预览(附件['previewUrl'])
            return
        当前=自身.fileUploads.getSnapshot()
        自身.fileUploads.set({键:值 for 键,值 in 当前.items() if 键!=标识})

    def releaseDraftAttachments(自身,附件列):
        '放掉这一批'
        for 附件 in 附件列:
            自身.releaseDraftAttachment(附件['id'])

    def updateQueue(自身,项标识,动作):
        '改队列。插话不可用或条目没了就安静返回'
        会话=自身.作用域会话('updateQueue')
        结果=会话.updateQueue(项标识,动作)
        if not 结果.get('ok'):
            码=结果['error']['code']
            if 动作.get('kind')=='steer' and 码 in ('session/steer-unavailable','session/queue-item-not-found'):
                return
            raise 对话错误('conversation.updateQueue failed: '+码+': '+结果['error']['message'])

    def cancel(自身):
        '取消当前回合，队列保留'
        会话=自身.作用域会话('cancel')
        结果=会话.cancel()
        if not 结果.get('ok'):
            raise 对话错误('conversation.cancel failed: '+结果['error']['code']+': '+结果['error']['message'])

    def loadOlder(自身):
        '再拉一页更早的历史'
        自身.作用域会话('loadOlder').loadOlder()

    def 作用域会话(自身,操作):
        '没有作用域或绑定就失败'
        标识=自身.作用域标识(操作)
        绑定=自身.要求会话().binding(标识)
        if 绑定 is None:
            raise 对话错误('conversation.'+操作+': session "'+str(标识)+'" resolved no binding')
        return 绑定.session

    def 作用域标识(自身,操作):
        '从调用方上下文读会话标识'
        标识=自身.要求会话().scopeOf(自身.ctx)
        if 标识 is None:
            raise 对话错误('conversation.'+操作+' requires a session scope — address one via ctx.sessions.scope(id).conversation')
        return 标识

    def 要求会话(自身):
        '会话服务必须在'
        会话=自身.ctx.get('sessions')
        if 会话 is None:
            raise 对话错误('conversation: sessions service unavailable')
        return 会话

    def 结算附件(自身,会话标识,附件列,退役):
        '观察到回声后放掉草稿。图片预览交给界面会话缓存'
        if 退役.get('reason')!='observed':
            return
        界面=自身.ctx.get('uiConversation')
        下标=0
        for 附件 in 附件列:
            活=自身.草稿附件.get(附件['id'])
            引用=None
            if isinstance(退役.get('attachments'),list) and 下标<len(退役['attachments']):
                引用=退役['attachments'][下标]
            下标+=1
            if 活 is None:
                continue
            if 附件['kind']=='file':
                自身.releaseDraftAttachment(附件['id'])
                continue
            del 自身.草稿附件[附件['id']]
            if 引用 is not None and 'mediaType' in 引用 and 界面 is not None and 界面.seedImageUrl(会话标识,引用,附件['previewUrl']) is True:
                continue
            撤销预览(附件['previewUrl'])

    def 编码图片(自身,文件):
        '浏览器图片的线文'
        出={'mediaType':图片媒体类型(getattr(文件,'type','')),'data':字节转base64(读取字节(文件))}
        if getattr(文件,'name','')!='':
            出['name']=文件.name
        return 出
