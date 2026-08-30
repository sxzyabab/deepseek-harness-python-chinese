"""GoalBar 的注入面类型说明。



对齐上游 `ui-goal/src/client/slots.ts`。公开面仅中文名。

实时目标值经投影到达；inject 只携带变更动词。

"""



__all__=['无当前目标结果']#仅中文公开名



无当前目标结果={#没有当前目标时的失败结果

    'ok':False,#失败

    'error':{'code':'no-current-goal','message':'no current goal to mutate','details':{}},#无当前目标可改

}#结果结束


