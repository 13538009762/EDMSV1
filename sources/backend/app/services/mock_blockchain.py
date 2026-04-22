import hashlib
import time
import random

class MockBlockchainService:
    @staticmethod
    def calculate_hash(content: str) -> str:
        """真实计算：提取文档正文的 SHA-256 指纹"""
        if not content:
            return ""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def mock_notarize_to_chain() -> str:
        """伪造上链：模拟网络延迟，生成逼真的以太坊 TxHash"""
        time.sleep(1.2)  # 刻意停顿1.2秒，让前端转圈圈，体现"正在上链"的高级感
        # 随机生成一个 0x 开头的 64 位字符，长得和真区块链凭证一模一样
        mock_tx_hash = "0x" + "".join(random.choices("0123456789abcdef", k=64))
        return mock_tx_hash
