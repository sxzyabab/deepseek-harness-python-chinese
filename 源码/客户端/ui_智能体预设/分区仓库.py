"""智能体预设管理控制器：名册以列表呈现，复制对话框是创建预设的唯一途径。

对齐上游 `ui-agent-preset/src/client/section-store.ts`。公开面仅中文名。
浏览器不编辑任何组合正文；新预设是宿主侧对已有预设的复制。
"""
import re#正则
from ...依赖 import cordis#外部依赖胶水
from .设置仓库 import 错误文,写默认预设,读名册#读名册、错误文案、写默认

__all__=['分区控制器','草稿阻挡','分区初始','预设标识形']#仅中文公开名

预设标识形=re.compile(r'^[a-z0-9][a-z0-9-]*$')#预设 id 合法形

分区初始={#页面初始快照
    'status':'idle','error':None,'authorable':False,'hasDocument':False,
    'rows':[],'copy':None,'view':None,'pendingDelete':None,'deleting':False,'revealedPaths':{},
}#结束初始

def 解开(值):#承诺则等待
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 草稿阻挡(草稿,行们):#复制草稿的客户端阻挡
    """返回阻挡原因键；可提交则为 None。"""
    标识=草稿.get('id') if isinstance(草稿,dict) else ''#id
    if 标识=='':#id 为空
        return 'idRequired'#必填
    if not 预设标识形.match(标识):#id 不合规则
        return 'idInvalid'#非法
    for 行 in 行们 or []:#碰撞检查
        if (行.get('id') if isinstance(行,dict) else None)==标识:#已被占用
            return 'idTaken'#占用
    return None#可提交

class 简易快照仓:#快照仓
    """订阅 + set。"""
    def __init__(自身,初始):#初始
        """记下状态。"""
        自身.状态=dict(初始)#可变
        自身.订阅们=[]#监听

    def getSnapshot(自身):#读
        """浅拷贝。"""
        return dict(自身.状态)#拷贝

    def subscribe(自身,听):#订阅
        """返回拆除器。"""
        自身.订阅们.append(听)#登记
        def 拆():#拆除
            """去掉。"""
            if 听 in 自身.订阅们:#仍在
                自身.订阅们.remove(听)#删
        return 拆#拆除器

    def set(自身,下一):#整表替换
        """写快照并广播。"""
        自身.状态=dict(下一)#替换
        for 听 in list(自身.订阅们):#广播
            听()#回调

