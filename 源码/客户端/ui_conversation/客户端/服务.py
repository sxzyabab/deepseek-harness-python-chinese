"""按作用域寻址的会话发送、取消与历史编排。

对齐上游 `ui-conversation/src/client/service.ts`。公开面仅中文名。
浏览器 File/Blob/URL API 在非浏览器宿主半退化为 data URL 或拒绝。
"""
import base64,uuid#图片编码与草稿 id
from cordis import 服务#Cordis 服务基类

__all__=['不支持图片媒体类型','会话控制器','图片媒体类型','字节转base64']#仅中文公开名

支持媒体=('image/png','image/jpeg','image/webp','image/gif')#受支持的图片 MIME

class 不支持图片媒体类型(Exception):#不支持的图片媒体类型
    """浏览器声明了不支持的图片类型，由 UI 边界本地化。"""
    def __init__(自身,媒体类型):#记下声明的类型
        """保存声明值。"""
        super().__init__('unsupported image media type: '+(媒体类型 or '(empty)'))#消息
        自身.name='UnsupportedImageMediaTypeError'#错误名
        自身.mediaType=媒体类型#声明值

def 图片媒体类型(值):#收窄浏览器声明的图片 MIME
    """不支持则抛。"""
    if 值 in 支持媒体:#受支持
        return 值#原样
    raise 不支持图片媒体类型(值)#UI 边界本地化

def 字节转base64(数据):#字节转 base64
    """接受 bytes / bytearray / memoryview。"""
    if isinstance(数据,memoryview):#视图
        数据=数据.tobytes()#拷贝
    elif not isinstance(数据,(bytes,bytearray)):#其它
        数据=bytes(数据)#强制
    return base64.b64encode(bytes(数据)).decode('ascii')#base64 文本

def 收回预览(网址):#收回预览 URL
    """只收回 blob: 对象 URL；宿主注入的 revokeObjectURL 若存在则调用。"""
    if not isinstance(网址,str) or not 网址.startswith('blob:'):#非 blob
        return#无事
    撤销=globals().get('revokeObjectURL')#宿主可注入
    if callable(撤销):#有撤销器
        撤销(网址)#收回

def 浏览器草稿附件(文件):#从 File 造草稿附件
    """仅浏览器侧的草稿描述；只有其 id 进入输入状态。"""
    标识=str(uuid.uuid4())#草稿身份
    if isinstance(文件,dict) and 'previewUrl' in 文件:#映射已带预览
        预览=文件['previewUrl']#用已有
    elif hasattr(文件,'previewUrl'):#对象已带预览
        预览=文件.previewUrl#用已有
    else:#造预览
        造=globals().get('createObjectURL')#宿主可注入
        预览=造(文件) if callable(造) else 'blob:'+标识#有则造，否则草稿键
    return {'kind':'image','id':标识,'previewUrl':预览,'file':文件}#草稿描述
