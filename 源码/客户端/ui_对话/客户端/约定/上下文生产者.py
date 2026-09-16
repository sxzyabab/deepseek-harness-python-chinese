__all__=['上下文角色','已知上下文形态']#仅中文公开名

上下文角色=('inject','recall')#inject 为生产者供给；recall 为跨会话召回。插话走独立事件，不到这里

已知上下文形态=('instructions','catalog','snapshot','notice','relay','recall')#本 UI 版本会呈现的耐久形态

#上下文生产者视图：role 为上下文角色；label 为行头生产者名，无可读 kind 时为 None
