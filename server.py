import tornado.ioloop
import tornado.web

from santa import Santa, client
from dao import Wallet, Claim


class BaseHandler(tornado.web.RequestHandler):
    def done(self, data=None, status=0, msg=''):
        self.write({
            'status': status,
            'data': data or {},
            'msg': msg
        })


class WalletHandler(BaseHandler):
    def get(self, uid):
        wallet = Wallet.get(client, int(uid))
        self.done(wallet and wallet.dic or {})


class EnvelopeHandler(BaseHandler):
    def post(self):
        #: TODO. get from auth token
        try:
            user_id = int(self.get_argument('user_id'))
            cent = int(float(self.get_argument('money')) * 100)
            num = int(self.get_argument('num'))
            if num > cent:
                self.done(msg='num too large')
                return
            envelope = Santa.create_envelope(user_id, cent, num)
            self.write(envelope.dic)
        except Exception as e:
            self.done(msg=str(e))


class ClaimHandler(BaseHandler):
    def post(self):
        #: TODO. get from auth token
        try:
            user_id = int(self.get_argument('user_id'))
            envelope_id = int(self.get_argument('envelope_id'))
            secret = self.get_argument('secret')
            claim = Santa.claim_envelope(user_id, envelope_id, secret)
            self.done(data=claim.dic)
        except Exception as e:
            self.done(msg=str(e))


class ClaimListHandler(BaseHandler):
    def get(self, user_id):
        #: TODO. get from auth token
        try:
            start = int(self.get_argument('start'))
            limit = int(self.get_argument('limit', 12))
            claims = Claim.query(client, user_id, start, limit)
            self.done(data=[c.dic for c in claims])
        except Exception as e:
            self.done(msg=str(e))


def make_app():
    return tornado.web.Application([
        (r"/user/(\d+)/wallet/", WalletHandler),
        (r"/envelope/create/", EnvelopeHandler),
        (r"/envelope/claim/", ClaimHandler),
        (r"/user/(\d+)/envelope/claim/", ClaimListHandler),
    ])


if __name__ == '__main__':
    app = make_app()
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()
