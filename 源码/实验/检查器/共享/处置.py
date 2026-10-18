'按登记的反序释放检查器资源，最后即使前面失败也关闭源'
import threading


def 处置检查器资源(清理列表,关闭,消息):
    '反序执行每个拆除器，再调用关闭。返回期约时等到结算。失败按释放顺序收成一组'
    失败列表=[]
    动作=list(reversed(list(清理列表)))
    动作.append(关闭)
    for 卸 in 动作:
        try:
            结果=卸()
            然后=getattr(结果,'then',None)
            if callable(然后):
                完成=threading.Event()
                盒子={}

                def 成功(值=None,完成=完成):
                    '期约兑现'
                    完成.set()

                def 失败(错误=None,完成=完成,盒子=盒子):
                    '期约拒绝'
                    if isinstance(错误,BaseException):
                        盒子['错误']=错误
                    elif 错误 is None:
                        盒子['错误']=Exception('rejected')
                    else:
                        盒子['错误']=Exception(str(错误))
                    完成.set()

                然后(成功,失败)
                完成.wait()
                if '错误' in 盒子:
                    raise 盒子['错误']
        except Exception as 错误:
            失败列表.append(错误)
    if len(失败列表)>0:
        raise ExceptionGroup(消息,失败列表)
