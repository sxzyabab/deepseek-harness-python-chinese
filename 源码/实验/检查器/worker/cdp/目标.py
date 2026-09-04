"""同时暴露 Network、Console 与 Sources 所需的最小页面 target CDP 方法。"""
#对齐上游 worker/cdp/target.ts

__all__=['cdp方法未处理','处理脚手架']#仅中文公开名

cdp方法未处理=object()#未处理哨兵

def 处理脚手架(请求,目标):#处理脚手架方法
    """处理一条 Worker 本地身份或页面脚手架方法。"""
    帧={#合成帧
        'id':'dsh-inspector-host-frame',#帧id
        'loaderId':'dsh-inspector-loader',#加载器id
        'url':'dsh://host',#URL
        'domainAndRegistry':'',#域与注册表
        'securityOrigin':'dsh://host',#安全源
        'mimeType':'text/html',#MIME
        'secureContextType':'Secure',#安全上下文
        'crossOriginIsolatedContextType':'NotIsolated',#跨源隔离
        'gatedAPIFeatures':[],#门控API
    }#frame结束
    方法=请求['method']#方法名
    if 方法 in (#空结果族
        'Page.enable','Page.disable','Page.setLifecycleEventsEnabled',#Page
        'Target.setDiscoverTargets','Target.setAutoAttach',#Target
        'Log.enable','Log.disable','Console.enable','Console.disable',#Log/Console
    ):#
        return {}#空结果
    if 方法=='Page.getFrameTree':#帧树
        return {'frameTree':{'frame':帧,'childFrames':[]}}#帧树
    if 方法=='Page.getResourceTree':#资源树
        return {'frameTree':{'frame':帧,'resources':[]}}#资源树
    if 方法=='Page.getNavigationHistory':#导航历史
        return {#历史
            'currentIndex':0,#当前索引
            'entries':[{'id':1,'url':帧['url'],'userTypedURL':帧['url'],'title':目标['title'],'transitionType':'typed'}],#条目
        }#return结束
    if 方法=='Target.getTargetInfo':#目标信息
        return {#信息
            'targetInfo':{#目标
                'targetId':目标['targetId'],#id
                'type':'page',#类型
                'title':目标['title'],#标题
                'url':帧['url'],#URL
                'attached':True,#已附着
                'canAccessOpener':False,#不可访问opener
            },#targetInfo结束
        }#return结束
    if 方法=='Browser.getVersion':#浏览器版本
        return {#版本
            'protocolVersion':'1.3',#协议版本
            'product':'dsh-experimental-inspector/0',#产品
            'revision':'@experimental',#修订
            'userAgent':'dsh-experimental-inspector',#UA
            'jsVersion':'cpython',#JS版本占位
        }#return结束
    return cdp方法未处理#哨兵
