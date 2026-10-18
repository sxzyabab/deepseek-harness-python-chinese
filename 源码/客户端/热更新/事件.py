'热更新 SSE 帧。键保持英文：type、graph、id、rev、kind、frame'

__all__=['事件端点','事件路由','解析插件事件帧']#本模块公开名

事件端点='/plugins/events'#推送 graph 与 rebuilt 帧的系统 SSE 端点
事件路由=事件端点[1:]#文档相对路径，给页面 EventSource

def 解析插件事件帧(值):
    '校验帧外壳。完整图由模块控制器在更新索引前再解析'
    if not isinstance(值,dict):#数组和标量都不是对象帧
        return {'kind':'invalid'}#无效
    种类=值.get('type')#帧类型
    if 种类=='rebuilt':#重建通知
        if isinstance(值.get('id'),str) and isinstance(值.get('rev'),str):#id 与 rev 都是字符串
            return {'kind':'frame','frame':{'type':'rebuilt','id':值['id'],'rev':值['rev']}}#帧
        return {'kind':'invalid'}#已知类型但字段不对
    if 种类=='graph':#整图
        图=值.get('graph')#图载荷
        if isinstance(图,(dict,list)):#对象或数组；null 不是图
            return {'kind':'frame','frame':{'type':'graph','graph':图}}#帧
        return {'kind':'invalid'}#图字段不对
    if isinstance(种类,str):#向前兼容的未知类型
        return {'kind':'unknown'}#未知
    return {'kind':'invalid'}#没有字符串类型
