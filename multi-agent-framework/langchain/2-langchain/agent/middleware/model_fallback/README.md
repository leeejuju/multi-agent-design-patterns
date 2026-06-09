# model fall back
```text
"""
Automatic fallback to alternative models on errors.

Retries failed model calls with alternative models in sequence until
success or all models exhausted. Primary model specified in `create_agent`.

简单来说就是自动 fallback。当模型访问发生错误时，系统会自动替换到其他 fallback 模型。

如果你提供了多个 fallback，它就会按照顺序一直执行，直到其中一个有效，或者全部失败为止


"""
```

```python
first_model: str | BaseChatModel,
*additional_models: str | BaseChatModel, 这个也没有什么好说的
```
