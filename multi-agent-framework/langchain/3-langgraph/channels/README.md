# langgraph.channels

源码位置：`.venv/Lib/site-packages/langgraph/channels/`

## BaseChannel

这里文档本身说了一个 ***Base class for all channels***

### 参数上：只规定了两种参数

1. key： 顾名思义是隶属于 channel 下参数的名称

2. typ： 顾名思义是隶属于 channel 下参数的type

### 类方法

#### 1. ValueType & UpdateType

规定了两个属性类的参数，这里先按下不表

``` python
@property
@abstractmethod
def ValueType(self) -> Any:
    """The type of the value stored in the channel."""

@property
@abstractmethod
def UpdateType(self) -> Any:
    """The type of the update received by the channel."""
```

#### 2. checkpoint & from_checkpoint & get

这里是关于 checkpointer 的存取过程，关于 checkpointer 的详细定义请看 [checkpoint](../checkpoint/README.md) 这是 langgraph 维护短期记忆的核心部分