from ...依赖.schemastery import 布尔字段

__all__=['配置','上手引导配置全局键']

配置={'credentialOnboarding':布尔字段(默认值=True)}#校验宿主配置及其公开页引导载荷
上手引导配置全局键='__DSH_MODELS_ONBOARDING__'#仅携带公开引导选项的页全局键