class 会话控制器(服务):#按作用域寻址的会话服务
    """根单例，登记为 conversation。"""
    def __init__(自身,上下文,配置):#挂到 conversation 名下
        """配置携带 input 与 blocks 登记表。"""
        super().__init__(上下文,'conversation')#以 conversation 登记
        自身.input=配置['input']#输入机登记表
        自身.blocks=配置['blocks']#阻断登记表
        自身.草稿附件={}#草稿附件表
        自身.图片网址={}#历史图片 URL 缓存
        自身.图片世代={}#会话 → 图片世代
        自身.已创建网址=set()#已创建的对象 URL
        自身.已拆除=False#拆除后为 True
        def 清缓存():#光纤拆除时清附件缓存
            """收回 URL 并清空表。"""
            自身.已拆除=True#标为已拆除
            for 网址 in list(自身.已创建网址):#逐个
                收回预览(网址)#收回
            自身.已创建网址.clear()#清空
            自身.草稿附件.clear()#清空草稿
            自身.图片网址.clear()#清空历史
            自身.图片世代.clear()#清空世代
            return None#无额外拆除
        上下文.effect(lambda:清缓存,'conversation attachment URL cache')#附件 URL 缓存

    def send(自身,文本):#排队投递文本提示
        """业务失败则拒绝。"""
        会话=自身.作用域会话('send')#取作用域会话面
        结果=会话.prompt([{'type':'text','text':文本}],'queue')#排队发送
        结果=自身.解开(结果)#等待
        if not 取成功(结果):#业务失败
            错误=取错误(结果)#错误
            raise Exception('conversation.send failed: '+str(错误.get('code'))+': '+str(错误.get('message')))#拒绝

    def sendSession(自身,会话,文本,图片标识们,模式):#一次准入提交图片与文本
        """有草稿已不可用则拒绝；成功后释放草稿。"""
        附件们=自身.draftImages(图片标识们)#按 id 解析仍活草稿
        if len(附件们)!=len(图片标识们):#缺图
            raise Exception('conversation.sendSession: one or more draft images are no longer available')#拒绝
        已传=自身.解开(自身.序列化图片([项['file'] for 项 in 附件们]))#File 转图片块
        内容=list(已传)+( [] if 文本=='' else [{'type':'text','text':文本}] )#图片在前
        结果=自身.解开(会话.prompt(内容,模式))#按模式投递
        if not 取成功(结果):#业务失败
            错误=取错误(结果)#错误
            raise Exception('conversation.send failed: '+str(错误.get('code'))+': '+str(错误.get('message')))#拒绝
        自身.releaseDraftImages(附件们)#成功后释放

    def createDraftImages(自身,文件们):#登记草稿图片
        """校验媒体类型后返回有序草稿描述。"""
        for 文件 in 文件们:#逐个校验
            类型=文件.get('type') if isinstance(文件,dict) else getattr(文件,'type','')#MIME
            图片媒体类型(类型)#不支持则抛
        结果=[]#草稿们
        for 文件 in 文件们:#逐个造
            附件=浏览器草稿附件(文件)#浏览器草稿
            自身.草稿附件[附件['id']]=附件#记入
            自身.已创建网址.add(附件['previewUrl'])#跟踪 URL
            结果.append(附件)#收下
        return 结果#有序草稿

    def draftImages(自身,标识们):#按 id 取仍活草稿
        """按请求顺序。"""
        附件们=[]#累积
        for 标识 in 标识们:#按序
            附件=自身.草稿附件.get(标识)#可能已释放
            if 附件 is not None:#仍活
                附件们.append(附件)#收下
        return 附件们#仍活草稿

    def releaseDraftImage(自身,标识):#释放单份草稿
        """已不在则无事。"""
        附件=自身.草稿附件.get(标识)#查
        if 附件 is None:#已不在
            return#无事
        del 自身.草稿附件[标识]#删除
        自身.已创建网址.discard(附件['previewUrl'])#不再跟踪
        收回预览(附件['previewUrl'])#收回

    def releaseDraftImages(自身,附件们):#批量释放草稿
        """逐个按 id 释放。"""
        for 附件 in 附件们:#每个
            自身.releaseDraftImage(附件['id'])#释放

    def resolveImage(自身,会话标识,附件):#解析历史图片 URL
        """缓存进行中的承诺；已拆除则拒绝。"""
        if 自身.已拆除:#已拆除
            raise Exception('conversation.resolveImage: service is disposed')#拒绝
        键=str(会话标识)+':'+str(附件.get('attachmentId') if isinstance(附件,dict) else getattr(附件,'attachmentId',''))#键
        缓存=自身.图片网址.get(键)#查缓存
        if 缓存 is not None:#命中
            return 缓存['pending']#复用
        世代=自身.图片世代.get(会话标识,0)#当前世代
        绑定=自身.要求会话().binding(会话标识)#按 id 取绑定
        会话=绑定.session if 绑定 is not None else None#会话面
        if 会话 is None:#未知
            raise Exception('conversation.resolveImage: unknown session "'+str(会话标识)+'"')#未知会话
        附件标识=附件.get('attachmentId') if isinstance(附件,dict) else getattr(附件,'attachmentId')#附件 id
        def 加载():#读持久附件字节并造 URL
            """失败则视世代清缓存。"""
            try:#读
                结果=自身.解开(会话.readAttachment(附件标识))#读
                if not 取成功(结果):#读失败
                    错误=取错误(结果)#错误
                    raise Exception(str(错误.get('code'))+': '+str(错误.get('message')))#抛
                if 自身.已拆除:#加载完成前已拆除
                    raise Exception('conversation.resolveImage: service was disposed before loading completed')#拆除
                if 自身.图片世代.get(会话标识,0)!=世代:#世代已变
                    raise Exception('historical image scope was released before loading completed')#作用域释放
                值=结果.get('value') if isinstance(结果,dict) else getattr(结果,'value',None)#值
                媒体=值['attachment']['mediaType'] if isinstance(值,dict) else getattr(getattr(值,'attachment',None),'mediaType','application/octet-stream')#MIME
                数据=值['data'] if isinstance(值,dict) else getattr(值,'data',b'')#字节
                网址='data:'+str(媒体)+';base64,'+字节转base64(数据)#data URL 回退
                自身.已创建网址.add(网址)#跟踪
                return 网址#可渲染
            except Exception:#失败
                条目=自身.图片网址.get(键)#仍本世代才删
                if 条目 is not None and 条目.get('generation')==世代:#本世代
                    自身.图片网址.pop(键,None)#清缓存
                raise#继续拒绝
        进行中=加载#同步可调用；宿主半可再包成承诺
        自身.图片网址[键]={'sessionId':会话标识,'generation':世代,'pending':进行中}#写入
        return 进行中#承诺或同步结果

    def releaseSessionImages(自身,会话标识):#释放该会话历史图片
        """世代加一，作废进行中的加载。"""
        自身.图片世代[会话标识]=自身.图片世代.get(会话标识,0)+1#世代+1
        for 键 in list(自身.图片网址.keys()):#扫缓存
            条目=自身.图片网址[键]#条目
            if 条目.get('sessionId')!=会话标识:#其它会话
                continue#跳过
            del 自身.图片网址[键]#去掉
            进行中=条目.get('pending')#进行中
            if callable(进行中):#可调用
                try:#成功加载才有 URL
                    网址=进行中()#取 URL
                    if 网址 in 自身.已创建网址:#跟踪中
                        自身.已创建网址.discard(网址)#去掉
                        收回预览(网址)#收回
                except Exception:#失败加载
                    pass#无 URL

    def updateQueue(自身,条目标识,动作):#改待处理队列
        """严格转向竞态可收敛为成功。"""
        会话=自身.作用域会话('updateQueue')#取会话
        结果=自身.解开(会话.updateQueue(条目标识,动作))#转发
        if not 取成功(结果):#业务失败
            错误=取错误(结果)#错误
            种类=动作.get('kind') if isinstance(动作,dict) else getattr(动作,'kind',None)#动作种类
            码=错误.get('code')#错误码
            if 种类=='steer' and 码 in ('steer-unavailable','queue-item-not-found'):#可收敛
                return#成功
            raise Exception('conversation.updateQueue failed: '+str(码)+': '+str(错误.get('message')))#拒绝

    def cancel(自身):#取消进行中的回合
        """失败与 send 一样拒绝。"""
        会话=自身.作用域会话('cancel')#取会话
        结果=自身.解开(会话.cancel())#转发
        if not 取成功(结果):#失败
            错误=取错误(结果)#错误
            raise Exception('conversation.cancel failed: '+str(错误.get('code'))+': '+str(错误.get('message')))#拒绝

    def loadOlder(自身):#拉更早历史
        """转发到会话面。"""
        自身.解开(自身.作用域会话('loadOlder').loadOlder())#转发

    def 作用域会话(自身,操作):#按调用方作用域取会话面
        """没有绑定则抛。"""
        标识=自身.作用域标识(操作)#读标签
        绑定=自身.要求会话().binding(标识)#查绑定
        if 绑定 is None:#没有
            raise Exception('conversation.'+操作+': session "'+str(标识)+'" resolved no binding')#抛
        return 绑定.session#会话面

    def 作用域标识(自身,操作):#读调用方会话标签
        """根上下文大声失败。"""
        标识=自身.要求会话().scopeOf(自身.ctx)#从重绑后的 ctx 读
        if 标识 is None:#根上下文
            raise Exception('conversation.'+操作+' requires a session scope — address one via ctx.sessions.scope(id).conversation')#必须经 scope
        return 标识#会话身份

    def 要求会话(自身):#取 sessions 服务
        """严格 ctx.get。"""
        会话们=自身.ctx.get('sessions')#取
        if 会话们 is None:#未挂载
            raise Exception('conversation: sessions service unavailable')#抛
        return 会话们#会话面

    def 序列化图片(自身,图片们):#File 转图片块
        """并行读每个文件（本面同步逐个）。"""
        结果=[]#块们
        for 文件 in 图片们:#每个
            类型=文件.get('type') if isinstance(文件,dict) else getattr(文件,'type','')#MIME
            媒体=图片媒体类型(类型)#校验
            if isinstance(文件,dict) and 'data' in 文件:#已有字节
                数据=文件['data']#字节
            elif hasattr(文件,'arrayBuffer') and callable(文件.arrayBuffer):#浏览器 File
                缓冲=自身.解开(文件.arrayBuffer())#读
                数据=缓冲#字节
            else:#原始 bytes
                数据=文件 if isinstance(文件,(bytes,bytearray)) else getattr(文件,'data',b'')#字节
            块={'type':'image','mediaType':媒体,'data':字节转base64(数据)}#图片块
            名=文件.get('name') if isinstance(文件,dict) else getattr(文件,'name','')#文件名
            if 名:#有名
                块['name']=名#带上
            结果.append(块)#收下
        return 结果#图片块列表

    def 解开(自身,值):#承诺则等待
        """有等待方法则调用。"""
        if hasattr(值,'等待') and callable(值.等待):#中文承诺
            return 值.等待()#等待
        if hasattr(值,'result') and callable(getattr(值,'result',None)):#concurrent future
            return 值.result()#结果
        return 值#同步

def 取成功(结果):#结果是否 ok
    """映射或对象。"""
    if isinstance(结果,dict):#映射
        return 结果.get('ok') is True#ok
    return getattr(结果,'ok',False) is True#属性

def 取错误(结果):#取 error 字段
    """映射或对象。"""
    if isinstance(结果,dict):#映射
        return 结果.get('error') or {}#错误
    return getattr(结果,'error',None) or {}#属性
