# model retry

```text
 """Middleware that automatically retries failed model calls with configurable backoff.Supports retrying on specific exceptions and exponential backoff.
```


这玩意儿是说 ModelRetryMiddleware，这是一个重试中间件。

这两个场景：

1. 一些指定的，或者说指定的一个 exception
2. 在指定的回调时间里，不断退避的时间 这种两个进行重 call 


```python
def __init__(
    self,
    *,
    max_retries: int = 2,
    retry_on: RetryOn = (Exception,),
    on_failure: OnFailure = "continue",
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> None:
```

提供了很多个参数，对于它的重试机制，其实有点意思。

1. max_try：顾名思义，就是最多尝试几次。
2. retry：也很简单，比如在发生什么样的情况时进行重试。

而且它在 retry 的时候，提供了好几个类型，比如 error 和 continue

然后就是关于 on_failure_retry 和 on_failure。

其实我觉得它代表的是 behavior when all retries are exhausted。on_failure 说的就是当所有的 retry 次数耗尽的时候应该怎么做。

它提供了三个选项：
1. continue：跳过并继续，就像忽略 error 一样
2. raise exception：抛出异常
3. custom callable：可以自己去做一些截断处理



我最最好奇的是它 decay 的机制。

因为一般来说，我其实没有考虑那么深，通常可能会固定间隔一秒或两秒。但它不一样，它提供了四个参数，其中一个是 backoff factor（回退因子）。它是以 2 为底数，根据 retry 的次数来延长 retry 的时间间隔。


然后它每次的 wait 时间长是 initial decay，然后乘以 backoff，然后是2次方的 retry number 

initial_delay * (backoff_factor ** retry_number)


然后他同时设置了 max decay，也是为了防止等待的时长无限延伸

jitter: Whether to add random jitter (`±25%`) to delay to avoid thundering herd.

设置了 Jitter。Jitter 在 CV 里面是一个颜色的抖动，它本身也是“抖动”的意思。

它这样设计是为了保证在有 100 个或者更多请求时，这 100 个请求不会在同一时间间隔内全部打过来。可能就会是类似于好几个波次，比如说：
1. 10秒有一波
2. 20秒一波
3. 30秒一波

这类似于 Redis 在设置时，为了防止缓存雪崩和缓存穿透所做的处理。

should_retry_exception

另一个特点就是它的 retry_on 参数。

关于 retry_on，它的逻辑是这样的：
1. 处理逻辑：
   它会根据 should_retry_exception 来判断。当发生 exception 时，它提供了一个函数来包装处理逻辑。
   
2. 类型判断：
   retry_on 支持多种类型，它本身可以是一个 Callable（可调用对象），也可以是一个元组（tuple）。因此代码里做了一些判断：
   (a) 如果 retry_on 是一个 Callable，它会直接调用这个函数去处理 exception。
   (b) 如果它不是 Callable，那么它必须是一个元组。如果既不是 Callable 也不是元组，程序就会报错。
   (c) 如果是元组，它还会进一步校验 exception 是否在元组定义的类型范围内。如果不是，同样会报错。




calculate_delay然后他又看了一下 calculate_delay 函数。这个函数的主要作用是真正计算当前的 delay，它会根据之前的 backoff factor 和 jitter 等因素来计算。

为了防止延迟过长，计算结果不能超过 max_delay 设定的 60 秒。

```python
if jitter and delay > 0:
        jitter_amount = delay * 0.25  # ±25% jitter
        delay += random.uniform(-jitter_amount, jitter_amount)  # noqa: S311
        # Ensure delay is not negative after jitter
        delay = max(0, delay)
```

看了一下，它这个比较有意思：在当前存在 jitter 和 delay 的时候，它会先算一下当前 delay 的 25% 是多少，然后在 25% 的范围内对 delay 进行调整（可能增加也可能减少），最终返回的还是那个 delay