class 分区控制器:#预设管理页控制器
    """读取名册并驱动复制对话框、查看器与位置揭示。"""
    def __init__(自身,接口,名册变更=None):#挂 API 与名册变更回调
        """记下依赖与初始仓。"""
        自身.接口=接口#预设与设置线
        自身.名册变更=名册变更 or (lambda:None)#名册目录变更回调
        自身.store=简易快照仓(分区初始)#页面快照商店

    def _合并(自身,补丁):#合并进快照
        """浅合并补丁。"""
        现=自身.store.getSnapshot()#现
        现.update(补丁)#合并
        自身.store.set(现)#写

    def _改草稿(自身,补丁):#改打开的复制草稿
        """对话框未开则忽略。"""
        现=自身.store.getSnapshot()#现
        草稿=现.get('copy')#当前草稿
        if 草稿 is None:#未开
            return#忽略
        下一=dict(草稿)#拷贝
        下一.update(补丁)#合并
        自身._合并({'copy':下一})#写入

    def load(自身):#读名册并刷新快照
        """空名册 → unavailable。"""
        前=自身.store.getSnapshot()#读取前
        if 前.get('status')=='loading':#已有读取在飞
            return#让出
        自身._合并({'status':'loading','error':None})#标 loading
        名册=读名册(自身.接口)#读名册
        if not 名册.get('ok'):#失败
            自身._合并({'status':'error','error':名册.get('error')})#错误
            return#停
        值=名册.get('value') or {}#值
        预设们=值.get('presets') or []#列表
        可写=bool(值.get('authorable'))#可否编写
        有文档=bool(值.get('hasDocument'))#有无打开器
        if len(预设们)==0:#部署未配置任何预设
            自身._合并({'status':'unavailable','rows':[],'authorable':可写,'hasDocument':有文档,'copy':None,'view':None})#不可用
            return#空名册到此为止
        揭示=前.get('revealedPaths') or {}#重载前的揭示
        保留={k:v for k,v in 揭示.items() if any(p.get('id')==k for p in 预设们)}#只保留仍在名册里的路径
        自身._合并({#写入就绪快照
            'status':'ready','error':None,'authorable':可写,'hasDocument':有文档,
            'rows':[dict(p) for p in 预设们],'revealedPaths':保留,
        })#结束就绪

    def view(自身,标识):#打开只读查看器
        """组合已加载，或失败已写到页面上。"""
        自身._合并({'error':None})#清整页错误
        try:#读组合正文
            应答=解开(自身.接口.agentPresets.read({'agentPreset':标识}))#向宿主读预设
            结果=应答.get('result') if isinstance(应答,dict) else None#信封
            if not 结果 or not 结果.get('ok'):#宿主拒绝
                错=(结果 or {}).get('error') or {}#错误
                自身._合并({'error':错.get('message') if isinstance(错,dict) else str(错)})#整页展示失败
                return#停在失败
            值=结果.get('value') or {}#值
            名=值.get('name')#展示名
            自身._合并({'view':{'id':标识,'title':名 if 名 is not None else 标识,'content':值.get('content') or ''}})#打开查看器
        except Exception as 错误:#传输或未知拒绝
            自身._合并({'error':错误文(错误)})#整页展示拒绝文案

    def closeView(自身):#关掉查看器
        """清查看器。"""
        自身._合并({'view':None})#清

    def beginCopy(自身,源):#打开复制对话框
        """针对一份预设打开复制对话框。"""
        行=next((r for r in 自身.store.getSnapshot().get('rows') or [] if r.get('id')==源),None)#找源行
        标题=(行.get('name') if 行 else None) or 源#源标题
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
        草稿=自身.store.getSnapshot().get('copy')#当前草稿
        if 草稿 is None or 草稿.get('saving'):#未开或已在飞
            return#忽略
        if 草稿阻挡(草稿,自身.store.getSnapshot().get('rows')) is not None:#客户端仍阻挡
            return#忽略
        自身._改草稿({'saving':True,'error':None})#标为提交中
        try:#向宿主复制
            名=(草稿.get('name') or '').strip()#去掉首尾空白的展示名
            载荷={'from':草稿['from'],'agentPreset':草稿['id']}#基础
            if 名!='':#非空展示名
                载荷['name']=名#带上
            应答=解开(自身.接口.agentPresets.copy(载荷))#经线复制
            结果=应答.get('result') if isinstance(应答,dict) else None#信封
            if not 结果 or not 结果.get('ok'):#宿主拒绝
                错=(结果 or {}).get('error') or {}#错误
                自身._改草稿({'saving':False,'error':错.get('message') if isinstance(错,dict) else str(错)})#对话框展示失败
                return#停在对话框
            自身._合并({'copy':None})#关掉对话框
            自身.load()#重读名册
            自身.名册变更()#通知其它面
            自身.openLocation(草稿['id'])#打开或揭示新目录
        except Exception as 错误:#传输或未知拒绝
            自身._改草稿({'saving':False,'error':错误文(错误)})#对话框展示拒绝文案

    def openLocation(自身,标识):#打开或揭示目录
        """宿主已回答且页面已反映。"""
        try:#问宿主打开文档
            应答=解开(自身.接口.agentPresets.openDocument({'agentPreset':标识}))#打开或返回路径
            结果=应答.get('result') if isinstance(应答,dict) else None#信封
            if not 结果 or not 结果.get('ok'):#宿主拒绝
                错=(结果 or {}).get('error') or {}#错误
                自身._合并({'error':错.get('message') if isinstance(错,dict) else str(错)})#整页展示失败
                return#停在失败
            值=结果.get('value') or {}#值
            if 值.get('opened'):#桌面已打开
                return#无需揭示
            路径=值.get('path')#打不开时给出的路径
            揭示=dict(自身.store.getSnapshot().get('revealedPaths') or {})#现有
            揭示[标识]=路径#记到该行
            自身._合并({'revealedPaths':揭示})#写入
        except Exception as 错误:#传输或未知拒绝
            自身._合并({'error':错误文(错误)})#整页展示拒绝文案

    def confirmDelete(自身,标识):#打开或关掉删除确认
        """删除飞行中不改确认。"""
        if 自身.store.getSnapshot().get('deleting'):#删除飞行中
            return#忽略
        自身._合并({'pendingDelete':标识})#记下待删或清掉

    def remove(自身):#执行删除
        """删除已落定且页面已反映。"""
        现=自身.store.getSnapshot()#现
        待删=现.get('pendingDelete')#待删
        if 待删 is None or 现.get('deleting'):#无确认或已在飞
            return#忽略
        自身._合并({'deleting':True,'error':None})#标为删除中
        try:#向宿主删除
            应答=解开(自身.接口.agentPresets.remove({'agentPreset':待删}))#经线删除
            结果=应答.get('result') if isinstance(应答,dict) else None#信封
            if not 结果 or not 结果.get('ok'):#宿主拒绝
                错=(结果 or {}).get('error') or {}#错误
                自身._合并({'deleting':False,'pendingDelete':None,'error':错.get('message') if isinstance(错,dict) else str(错)})#清确认
                return#停在失败
            自身._合并({'deleting':False,'pendingDelete':None})#清删除态
            自身.load()#重读名册
            自身.名册变更()#通知其它面
        except Exception as 错误:#传输或未知拒绝
            自身._合并({'deleting':False,'pendingDelete':None,'error':错误文(错误)})#清确认并展示拒绝

    def makeDefault(自身,标识):#设为默认预设
        """写入已落定且名册已重读。"""
        失败=写默认预设(自身.接口,标识)#经设置面写入
        if 失败 is not None:#写入失败
            自身._合并({'error':失败})#整页展示失败
            return#停在失败
        自身.load()#重读名册以刷新 isDefault
