# callback 贯穿模型输出期间的行为
即 
on_chat_model_start
on_llm_star
on_llm_new_token
on_llm_end
on_llm_error

主要是可以在这里埋点，比如日志之类的，

但是我认为最主要的还是追踪token生成期间的行为，这一点还是比较重要
