__all__=['数学兼容']

def 数学兼容():
    'TeX 反斜杠定界符和同一行的双美元块。micromark 不在这棵树里，这里只交出要登记的构造名'
    return {
        'flow':{
            'backslash':'backslashMathFlow',
            'dollar':'sameLineDollarMathFlow',
        },
        'text':{'backslash':'backslashMathText'},
        '定界':(
            ('\\(','\\)'),
            ('\\[','\\]'),
            ('$$','$$'),
        ),
    }
