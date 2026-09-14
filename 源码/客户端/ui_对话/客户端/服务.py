import uuid#草稿 id
from ....依赖 import cordis#外部依赖胶水
from ....依赖.工具 import 二进制#base64 编解码
from .约定.槽 import 对话错误#本包唯一异常基类
服务=cordis.服务#Cordis 服务基类

__all__=['不支持图片媒体类型','对话错误','会话控制器','图片媒体类型','字节转base64']#仅中文公开名

支持媒体=('image/png','image/jpeg','image/webp','image/gif')#受支持的图片 MIME

class 不支持图片媒体类型(Exception):
    """浏览器声明了不支持的图片类型，由 UI 边界本地化。"""
    def __init__(自身,媒体类型):
        """保存声明值。"""
        super().__init__('unsupported image media type: '+(媒体类型 or '(empty)'))#消息
        自身.mediaType=媒体类型#声明值

def 图片媒体类型(值):
    """不支持则抛。"""
    if 值 in 支持媒体:
        return 值#原样
    raise 不支持图片媒体类型(值)#UI 边界本地化

字节转base64=二进制.转base64#依赖版 base64 编码

def 收回预览(网址):
    """只收回 blob: 对象 URL；宿主注入的 revokeObjectURL 若存在则调用。"""
    if not isinstance(网址,str) or not 网址.startswith('blob:'):
        return#无事
    撤销=globals().get('revokeObjectURL')#宿主可注入
    if 撤销 is not None:
        撤销(网址)#收回

def 浏览器草稿附件(文件):
    """从 File 造草稿附件。文件为本包 dict。"""
    标识=str(uuid.uuid4())#草稿身份
    if 'previewUrl' in 文件:
        预览=文件['previewUrl']#用已有
    else:
        造=globals().get('createObjectURL')#宿主可注入
        预览=造(文件) if 造 is not None else 'blob:'+标识#有则造，否则草稿键
    return {'kind':'image','id':标识,'previewUrl':预览,'file':文件}#草稿描述

