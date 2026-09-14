import re#正则
from .设置存储 import 错误文,写默认预设,写模式选择启用,读名册#读名册、错误文案、写默认与选择器

__all__=['分区控制器','草稿阻挡','分区初始','预设标识形']#仅中文公开名

预设标识形=re.compile(r'^[a-z0-9][a-z0-9-]*\Z',re.ASCII)#预设 id 合法形

分区初始={#页面初始快照
    'status':'idle','error':None,'authorable':False,'hasDocument':False,
    'showPicker':False,'policySaving':False,
    'rows':[],'copy':None,'view':None,'pendingDelete':None,'deleting':False,'revealedPaths':{},
}#结束初始

def 草稿阻挡(草稿,行列表):#复制草稿的客户端阻挡
    """返回阻挡原因键；可提交则为 None。"""
    标识=草稿['id'] if 草稿 is not None and 'id' in 草稿 else ''#id
    if 标识=='':#id 为空
        return 'idRequired'#必填
    if 预设标识形.match(标识) is None:#id 不合规则
        return 'idInvalid'#非法
    列表=行列表 if 行列表 is not None else []#现有行
    for 行 in 列表:#碰撞检查
        if 行['id']==标识:#已被占用
            return 'idTaken'#占用
    return None#可提交

class 简易快照存储:#快照存储
    """订阅 + set。"""
    def __init__(自身,初始):#初始
        """记下状态。"""
        自身.状态=dict(初始)#可变
        自身.订阅列表=[]#监听

    def getSnapshot(自身):#读
        """浅拷贝。"""
        return dict(自身.状态)#拷贝

    def subscribe(自身,监听):#订阅
        """返回拆除器。"""
        自身.订阅列表.append(监听)#登记
        def 拆除订阅():#拆除
            """去掉。"""
            if 监听 in 自身.订阅列表:#仍在
                自身.订阅列表.remove(监听)#删
        return 拆除订阅#拆除器

    def set(自身,下一):#整表替换
        """写快照并广播。"""
        自身.状态=dict(下一)#替换
        for 监听 in list(自身.订阅列表):#广播
            监听()#回调

