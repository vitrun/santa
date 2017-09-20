# Santa
A redis based, simple, yet performant red-envelope(红包) solution demo.


### Design
- 内存操作，高并发性能
- FIFO队列，避免锁竞争
- 易于横向拓展


### API
所有API返回结构均为{"status":, "data":, "msg":}, status：状态码，msg:错误提示，data:有效数据（以下data均指此字段）

- GET /user/:id/wallet/, 查看余额
    - param:
    - data: {"cent":, "id":}
- POST /envelop/create/, 发红包
    - param: user_id=&money=&num=
    - data: {"total_cent": , "total_num": , "remain_cent": , "remain_num": , "secret": , "id": }
- POST /envelop/claim/, 抢红包
    - param: user_id=&envelope_id=&secret=
    - data: {"user_id":, "envelope_id":, "cent":, "id":}
- GET /user/:id/envelop/claim/, 查询领到的红包
    - param: start=&limit=
    - data: [{"user_id":, "envelope_id":, "cent":, "id":}]


### Setup
- run redis
- virtualenv pyenv -p python3.6
- source pyenv/bin/activate
- pip install -r requirements.txt
- python server.py
- curl -d 'user_id=1&money=8.5&num=20' 'http://localhost:8080/envelope/create/'


### Test
- python job claim
- nosetests -v test.py


### Todo
- 内存操作后持久化到db，历史数据查询走db
- 改为多队列，便于横向拓展
- 验证redis过期通知的时效性
- authentication
- benchmark
