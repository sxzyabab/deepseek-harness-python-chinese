"""PTC 执行缝词汇：调用方交给运行时的输入与返回。纯类型，无运行时代码。"""
__all__=[#仅中文公开名
    '绑定错误类字段','绑定命名空间字段','运行请求字段','运行规格字段',
    '运行沙箱字段','运行失败字段','运行结果字段','运行失败种类',
]#公开面结束

绑定错误类字段=('name','memberNameProperty')#程序可见拒绝构造器
绑定命名空间字段=('global','functions','errorClass')#一组绑定函数
运行请求字段=('program','bindings','cwd','timeoutMs','sandboxPolicy','signal')#一次程序输入
运行规格字段=('program','bindings','cwd','timeoutMs','sandboxPolicy','signal')#已解析输入，cwd 与 timeoutMs 必填
运行沙箱字段=('mode','denied','enforcement')#文件围栏事实
运行失败种类=('exception','timeout','abort','worker-exit','invalid-output','output-limit','protocol','sandbox-unavailable')#正交失败类
运行失败字段=('kind','message')#失败类与英文细节
运行结果字段=('sandbox','value','logs','error')#一次运行结局
