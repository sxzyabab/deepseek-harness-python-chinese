__all__=['派生']

def 派生(源,投影):
    """源快照身份变化才重算。"""
    见过=[None]
    值箱={'ready':False,'value':None}
    def 取快照():
        """身份未变复用。"""
        快照=源['getSnapshot']() if isinstance(源,dict) else 源.getSnapshot()
        if (not 值箱['ready']) or (快照 is not 见过[0]):
            见过[0]=快照
            值箱['value']=投影(快照)
            值箱['ready']=True
        return 值箱['value']
    def 订阅(监听):
        """透传源订阅。"""
        if isinstance(源,dict):
            return 源['subscribe'](监听)
        return 源.subscribe(监听)
    return {'getSnapshot':取快照,'subscribe':订阅}
