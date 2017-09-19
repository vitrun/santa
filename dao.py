import time
import json

data_ttl = 60  # seconds


class Doc:
    fields, dic = [], {}

    def __init__(self, **kwargs):
        # import ipdb; ipdb.set_trace()
        for f in self.__class__.fields:
            v = kwargs[f]
            if isinstance(v, bytes):
                v = v.decode('utf8')
            setattr(self, f, v)
        self.id = kwargs.get('id')

    @property
    def dic(self):
        return {k: getattr(self, k) for k in self.fields + ['id']}

    @classmethod
    def get(cls, cli, doc_id):
        doc = cli.hgetall(cls._get_key(doc_id))
        if not doc:
            return None
        dic = {
            k.decode('utf8'): v for k, v in doc.items()
            }
        inst = cls(**dic)
        inst.id = doc_id
        return inst

    @classmethod
    def _get_key(cls, _id):
        return '%s:%d' % (cls.__name__.lower(), _id)

    def save(self, cli):
        self._save(self.dic)
        key = self._get_key(self.id)
        cli.hmset(key, self.dic)

    def _save(self, _):
        #: 持久化到db后返回的id，或派号器生成的id
        self.dic['id'] = self.id = int(time.time() * 1000) % 1505790000000


class Envelope(Doc):
    fields = ['total_cent', 'total_num', 'remain_cent', 'remain_num', 'secret']

    @classmethod
    def has_claimed(cls, cli, user_id, env_id):
        return cli.get('envelope:claimed:%d:%d' % (user_id, env_id))

    @classmethod
    def mark_claimed(cls, cli, user_id, env_id):
        return cli.set('envelope:claimed:%d:%d' % (user_id, env_id), 1)

    @classmethod
    def claim(cls, cli, env_id):
        remain = cli.hincrby(cls._get_key(env_id), 'remain_num', -1)
        return remain >= 0

    def save(self, cli):
        super(Envelope, self).save(cli)
        cli.expire("envelope:expire:%d" % self.id, data_ttl)

    def decr_cent(self, cli, delta):
        cli.hincrby(self._get_key(self.id), 'remain_cent', -delta)


class Claim(Doc):
    fields = ['user_id', 'envelope_id', 'cent']

    def record(self, cli):
        cli.append('envelope:claimed:%d' % self.user_id, json.dumps(self.dic))


class Wallet(Doc):
    fields = ['cent']

    @classmethod
    def incr(cls, client, user_id, delta):
        client.hincrby(cls._get_key(user_id), 'cent', delta)


if __name__ == '__main__':
    import redis

    client = redis.StrictRedis(host='localhost', port=6379, db=0)
    env = Envelope(total_cent=343, total_num=5, remain_cent=38, remain_num=1, secret='8jW39af')
    env.save(client)
    env2 = Envelope.get(client, env.id)
    assert env.id == env2.id
