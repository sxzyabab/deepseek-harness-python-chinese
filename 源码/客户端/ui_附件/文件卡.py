'待上传文件卡：类型图标、名称、大小或状态、移除与重试'
from nicegui import ui as 界面
from ..ui_基础界面组件.文件类型图标 import 文件扩展名,文件类型图标

__all__=['文件卡','文件大小文']

def 文件大小文(字节):
    '按 1024 进位，最多到 GB'
    if isinstance(字节,bool) or not isinstance(字节,(int,float)) or 字节<0:
        return ''
    单位=('B','KB','MB','GB')
    值=float(字节)
    档=0
    while 值>=1024 and 档<len(单位)-1:
        值=值/1024
        档+=1
    if 档==0:
        return str(int(值))+' B'
    return f'{值:.1f} {单位[档]}'

class 文件卡:
    '一张待处理文件：上传中、就绪或失败'
    def __init__(自身,属性):
        '记下名称、字节、状态和回调'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '图标或转圈、名称、状态行、移除；失败时可重试'
        属性=自身.属性
        名称=属性['name'] if isinstance(属性.get('name'),str) and 属性['name']!='' else ''
        字节=属性['bytes'] if 'bytes' in 属性 else 0
        状态=属性['state'] if 属性.get('state') in ('uploading','ready','error') else 'uploading'
        文案=属性['labels'] if isinstance(属性.get('labels'),dict) else {}
        扩展=文件扩展名(名称).upper()[:8]
        if 状态=='uploading':
            辅=文案.get('uploading') or ''
        elif 状态=='error':
            辅=文案.get('failed') or ''
        else:
            大小=文件大小文(字节)
            辅=扩展 if 大小=='' else (扩展+' '+大小 if 扩展!='' else 大小)
        进度=属性.get('progress')
        with 界面.column().classes('file-card'+(' file-card-failed' if 状态=='error' else '')):
            with 界面.row().style('align-items:center;gap:8px;width:100%'):
                if 状态=='uploading':
                    界面.spinner(size='16px')
                else:
                    文件类型图标({'path':名称,'size':28}).渲染()
                with 界面.column().style('min-width:0;gap:0'):
                    界面.label(名称).style('font-size:13px;line-height:18px')
                    if 辅!='':
                        界面.label(辅).style('font-size:12px;line-height:16px;color:var(--dsw-alias-label-tertiary)')
                def 移除():
                    '去掉这张卡'
                    回调=属性.get('onRemove')
                    if callable(回调):
                        回调()
                界面.button(on_click=移除).props('icon=close flat round aria-label="'+(文案.get('remove') or '')+'"')
            if 状态=='error':
                def 重试():
                    '再传一次'
                    回调=属性.get('onRetry')
                    if callable(回调):
                        回调()
                界面.button(文案.get('retry') or '', on_click=重试).props('flat no-caps')
            if 状态=='uploading':
                宽='100%'
                if isinstance(进度,(int,float)) and not isinstance(进度,bool):
                    宽=str(max(0,min(1,float(进度)))*100)+'%'
                界面.element('div').style('height:2px;width:'+宽+';background:var(--dsw-alias-label-primary)')

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
