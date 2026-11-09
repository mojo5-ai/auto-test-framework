"""
测试数据生成器

基于 Faker 库，提供常用的测试数据生成方法。
支持中文语境的数据生成。

用法：
    from utils.data_generator import DataGenerator
    dg = DataGenerator()
    user = dg.user()  # 生成随机用户数据
"""

from faker import Faker


class DataGenerator:
    """测试数据生成器，封装 Faker 常用方法"""

    def __init__(self, locale: str = "zh_CN"):
        """
        Args:
            locale: 语言区域，默认中文
        """
        self.fake = Faker(locale)

    def username(self, prefix: str = "test_user") -> str:
        """生成随机用户名"""
        return f"{prefix}_{self.fake.user_name()[:12]}"

    def password(self, length: int = 12) -> str:
        """
        生成符合安全要求的密码
        包含大小写字母、数字和特殊字符
        """
        base = self.fake.password(length=length)
        # 确保包含特殊字符
        if not any(c in "!@#$%^&*" for c in base):
            base = base[:-1] + "!Aa1"
        return base

    def email(self, domain: str = "example.com") -> str:
        """生成测试邮箱"""
        return self.fake.email(domain=domain)

    def phone(self) -> str:
        """生成中国大陆手机号（仅用于测试）"""
        return self.fake.phone_number()

    def address(self) -> str:
        """生成随机地址"""
        return self.fake.address()

    def company_name(self) -> str:
        """生成随机公司名"""
        return self.fake.company()

    def sentence(self) -> str:
        """生成随机句子"""
        return self.fake.sentence()

    def user(self, **kwargs) -> dict:
        """
        生成完整的用户测试数据

        Args:
            **kwargs: 可覆盖默认字段，如 username="admin"

        Returns:
            dict: {"username": ..., "password": ..., "email": ..., "phone": ...}
        """
        data = {
            "username": self.username(),
            "password": self.password(),
            "email": self.email(),
            "phone": self.phone(),
        }
        data.update(kwargs)
        return data