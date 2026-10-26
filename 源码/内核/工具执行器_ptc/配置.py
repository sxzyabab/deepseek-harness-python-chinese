'程序子调用并发；挂载和直接构造共用这一份校验'
from ..工具 import 解析并行上限

__all__=('配置',)#英文槽 Config 不进此表

class 配置模式:
    '校验后的程序子调用并发上限；1 表示串行'
    def 校验数据(自身,数据=None):
        '缺省 10；必须是正整数'
        if 数据 is None:
            数据={}#缺省空配置
        if not isinstance(数据,dict):
            raise TypeError('ptc 工具执行器的配置必须是对象')#给人看的说明
        上限=解析并行上限(数据['maxParallelSubCalls'] if 'maxParallelSubCalls' in 数据 else None)#正整数
        return {'maxParallelSubCalls':上限}#只留这个字段

    def __call__(自身,数据=None):
        '直接构造执行器时走同一份校验'
        return 自身.校验数据(数据)#归一

配置=配置模式()#加载器与构造函数共用