class 分区控制器:#预设管理页控制器
    """读取名册并驱动复制对话框、查看器与位置揭示。RPC 一律等待。"""
    def __init__(自身,接口,名册变更=None):#挂 API 与名册变更回调
        """记下依赖与初始存储。"""
        自身.接口=接口#预设与设置线
        自身.名册变更=名册变更#名册目录变更回调
        自身.存储=简易快照存储(分区初始)#页面快照存储
        自身.加载中=False#是否正在排空加载
        自身.请求重载=False#加载期间又有失效

    def _合并(自身,补丁):#合并进快照
        """浅合并补丁。"""
        现=自身.存储.getSnapshot()#现
        现.update(补丁)#合并
        自身.存储.set(现)#写

    def 确认有效默认(自身,选择器):#策略写入后回读并反映宿主有效默认
        """开关对齐且名册就绪时返回有效默认 id。"""
        自身.load()#重读名册
        if 自身.存储.getSnapshot()['status']=='error':#失败则再读一次
            自身.load()#再读
        态=自身.存储.getSnapshot()#最新快照
        if 态['status']!='ready' or 态['showPicker']!=选择器:#开关未对齐
            return None#无效
        for 行 in 态['rows']:#找默认
            if 'isDefault' in 行 and 行['isDefault']:#默认
                return 行['id']#有效默认 id
        return None#无名册默认

    def setPickerVisible(自身,露出,同步空白会话=None):#写出选择器开关
        """露出或藏起新会话预设选择，不改已保存的默认。"""
        态=自身.存储.getSnapshot()#当前快照
        if 态['status']!='ready' or 态['policySaving'] or 态['showPicker']==露出:#无需写
            return#忽略
        自身._合并({'policySaving':True,'error':None})#上锁
        try:#写入并确认
            失败=写模式选择启用(自身.接口,露出)#写出开关
            if 失败 is not None:#写入失败
                自身.load()#重读
                自身._合并({'error':失败})#整页展示失败
                return#停在失败
            有效=自身.确认有效默认(露出)#确认有效默认
            if 有效 is None:#开关未对齐或名册未就绪
                return#停
            if 同步空白会话 is not None:#可选同步空白会话
                同步失败=同步空白会话(有效)#同步
                if 同步失败 is not None:#同步拒绝
                    自身._合并({'error':同步失败})#整页展示
        except Exception as 错误:#传输失败；RPC 异常契约未定
            自身.load()#重读
            自身._合并({'error':错误文(错误)})#整页展示失败
        finally:#无论成败都解锁
            自身._合并({'policySaving':False})#解锁

    def _改草稿(自身,补丁):#改打开的复制草稿
        """对话框未开则忽略。"""
        现=自身.存储.getSnapshot()#现
        草稿=现['copy']#当前草稿
        if 草稿 is None:#未开
            return#忽略
        下一=dict(草稿)#拷贝
        下一.update(补丁)#合并
        自身._合并({'copy':下一})#写入

    def load(自身):#读名册并刷新快照
        """合并失效，读期间收到的变更不会丢。"""
        自身.请求重载=True#标失效
        if 自身.加载中:#已有在飞
            return#等当前趟排完
        自身.加载中=True#开一趟
        try:#循环读到没有新失效
            while 自身.请求重载:#至少读一次
                自身.请求重载=False#本趟已认领失效
                自身._单次加载()#本趟拥有的一次读取
        finally:#无论成败都清在飞
            自身.加载中=False#允许下次开新趟

    def _单次加载(自身):#单次读取
        """空名册 → unavailable。"""
        前=自身.存储.getSnapshot()#读取前
        if 前['status']=='loading':#已有读取在飞
            return#让出
        自身._合并({'status':'loading','error':None})#标 loading
        名册=读名册(自身.接口)#读名册
        if not 名册['ok']:#失败
            自身._合并({'status':'error','error':名册['error']})#错误
            return#停
        值=名册['value'] if 名册['value'] is not None else {}#值
        预设列表=值['presets'] if 'presets' in 值 and 值['presets'] is not None else []#列表
        可写=bool(值['authorable']) if 'authorable' in 值 else False#可否编写
        有文档=bool(值['hasDocument']) if 'hasDocument' in 值 else False#有无打开器
        选择启用=bool(值['modeSelectionEnabled']) if 'modeSelectionEnabled' in 值 else False#选择器开关
        if len(预设列表)==0:#部署未配置任何预设
            自身._合并({'status':'unavailable','rows':[],'authorable':可写,'hasDocument':有文档,'showPicker':选择启用,'copy':None,'view':None})#不可用
            return#空名册到此为止
        揭示=前['revealedPaths'] if 前['revealedPaths'] is not None else {}#重载前的揭示
        保留={}#只保留仍在名册里的路径
        for 键,路径 in 揭示.items():#逐条
            if any(项['id']==键 for 项 in 预设列表):#仍在名册
                保留[键]=路径#留下
        自身._合并({#写入就绪快照
            'status':'ready','error':None,'authorable':可写,'hasDocument':有文档,
            'showPicker':选择启用,
            'rows':[dict(项) for 项 in 预设列表],'revealedPaths':保留,
        })#结束就绪

    def view(自身,标识):#打开只读查看器
        """组合已加载，或失败已写到页面上。"""
        自身._合并({'error':None})#清整页错误
        try:#读组合正文
            应答=自身.接口.agentPresets.read({'agentPreset':标识}).等待()#向宿主读预设
            结果=应答['result'] if 'result' in 应答 else None#信封
            if 结果 is None or not 结果['ok']:#宿主拒绝
                错误体=(结果['error'] if 结果 is not None and 'error' in 结果 else None) or {}#错误
                自身._合并({'error':错误体['message'] if isinstance(错误体,dict) and 'message' in 错误体 else str(错误体)})#整页展示失败
                return#停在失败
            值=结果['value'] if 'value' in 结果 and 结果['value'] is not None else {}#值
            名=值['name'] if 'name' in 值 else None#展示名
            内容=值['content'] if 'content' in 值 and 值['content'] is not None else ''#组合正文
            自身._合并({'view':{'id':标识,'title':名 if 名 is not None else 标识,'content':内容}})#打开查看器
        except Exception as 错误:#传输或未知拒绝；RPC 异常契约未定
            自身._合并({'error':错误文(错误)})#整页展示拒绝文案

    def closeView(自身):#关掉查看器
        """清查看器。"""
        自身._合并({'view':None})#清

    def beginCopy(自身,源):#打开复制对话框
        """针对一份预设打开复制对话框。"""
        行=None#源行
        for 候选 in 自身.存储.getSnapshot()['rows']:#找源行
            if 候选['id']==源:#命中
                行=候选#记下
                break#停
        标题=(行['name'] if 行 is not None and 'name' in 行 else None) or 源#源标题
        自身._合并({'error':None,'copy':{'from':源,'fromTitle':标题,'id':'','name':'','saving':False,'error':None}})#空草稿

    def cancelCopy(自身):#取消复制
        """丢掉草稿。"""
        自身._合并({'copy':None})#丢掉

    def setCopyId(自身,标识):#改草稿 id
        """写入 id 并清对话框错误。"""
        自身._改草稿({'id':标识,'error':None})#写入

    def setCopyName(自身,名):#改草稿展示名
        """写入展示名并清对话框错误。"""
        自身._改草稿({'name':名,'error':None})#写入

    def confirmCopy(自身):#提交复制
        """复制已落定且页面已反映。"""
        草稿=自身.存储.getSnapshot()['copy']#当前草稿
        if 草稿 is None or 草稿['saving']:#未开或已在飞
            return#忽略
        if 草稿阻挡(草稿,自身.存储.getSnapshot()['rows']) is not None:#客户端仍阻挡
            return#忽略
        自身._改草稿({'saving':True,'error':None})#标为提交中
        try:#向宿主复制
            名原文=草稿['name'] if 'name' in 草稿 and 草稿['name'] is not None else ''#展示名
            名=名原文.strip()#去掉首尾空白的展示名
            载荷={'from':草稿['from'],'agentPreset':草稿['id']}#基础
            if 名!='':#非空展示名
                载荷['name']=名#带上
            应答=自身.接口.agentPresets.copy(载荷).等待()#经线复制
            结果=应答['result'] if 'result' in 应答 else None#信封
            if 结果 is None or not 结果['ok']:#宿主拒绝
                错误体=(结果['error'] if 结果 is not None and 'error' in 结果 else None) or {}#错误
                自身._改草稿({'saving':False,'error':错误体['message'] if isinstance(错误体,dict) and 'message' in 错误体 else str(错误体)})#对话框展示失败
                return#停在对话框
            自身._合并({'copy':None})#关掉对话框
            自身.load()#重读名册
            if 自身.名册变更 is not None:#有回调
                自身.名册变更()#通知其它面
            自身.openLocation(草稿['id'])#打开或揭示新目录
        except Exception as 错误:#传输或未知拒绝；RPC 异常契约未定
            自身._改草稿({'saving':False,'error':错误文(错误)})#对话框展示拒绝文案

    def openLocation(自身,标识):#打开或揭示目录
        """宿主已回答且页面已反映。"""
        try:#问宿主打开文档
            应答=自身.接口.agentPresets.openDocument({'agentPreset':标识}).等待()#打开或返回路径
            结果=应答['result'] if 'result' in 应答 else None#信封
            if 结果 is None or not 结果['ok']:#宿主拒绝
                错误体=(结果['error'] if 结果 is not None and 'error' in 结果 else None) or {}#错误
                自身._合并({'error':错误体['message'] if isinstance(错误体,dict) and 'message' in 错误体 else str(错误体)})#整页展示失败
                return#停在失败
            值=结果['value'] if 'value' in 结果 and 结果['value'] is not None else {}#值
            if 'opened' in 值 and 值['opened']:#桌面已打开
                return#无需揭示
            路径=值['path'] if 'path' in 值 else None#打不开时给出的路径
            揭示=dict(自身.存储.getSnapshot()['revealedPaths'] if 自身.存储.getSnapshot()['revealedPaths'] is not None else {})#现有
            揭示[标识]=路径#记到该行
            自身._合并({'revealedPaths':揭示})#写入
        except Exception as 错误:#传输或未知拒绝；RPC 异常契约未定
            自身._合并({'error':错误文(错误)})#整页展示拒绝文案

    def confirmDelete(自身,标识):#打开或关掉删除确认
        """删除飞行中不改确认。"""
        if 自身.存储.getSnapshot()['deleting']:#删除飞行中
            return#忽略
        自身._合并({'pendingDelete':标识})#记下待删或清掉

    def remove(自身):#执行删除
        """删除已落定且页面已反映。"""
        现=自身.存储.getSnapshot()#现
        待删=现['pendingDelete']#待删
        if 待删 is None or 现['deleting']:#无确认或已在飞
            return#忽略
        自身._合并({'deleting':True,'error':None})#标为删除中
        try:#向宿主删除
            应答=自身.接口.agentPresets.remove({'agentPreset':待删}).等待()#经线删除
            结果=应答['result'] if 'result' in 应答 else None#信封
            if 结果 is None or not 结果['ok']:#宿主拒绝
                错误体=(结果['error'] if 结果 is not None and 'error' in 结果 else None) or {}#错误
                自身._合并({'deleting':False,'pendingDelete':None,'error':错误体['message'] if isinstance(错误体,dict) and 'message' in 错误体 else str(错误体)})#清确认
                return#停在失败
            自身._合并({'deleting':False,'pendingDelete':None})#清删除态
            自身.load()#重读名册
            if 自身.名册变更 is not None:#有回调
                自身.名册变更()#通知其它面
        except Exception as 错误:#传输或未知拒绝；RPC 异常契约未定
            自身._合并({'deleting':False,'pendingDelete':None,'error':错误文(错误)})#清确认并展示拒绝

    def makeDefault(自身,标识,同步空白会话=None):#设为默认预设
        """写入已落定且名册已重读。选择器关闭或策略在写则忽略。"""
        态=自身.存储.getSnapshot()#当前快照
        if not 态['showPicker'] or 态['policySaving']:#选择器关或策略在写
            return#忽略
        自身._合并({'policySaving':True,'error':None})#上锁
        try:#写入并确认
            失败=写默认预设(自身.接口,标识)#经设置面写入
            if 失败 is not None:#写入失败
                自身._合并({'error':失败})#整页展示失败
                return#停在失败
            有效=自身.确认有效默认(True)#确认有效默认
            if 有效 is None:#名册未就绪
                return#停
            if 同步空白会话 is not None:#可选同步空白会话
                同步失败=同步空白会话(有效)#同步
                if 同步失败 is not None:#同步拒绝
                    自身._合并({'error':同步失败})#整页展示
        except Exception as 错误:#传输失败；RPC 异常契约未定
            自身._合并({'error':错误文(错误)})#整页展示失败
        finally:#无论成败都解锁
            自身._合并({'policySaving':False})#解锁
