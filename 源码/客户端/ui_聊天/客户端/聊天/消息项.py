import math#重试秒
import time#倒计时

__all__=['内容分片','重试秒数','模型重试行','回合错行','回合顶格行','待插话泡','待提交泡','用户消息行']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 内容分片(内容):
    """用户消息内容分片。"""
    文本列表=[]#文本
    图列表=[]#图
    其余=[]#其余
    块列表=内容 if 内容 is not None else []#块
    for 块 in 块列表:#块
        类型=块['type'] if 'type' in 块 else None#类型
        文=块['text'] if 'text' in 块 else None#文
        if 类型=='text' and isinstance(文,str):#文本
            文本列表.append(文)#收
        elif 类型=='image' and 'attachment' in 块 and 块['attachment'] is not None:#图
            图列表.append({'attachment':块['attachment']})#收
        else:#其余
            其余.append(块)#收
    return {'text':''.join(文本列表),'images':图列表,'rest':其余}#分片

def 重试秒数(毫秒):
    """ceil(ms/1000) 下限 1。"""
    return max(1,math.ceil(毫秒/1000))#秒

class 模型重试行:
    """倒计时挂在首次渲染。"""
    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        节点=自身.属性['node'] if 'node' in 自身.属性 and 自身.属性['node'] is not None else {}#节点
        延迟=节点['delayMs'] if 'delayMs' in 节点 and 节点['delayMs'] is not None else 0#延迟
        自身.截止=int(time.time()*1000)+int(延迟)#截止

    def 更新(自身,属性):
        """刷新；delay/seq 变则重锚。"""
        旧=自身.属性['node'] if 'node' in 自身.属性 else None#旧
        自身.属性=属性 if 属性 is not None else {}#新
        新=自身.属性['node'] if 'node' in 自身.属性 else None#新
        旧延=旧['delayMs'] if 旧 is not None and 'delayMs' in 旧 else None#旧延
        新延=新['delayMs'] if 新 is not None and 'delayMs' in 新 else None#新延
        旧序=旧['seq'] if 旧 is not None and 'seq' in 旧 else None#旧序
        新序=新['seq'] if 新 is not None and 'seq' in 新 else None#新序
        if 旧延!=新延 or 旧序!=新序:#重锚
            延迟=新延 if 新延 is not None else 0#延迟
            自身.截止=int(time.time()*1000)+int(延迟)#截止

    def 渲染(自身):
        """重试 details。"""
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        活跃=属性['active'] is True if 'active' in 属性 else False#活跃
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        延迟=节点['delayMs'] if 'delayMs' in 节点 and 节点['delayMs'] is not None else 0#延迟
        计划秒=重试秒数(延迟)#计划
        模式=节点['mode'] if 'mode' in 节点 else None#模式
        最大=节点['maxRetries'] if 'maxRetries' in 节点 and 模式=='normal' else '∞'#最大
        剩余=重试秒数(自身.截止-int(time.time()*1000)) if 活跃 is True else 计划秒#秒
        态=节点['retryState'] if 'retryState' in 节点 else None#态
        if 活跃 is True:#活跃
            标签=翻译('message.retry.active')#活
        elif 态=='cancelled':#取消
            标签=翻译('message.retry.cancelled')#取消
        elif 态=='started':#已开
            标签=翻译('message.retry.started')#开
        else:#排定
            标签=翻译('message.retry.scheduled')#排
        失败=节点['failure'] if 'failure' in 节点 else None#失败
        失败文=失败['message'] if 失败 is not None and 'message' in 失败 else None#失败文
        重试=节点['retry'] if 'retry' in 节点 else None#重试
        return {#重试
            'type':'model-retry','active':活跃,#类型/活
            'status':翻译('message.retry.status',{'label':标签,'retry':重试,'maximum':最大,'seconds':剩余}),#状态
            'delayLabel':翻译('message.retry.delay'),'delayMs':节点['delayMs'] if 'delayMs' in 节点 else None,#延迟
            'failureLabel':翻译('message.retry.failure'),'failure':失败文,#失败
            'cssModule':'消息项.module.css',#样式
        }#结束

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 回合错行:
    """终端失败反馈。"""
    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """错行。"""
        节点=自身.属性['node'] if 'node' in 自身.属性 and 自身.属性['node'] is not None else {}#节点
        翻译=自身.属性['t'] if 't' in 自身.属性 else 恒等翻译#文案
        消息=节点['message'] if 'message' in 节点 else None#消息
        码=节点['code'] if 'code' in 节点 else None#码
        return {'type':'turn-error','title':翻译('message.turnError'),'message':消息,'code':码,'dot':'error','cssModule':'消息项.module.css'}#错

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 回合顶格行:
    """输出顶格提示。"""
    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """警告行。"""
        翻译=自身.属性['t'] if 't' in 自身.属性 else 恒等翻译#文案
        return {'type':'turn-max-tokens','title':翻译('message.maxTokens'),'hint':翻译('message.maxTokens.hint'),'dot':'warning','cssModule':'消息项.module.css'}#顶格

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 待插话泡:
    """进行中插话预览。"""
    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """右对齐泡。"""
        内容=自身.属性['content'] if 'content' in 自身.属性 else None#内容
        分片=内容分片(内容)#分片
        return {'type':'pending-steering','text':分片['text'],'images':分片['images'],'pending':True,'cssModule':'消息项.module.css'}#泡

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 待提交泡:
    """本地提交回声，至持久 user/steering 出现。"""
    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """回声泡。"""
        提交=自身.属性['submission'] if 'submission' in 自身.属性 and 自身.属性['submission'] is not None else {}#提交
        文=提交['text'] if 'text' in 提交 and 提交['text'] is not None else ''#文本
        内容=[] if 文=='' else [{'type':'text','text':文}]#块
        预览=[]#图
        图列表=提交['images'] if 'images' in 提交 and 提交['images'] is not None else []#图
        for 图 in 图列表:#扫
            项={'preview':{'url':图['previewUrl'] if 'previewUrl' in 图 else None}}#预览
            if 'name' in 图 and 图['name'] is not None:#名
                项['preview']['name']=图['name']#名
            if 'width' in 图 and 图['width'] is not None:#宽
                项['preview']['width']=图['width']#宽
            if 'height' in 图 and 图['height'] is not None:#高
                项['preview']['height']=图['height']#高
            预览.append(项)#收
        位=提交['placement'] if 'placement' in 提交 else None#位
        时=提交['time'] if 'time' in 提交 else None#时
        return {'type':'pending-submission','text':文,'previewImages':预览,'pending':位=='steering','echo':True,'time':时,'cssModule':'消息项.module.css'}#泡

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 用户消息行:
    """右对齐用户消息。"""
    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """用户行。"""
        节点=自身.属性['node'] if 'node' in 自身.属性 and 自身.属性['node'] is not None else {}#节点
        内容=节点['content'] if 'content' in 节点 else None#内容
        分片=内容分片(内容)#分片
        return {'type':'user-message','text':分片['text'],'images':分片['images'],'rest':分片['rest'],'cssModule':'消息项.module.css'}#用户

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
