import importlib.resources as 包资源

__all__=[
    '基线样式','滚动条样式','设计平台样式','代码高亮样式','渐变阴影样式','字号令牌样式',
    '主题样式合计','样式文件名','说明',
]

说明='本包 `客户端/样式/` 已落盘全部分片；浏览器半按序注入 主题样式合计。'

样式文件名=(
    '基线.css',
    '设计平台_静态色.css',
    '设计平台_别名令牌.css',
    '渐变阴影.css',
    '字号令牌.css',
    '代码高亮.css',
    '滚动条.css',
)

def 读样式(文件名):
    '按 utf-8 读本包样式目录下的分片。打不开时异常文案只有样式读不到。'
    try:
        return 包资源.files(__package__).joinpath('样式',文件名).read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None

基线样式=读样式('基线.css')#base.css
设计平台样式=读样式('设计平台_静态色.css')+'\n'+读样式('设计平台_别名令牌.css')#design-platform 两片
渐变阴影样式=读样式('渐变阴影.css')#gradient/shadow
字号令牌样式=读样式('字号令牌.css')#font tokens
代码高亮样式=读样式('代码高亮.css')#shiki
滚动条样式=读样式('滚动条.css')#scrollbar 全文

主题样式合计='\n'.join([#浏览器半一次注入用
    基线样式,#基线
    设计平台样式,#设计平台
    渐变阴影样式,#渐变阴影
    字号令牌样式,#字号
    代码高亮样式,#代码高亮
    滚动条样式,#滚动条
])#合计结束
