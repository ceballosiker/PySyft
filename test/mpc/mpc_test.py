import unittest
import torch
import syft as sy
from syft.mpc import spdz
from syft.core.frameworks.torch import _GeneralizedPointerTensor, _MPCTensor


def _generate_mpc_number_pair(self, n1, n2):
    mpcs = []
    for i in [n1, n2]:
        x = torch.LongTensor([i])
        enc = spdz.encode(x)
        x_alice, x_bob = spdz.share(enc)
        x_alice.send(self.alice)
        x_bob.send(self.bob)
        x_pointer_tensor_dict = {self.alice: x_alice.child, self.bob: x_bob.child}
        x_gp = _GeneralizedPointerTensor(x_pointer_tensor_dict).on(x)
        mpcs.append(_MPCTensor(x_gp))
    return mpcs

class TestMPCTensor(unittest.TestCase):
    def setUp(self):
        self.hook = sy.TorchHook(verbose=True)

        me = self.hook.local_worker
        me.is_client_worker = False

        self.bob = sy.VirtualWorker(id="bob", hook=self.hook, is_client_worker=False)
        self.alice = sy.VirtualWorker(id="alice", hook=self.hook, is_client_worker=False)

        me.add_workers([self.bob, self.alice])
        self.bob.add_workers([me, self.alice])
        self.alice.add_workers([me, self.bob])

    def generate_mpc_number_pair(self, n1, n2):
        return _generate_mpc_number_pair(self, n1, n2)

    def mpc_sum(self, n1, n2):
        x_mpc, y_mpc = self.generate_mpc_number_pair(n1, n2)
        sum_mpc = x_mpc + y_mpc
        sum_mpc = sum_mpc.get()
        assert torch.eq(sum_mpc, torch.LongTensor([n1 + n2])).all()

    def test_mpc_sum(self):
        self.mpc_sum(3, 5)
        self.mpc_sum(4, 0)
        self.mpc_sum(5, -5)
        self.mpc_sum(3, -5)
        self.mpc_sum(2 ** 24, 2 ** 12)

    def mpc_mul(self, n1, n2):
        x_mpc, y_mpc = self.generate_mpc_number_pair(n1, n2)
        mul_mpc = x_mpc * y_mpc
        mul_mpc = mul_mpc.get()
        assert torch.eq(mul_mpc, torch.LongTensor([n1 * n2])).all(), (mul_mpc, 'should be', torch.LongTensor([n1 * n2]))

    def test_mpc_mul(self):
        self.mpc_mul(3, 5)
        self.mpc_mul(4, 0)
        self.mpc_mul(5, -5)
        self.mpc_mul(3, 5)
        self.mpc_mul(2 ** 12, 2 ** 12)

if __name__ == '__main__':
    unittest.main()
