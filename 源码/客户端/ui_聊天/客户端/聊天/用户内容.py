from ..文案 import 中文,填入

__all__=['用户内容']


class 用户内容:
    '调用方自己的消息行里面的文本、附件和引用。不画消息铬'
    def __init__(自身,属性):
        '记下准备好的内容和图片加载器'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        '文本和附加块进气泡。引用用中文摘要'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        内容=属性.get('content') if isinstance(属性.get('content'),dict) else {}
        文本=内容.get('text') or ''
        附件=内容.get('attachments') if isinstance(内容.get('attachments'),list) else []
        附加块=内容.get('extraBlocks') if isinstance(内容.get('extraBlocks'),list) else []
        引用=内容.get('referenceLabels') if isinstance(内容.get('referenceLabels'),list) else []
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.className='userStack'
        while 自身.根.firstChild is not None:
            自身.根.removeChild(自身.根.firstChild)
        if len(附件)>0:
            行=文档.createElement('div')
            行.className='attachmentRow'
            行.setAttribute('data-message-attachments','')
            for 项 in 附件:
                if isinstance(项,dict) and 项.get('type')=='image' and callable(属性.get('renderSlot')):
                    行.appendChild(属性['renderSlot']('conversation.chat.user.images',{
                        'images':[项.get('image')],
                        'loadImage':属性.get('loadImage'),
                        'align':'end',
                        'compact':len(附件)>1,
                        'window':窗口,
                    }) or 文档.createElement('span'))
                elif isinstance(项,dict) and isinstance(项.get('file'),dict):
                    卡=文档.createElement('span')
                    卡.className='fileCard'
                    卡.setAttribute('title',项['file'].get('name') or '')
                    名=文档.createElement('span')
                    名.className='fileName'
                    名.textContent=项['file'].get('name') or ''
                    卡.appendChild(名)
                    行.appendChild(卡)
            自身.根.appendChild(行)
        if 文本!='' or len(附加块)>0:
            泡=文档.createElement('div')
            泡.className='bubble'
            if 文本!='' and callable(属性.get('renderFactorySlot')):
                泡.appendChild(属性['renderFactorySlot']('conversation.user.text',{
                    'text':文本,
                    'facts':属性.get('facts'),
                    'interactive':属性.get('interactive') is True,
                    'ellipsis':属性.get('ellipsis') is True,
                    'window':窗口,
                }) or 文档.createTextNode(文本))
            elif 文本!='':
                泡.appendChild(文档.createTextNode(文本))
            for 块 in 附加块:
                标=文档.createElement('div')
                标.textContent=中文['message.extraBlock']
                泡.appendChild(标)
            自身.根.appendChild(泡)
        if len(引用)>0:
            摘要=文档.createElement('div')
            摘要.className='referenceSummary'
            摘要.textContent=填入(中文['message.referenceSummary'],{
                'labels':中文['message.referenceSeparator'].join(str(项) for 项 in 引用),
            })
            自身.根.appendChild(摘要)
        if 属性.get('parent') is not None and 自身.根.parentNode is None:
            属性['parent'].appendChild(自身.根)
        return 自身.根
