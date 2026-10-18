__all__=['markdown标签']


def markdown标签(翻译=None):
    '代码块和脚注交给共享 Markdown。字是公共中文表里实际取到的原文'
    return {
        'code':{
            'copyLabel':'复制',
            'copiedLabel':'复制成功',
            'toolbarLabels':{
                'codeLabel':'代码块',
                'wrapLabel':'自动换行',
                'unwrapLabel':'取消自动换行',
            },
        },
        'footnotes':'脚注',
    }
