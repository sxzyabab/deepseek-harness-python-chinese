'domonic.javascript.Promise的中文封装'
from domonic.javascript import Promise#期约

__all__=['PromiseEX']#模块导出

class PromiseEX(Promise):
    '一次性的结算。调用方使用中文名，状态仍写在原文上'
    def __init__(自身,函数=None,*位置参数,**关键字参数):
        '构造期约。传入函数时，原文把解决和拒绝交给它'
        Promise.__init__(自身,函数,*位置参数,**关键字参数)#可变参数是原文签名

    @property
    def 数据(自身):
        '结算后的值'
        return 自身.data#数据

    @数据.setter
    def 数据(自身,值):
        '写入结算值'
        自身.data=值#数据

    @property
    def 状态(自身):
        'pending、fulfilled或rejected'
        return 自身.state#状态

    @状态.setter
    def 状态(自身,值):
        '写入状态'
        自身.state=值#状态

    def 然后(自身,函数,当已拒绝=None):
        '兑现后调用函数。拒绝时可以另给一个函数'
        return 自身.then(函数,当已拒绝)#然后

    def 捕获(自身,错误):
        '拒绝后调用'
        return 自身.catch(错误)#捕获

    def 最终(自身,当最终):
        '无论兑现还是拒绝，结算后都调用'
        return 自身.finally_(当最终)#最终

    def 解决(自身,数据=None):
        '以数据兑现'
        return 自身.resolve(数据)#解决

    def 拒绝(自身,错误=None):
        '以错误拒绝'
        return 自身.reject(错误)#拒绝

    @staticmethod
    def 全部(可迭代):
        '全部兑现才兑现。有一个拒绝就拒绝'
        return Promise.all(可迭代)#全部

    @staticmethod
    def 全部已结算(可迭代):
        '每一个都结算后兑现，并带上各自的状态'
        return Promise.allSettled(可迭代)#全部已结算

    @staticmethod
    def 竞速(可迭代):
        '谁先结算就跟谁'
        return Promise.race(可迭代)#竞速

    @staticmethod
    def 任一(可迭代):
        '谁先兑现就跟谁。全部拒绝才拒绝'
        return Promise.any(可迭代)#任一

词元={#英到中，按词元而不是整个名字
    'Promise':'期约',
    'data':'数据',
    'state':'状态',
    'then':'然后',
    'catch':'捕获',
    'finally':'最终',
    'resolve':'解决',
    'reject':'拒绝',
    'all':'全部',
    'Settled':'已结算',
    'race':'竞速',
    'any':'任一',
    'func':'函数',
    'onrejected':'当已拒绝',
    'onfinally':'当最终',
    'error':'错误',
    'iterable':'可迭代',
}
