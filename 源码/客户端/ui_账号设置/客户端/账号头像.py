'账号身份旁边的头像。没有图片或加载失败时用缺省图标'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件
from ...ui_基础界面组件.icons import 图标用户16

__all__=['账号头像']

样式模块='账号头像'

class 账号头像:
    '共享加载成功后才显示图片，否则是用户图标'
    def __init__(自身,属性):
        '记下头像快照和失败回调'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        'ready 时画图片。出错交给业主，两边一起回到缺省图标'
        窗口=自身.属性['window'] if 'window' in 自身.属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '账号头像样式',
            os.path.join(os.path.dirname(__file__),'账号头像.module.css'),
            样式模块,
        )
        if 自身.根 is not None:
            自身.根.remove()
        头像=自身.属性.get('avatar')
        if isinstance(头像,dict) and 头像.get('status')=='ready':
            图=文档.createElement('img')
            图.className='image'
            图.setAttribute('data-dsh-css',样式模块)
            图.src=头像['url']
            图.alt=''
            图.referrerPolicy='no-referrer'
            def 出错(_事件=None,头像=头像):
                '这一次渲染用的快照失败了才上报'
                失败=自身.属性.get('avatarFailed')
                if 失败 is not None:
                    失败(头像)
            图.addEventListener('error',出错)
            自身.根=图
        else:
            自身.根=图标用户16({'window':窗口,'size':16})
        return 自身.根
