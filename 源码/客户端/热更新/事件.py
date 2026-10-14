'热更新 SSE 帧。键保持英文：type、graph、id、rev'
from .异常 import 热更新错误#本包异常

__all__=['插件事件帧','事件端点','事件路由','解析插件事件帧','热更新错误']#仅中文公开名

事件端点='/plugins/events'#推送 graph/rebuilt 帧的系统 SSE 端点
事件路由=事件端点[1:]#文档相对路径，给页面 EventSource

class 插件事件帧(dict):#SSE 帧映射形状
    '一帧 SSE：连接时的整图，或一条打包重建通知。键：type；graph 帧另有 graph；rebuilt 帧另有 id、rev'

def 解析插件事件帧(值):
    '校验 SSE 载荷。空对象不是合法帧'
    if not isinstance(值,dict):#非对象
        return {'kind':'invalid'}#无效
    种=值.get('type')#类型
    if 种=='rebuilt':#重建
        if isinstance(值.get('id'),str) and isinstance(值.get('rev'),str):#字段
            return {'kind':'frame','frame':{'type':'rebuilt','id':值['id'],'rev':值['rev']}}#帧
        return {'kind':'invalid'}#无效
    if 种=='graph':#图
        if isinstance(值.get('graph'),dict):#对象；空图仍是图
            return {'kind':'frame','frame':{'type':'graph','graph':值['graph']}}#帧
        return {'kind':'invalid'}#无效
    if isinstance(种,str):#未知
        return {'kind':'unknown'}#未知
    return {'kind':'invalid'}#无效
