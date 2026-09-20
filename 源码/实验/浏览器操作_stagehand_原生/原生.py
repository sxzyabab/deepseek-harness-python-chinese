import json,base64#结果与截图
from ...工具.值 import 断言永不#封闭联合
from ...工具.超时 import 若已中止则抛出#中止
from stagehand import Stagehand,localBrowser

__all__=['浏览器输入','浏览器方法','stagehand排空错误','打开原生浏览器','stagehand模型模式']#仅中文公开名

class stagehand排空错误(Exception):#SDK 未排空
    """SDK 请求在连接工作者终止前未排空。"""

def 校验模型(模型):#显式凭据
    """固定版本 SDK 接受的一份模型凭据。"""
    if not isinstance(模型,dict):#非对象
        raise Exception('Stagehand 需要非空的模型 API 密钥')
    名=模型.get('modelName')#名
    钥=模型.get('apiKey')#钥
    if not isinstance(名,str) or not isinstance(钥,str) or len(钥.strip())==0:#空白钥
        raise Exception('Stagehand 需要非空的模型 API 密钥')
    结果={'modelName':名,'apiKey':钥}#模型
    if 模型.get('headers') is not None:#头
        结果['headers']=模型['headers']#头
    return 结果#模型

stagehand模型模式=校验模型#配置变换

def 解析页参数(参数):#可选 pageId
    """可选 pageId。"""
    页=参数.get('pageId') if isinstance(参数,dict) else None#页
    if 页 is not None and (not isinstance(页,str) or len(页)<1):#非法
        raise Exception('Stagehand 浏览器标签页不可用；请列出标签页以选择当前 pageId')
    return 页#页

def 解析导航(参数):#navigate
    """navigate 参数。"""
    if not isinstance(参数,dict) or not isinstance(参数.get('url'),str):#非法
        raise Exception('Stagehand 浏览器操作')
    return {'pageId':解析页参数(参数),'url':参数['url']}#参数

def 解析标签(参数):#tabs
    """tabs 参数。"""
    if not isinstance(参数,dict):#非法
        raise Exception('Stagehand 浏览器操作')
    动作=参数.get('action')#动作
    if 动作=='list':#列
        return {'action':'list'}#参数
    if 动作=='new':#新
        return {'action':'new','url':参数.get('url')}#参数
    if 动作=='select' or 动作=='close':#选/关
        页=参数.get('pageId')#页
        if not isinstance(页,str) or len(页)<1:#非法
            raise Exception('Stagehand 浏览器标签页不可用；请列出标签页以选择当前 pageId')
        return {'action':动作,'pageId':页}#参数
    raise Exception('Stagehand browser operation')#失败

def 解析截图(参数):#screenshot
    """screenshot 参数。"""
    if not isinstance(参数,dict):#非法
        raise Exception('Stagehand 浏览器操作')
    if 'fullPage' not in 参数:#缺省
        整页=False#否
    else:
        整页=参数['fullPage']#整页
    return {'pageId':解析页参数(参数),'fullPage':bool(整页)}#参数

def 解析指令(参数):#act/observe
    """带 instruction 的参数。"""
    if not isinstance(参数,dict) or not isinstance(参数.get('instruction'),str) or len(参数['instruction'])<1:#非法
        raise Exception('Stagehand 浏览器操作')
    结果={'pageId':解析页参数(参数),'instruction':参数['instruction']}#参数
    if 'schema' in 参数:#extract
        结果['schema']=参数['schema']#模式
    return 结果#参数

浏览器输入={#方法 → 解析
    'navigate':解析导航,#导航
    'tabs':解析标签,#标签
    'screenshot':解析截图,#截图
    'act':解析指令,#动作
    'observe':解析指令,#观察
    'extract':解析指令,#提取
}#输入
浏览器方法=tuple(浏览器输入.keys())#封闭方法集

def 文本结果(值):#MCP 文本
    """规范 MCP 文本结果。"""
    return {'content':[{'type':'text','text':json.dumps(值,ensure_ascii=False)}]}#文本