class 会话控制器(服务):
    """根单例，登记为 conversation。"""
    def __init__(自身,上下文,配置):
        """配置携带 input 与 blocks 登记表。"""
        super().__init__(上下文,'conversation')#以 conversation 登记
        自身.input=配置['input']#输入机登记表
        自身.blocks=配置['blocks']#阻断登记表
        自身.草稿附件={}#草稿附件表
        自身.图片网址={}#历史图片 URL 缓存
        自身.图片世代={}#会话 → 图片世代
        自身.已创建网址=set()#已创建的对象 URL
        自身.已拆除=False#拆除后为 True
        def 清缓存():
            """收回 URL 并清空表。"""
            自身.已拆除=True#标为已拆除
            for 网址 in list(自身.已创建网址):
                收回预览(网址)#收回
            自身.已创建网址.clear()#清空
            自身.草稿附件.clear()#清空草稿
            自身.图片网址.clear()#清空历史
            自身.图片世代.clear()#清空世代
            return None#无额外拆除
        上下文.副作用(清缓存,'conversation attachment URL cache')#附件 URL 缓存

    def send(自身,文本):
        """业务失败则拒绝。"""
        会话=自身.作用域会话('send')#取作用域会话面
        结果=会话.prompt([{'type':'text','text':文本}],'queue').等待()#排队发送
        if 结果['ok'] is not True:
            错误=结果['error']#错误
            raise 对话错误('conversation.send failed: '+str(错误['code'])+': '+str(错误['message']))#拒绝

    def sendSession(自身,会话,文本,图片标识列表,模式):
        """有草稿已不可用则拒绝；成功后释放草稿。"""
        附件列表=自身.draftImages(图片标识列表)#按 id 解析仍活草稿
        if len(附件列表)!=len(图片标识列表):
            raise 对话错误('conversation.sendSession: one or more draft images are no longer available')#拒绝
        已传=自身.序列化图片([项['file'] for 项 in 附件列表])#File 转图片块
        内容=list(已传)+([] if 文本=='' else [{'type':'text','text':文本}])#图片在前
        结果=会话.prompt(内容,模式).等待()#按模式投递
        if 结果['ok'] is not True:
            错误=结果['error']#错误
            raise 对话错误('conversation.send failed: '+str(错误['code'])+': '+str(错误['message']))#拒绝
        自身.releaseDraftImages(附件列表)#成功后释放

    def createDraftImages(自身,文件列表):
        """校验媒体类型后返回有序草稿描述。文件为本包 dict。"""
        for 文件 in 文件列表:
            图片媒体类型(文件['type'] if 'type' in 文件 else '')#不支持则抛
        结果=[]#草稿列表
        for 文件 in 文件列表:
            附件=浏览器草稿附件(文件)#浏览器草稿
            自身.草稿附件[附件['id']]=附件#记入
            自身.已创建网址.add(附件['previewUrl'])#跟踪 URL
            结果.append(附件)#收下
        return 结果#有序草稿

    def draftImages(自身,标识列表):
        """按请求顺序取仍活草稿。"""
        附件列表=[]#累积
        for 标识 in 标识列表:
            if 标识 in 自身.草稿附件:
                附件列表.append(自身.草稿附件[标识])#收下
        return 附件列表#仍活草稿

    def releaseDraftImage(自身,标识):
        """已不在则无事。"""
        if 标识 not in 自身.草稿附件:
            return#无事
        附件=自身.草稿附件[标识]#查
        del 自身.草稿附件[标识]#删除
        自身.已创建网址.discard(附件['previewUrl'])#不再跟踪
        收回预览(附件['previewUrl'])#收回

    def releaseDraftImages(自身,附件列表):
        """逐个按 id 释放。"""
        for 附件 in 附件列表:
            自身.releaseDraftImage(附件['id'])#释放

    def resolveImage(自身,会话标识,附件):
        """缓存进行中的加载；已拆除则拒绝。附件为线协议 dict。"""
        if 自身.已拆除:
            raise 对话错误('conversation.resolveImage: service is disposed')#拒绝
        附件标识=附件['attachmentId']#附件 id
        键=str(会话标识)+':'+str(附件标识)#键
        if 键 in 自身.图片网址:
            return 自身.图片网址[键]['pending']#复用
        世代=自身.图片世代[会话标识] if 会话标识 in 自身.图片世代 else 0#当前世代
        绑定=自身.要求会话().binding(会话标识)#按 id 取绑定
        会话=绑定.session if 绑定 is not None else None#会话面
        if 会话 is None:
            raise 对话错误('conversation.resolveImage: unknown session "'+str(会话标识)+'"')#未知会话
        def 加载():
            """失败则视世代清缓存。"""
            try:
                结果=会话.readAttachment(附件标识).等待()#读
                if 结果['ok'] is not True:
                    错误=结果['error']#错误
                    raise 对话错误(str(错误['code'])+': '+str(错误['message']))#抛
                if 自身.已拆除:
                    raise 对话错误('conversation.resolveImage: service was disposed before loading completed')#拆除
                if (自身.图片世代[会话标识] if 会话标识 in 自身.图片世代 else 0)!=世代:
                    raise 对话错误('historical image scope was released before loading completed')#作用域释放
                值=结果['value']#值
                媒体=值['attachment']['mediaType']#MIME
                数据=值['data']#字节
                网址='data:'+str(媒体)+';base64,'+字节转base64(数据)#data URL 回退
                自身.已创建网址.add(网址)#跟踪
                return 网址#可渲染
            except 对话错误:
                if 键 in 自身.图片网址 and 自身.图片网址[键]['generation']==世代:
                    del 自身.图片网址[键]#清缓存
                raise#继续拒绝
        自身.图片网址[键]={'sessionId':会话标识,'generation':世代,'pending':加载}#写入
        return 加载#同步可调用

    def releaseSessionImages(自身,会话标识):
        """世代加一，作废进行中的加载。"""
        自身.图片世代[会话标识]=(自身.图片世代[会话标识] if 会话标识 in 自身.图片世代 else 0)+1#世代+1
        for 键 in list(自身.图片网址.keys()):
            条目=自身.图片网址[键]#条目
            if 条目['sessionId']!=会话标识:
                continue#跳过
            del 自身.图片网址[键]#去掉
            进行中=条目['pending']#进行中
            try:
                网址=进行中()#取 URL
                if 网址 in 自身.已创建网址:
                    自身.已创建网址.discard(网址)#去掉
                    收回预览(网址)#收回
            except 对话错误:
                pass#无 URL

    def updateQueue(自身,条目标识,动作):
        """严格转向竞态可收敛为成功。动作为本包 dict。"""
        会话=自身.作用域会话('updateQueue')#取会话
        结果=会话.updateQueue(条目标识,动作).等待()#转发
        if 结果['ok'] is not True:
            错误=结果['error']#错误
            种类=动作['kind'] if 'kind' in 动作 else None#动作种类
            码=错误['code']#错误码
            if 种类=='steer' and 码 in ('steer-unavailable','queue-item-not-found'):
                return#成功
            raise 对话错误('conversation.updateQueue failed: '+str(码)+': '+str(错误['message']))#拒绝

    def cancel(自身):
        """失败与 send 一样拒绝。"""
        会话=自身.作用域会话('cancel')#取会话
        结果=会话.cancel().等待()#转发
        if 结果['ok'] is not True:
            错误=结果['error']#错误
            raise 对话错误('conversation.cancel failed: '+str(错误['code'])+': '+str(错误['message']))#拒绝

    def loadOlder(自身):
        """转发到会话面。"""
        自身.作用域会话('loadOlder').loadOlder().等待()#转发

    def 作用域会话(自身,操作):
        """没有绑定则抛。"""
        标识=自身.作用域标识(操作)#读标签
        绑定=自身.要求会话().binding(标识)#查绑定
        if 绑定 is None:
            raise 对话错误('conversation.'+操作+': session "'+str(标识)+'" resolved no binding')#抛
        return 绑定.session#会话面

    def 作用域标识(自身,操作):
        """根上下文大声失败。"""
        标识=自身.要求会话().scopeOf(自身.ctx)#从重绑后的 ctx 读
        if 标识 is None:
            raise 对话错误('conversation.'+操作+' requires a session scope — address one via ctx.sessions.scope(id).conversation')#必须经 scope
        return 标识#会话身份

    def 要求会话(自身):
        """严格获取服务。"""
        会话面=自身.ctx.获取服务('sessions')#取
        if 会话面 is None:
            raise 对话错误('conversation: sessions service unavailable')#抛
        return 会话面#会话面

    def 序列化图片(自身,图片列表):
        """逐个把文件 dict 翻成图片块。"""
        结果=[]#块列表
        for 文件 in 图片列表:
            媒体=图片媒体类型(文件['type'] if 'type' in 文件 else '')#校验
            数据=文件['data'] if 'data' in 文件 else b''#字节
            块={'type':'image','mediaType':媒体,'data':字节转base64(数据)}#图片块
            if 'name' in 文件 and 文件['name']!='':
                块['name']=文件['name']#带上
            结果.append(块)#收下
        return 结果#图片块列表
