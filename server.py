import tornado.ioloop
import tornado.web

from santa import Santa, client
from dao import Wallet


class WalletHandler(tornado.web.RequestHandler):
    def get(self, uid):
        wallet = Wallet.get(client, int(uid))
        self.write(wallet and wallet.dic or {})


class EnvelopeCreationHandler(tornado.web.RequestHandler):
    def post(self):
        #: TODO. get from auth token
        try:
            user_id = int(self.get_argument('user_id'))
            cent = int(float(self.get_argument('money')) * 100)
            num = int(self.get_argument('num'))
            if num > cent:
                self.write({'error': 'num too large'})
                return
            envelope = Santa.create_envelope(user_id, cent, num)
            self.write(envelope.dic)
        except Exception as e:
            self.write({'error': str(e)})


class EnvelopeClaimHandler(tornado.web.RequestHandler):
    def post(self):
        #: TODO. get from auth token
        try:
            user_id = int(self.get_argument('user_id'))
            envelope_id = int(self.get_argument('envelope_id'))
            secret = self.get_argument('secret')
            claim = Santa.claim_envelope(user_id, envelope_id, secret)
            self.write(claim.dic)
        except Exception as e:
            self.write({'error': str(e)})


def make_app():
    return tornado.web.Application([
        (r"/user/(\d+)/wallet", WalletHandler),
        (r"/envelope/create/", EnvelopeCreationHandler),
        (r"/envelope/claim/", EnvelopeClaimHandler),
    ])


if __name__ == '__main__':
    app = make_app()
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()