def 选页(浏览器,页id):#当前或指定页
    """按 pageId 或活动页选取标签。"""
    上下文=浏览器.context#上下文
    if 页id is None:#活动
        页=上下文.activePage()#活动
    else:#指定
        页=None#候选
        for 候选 in 上下文.pages():#逐页
            if 候选.pageId==页id:#命中
                页=候选#记下
                break#停
    if 页 is None:#不可用
        raise Exception('Stagehand 浏览器标签页不可用；请列出标签页以选择当前 pageId')
    return 页#页

def 打开原生浏览器(配置):#公开初始化
    """用公开初始化与原生模型配置打开固定版本 SDK。宿主另拥有已启动的 Chromium；本工作者只拥有其 CDP 连接。"""
    浏览器=localBrowser.connect({#连接
        'cdpUrl':配置['cdpEndpoint'],#端点
        **({} if 'extensionId' not in 配置 else {'extensionId':配置['extensionId']}),#扩展
    })#连接结束
    stagehand=Stagehand.create({'browser':浏览器,'model':配置['model'],'logging':{'level':'off'}})#SDK
    def 关():#关 SDK
        """释放 Stagehand 状态。"""
        stagehand.close()#关
    def 执行(方法,原始参数,信号=None):#一次操作
        """校验参数后执行一次操作。"""
        若已中止则抛出(信号)#中止
        if 方法=='navigate':#导航
            参数=浏览器输入['navigate'](原始参数)#参数
            页=选页(浏览器,参数.get('pageId'))#页
            页.goto(参数['url'],{'timeout':配置['operationTimeoutMs']})#超时
            return 文本结果({'pageId':页.pageId,'url':页.url(),'title':页.title()})#结果
        if 方法=='tabs':#标签
            参数=浏览器输入['tabs'](原始参数)#参数
            上下文=浏览器.context#上下文
            if 参数['action']=='new':#新
                上下文.newPage(参数.get('url'))#新
            if 参数['action']=='select':#选
                上下文.setActivePage(选页(浏览器,参数.get('pageId')))#选
            if 参数['action']=='close':#关
                选页(浏览器,参数.get('pageId')).close()#关
            活动=上下文.activePage()#活动
            标签表=[]#列表
            for 页 in 上下文.pages():#逐页
                标签表.append({'pageId':页.pageId,'url':页.url(),'title':页.title(),'active':页.pageId==(活动.pageId if 活动 is not None else None)})#项
            return 文本结果({'tabs':标签表})#结果
        if 方法=='screenshot':#截图
            参数=浏览器输入['screenshot'](原始参数)#参数
            页=选页(浏览器,参数.get('pageId'))#页
            字节=页.screenshot({'type':'png','fullPage':参数['fullPage']})#截
            return {'content':[#内容
                {'type':'text','text':'Screenshot of tab '+str(页.pageId)+'.'},#文本
                {'type':'image','data':base64.b64encode(字节 if isinstance(字节,(bytes,bytearray)) else bytes(字节)).decode('ascii'),'mimeType':'image/png'},#图
            ]}#结果
        if 方法=='act':#动作
            参数=浏览器输入['act'](原始参数)#参数
            结果=stagehand.act(参数['instruction'],{'page':选页(浏览器,参数.get('pageId')),'timeout':配置['operationTimeoutMs']})#超时
            if not 结果['data']['success']:#失败
                raise Exception(结果['data']['message'])#失败
            return 文本结果(结果)#结果
        if 方法=='observe':#观察
            参数=浏览器输入['observe'](原始参数)#参数
            return 文本结果(stagehand.observe(参数['instruction'],{'page':选页(浏览器,参数.get('pageId')),'timeout':配置['operationTimeoutMs']}))#超时
        if 方法=='extract':#提取
            参数=浏览器输入['extract'](原始参数)#参数
            选项={'page':选页(浏览器,参数.get('pageId')),'timeout':配置['operationTimeoutMs']}#超时
            if 'schema' not in 参数:#无模式
                结果=stagehand.extract(参数['instruction'],选项)#提取
            else:#有模式
                结果=stagehand.extract(参数['instruction'],参数['schema'],选项)#提取
            return 文本结果(结果)#结果
        return 断言永不(方法,'Stagehand browser operation')#穷尽
    return {'execute':执行,'close':关}#运行时
