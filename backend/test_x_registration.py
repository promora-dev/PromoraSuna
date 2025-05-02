"""
测试交互式LLM引导的X账户注册脚本

此脚本用于测试交互式LLM引导系统进行X平台账户注册的功能，
通过调用test_interactive_x_registration模块进行测试。
使用真实邮箱凭据进行测试。
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from promora.platform_publisher.test_interactive_x_registration import test_interactive_x_registration, parse_args

async def main():
    """主函数"""
    args = parse_args()
    
    args.username = "PromoraAI"
    args.email = "feng@promora.ai"  # 使用提供的邮箱
    args.password = "sv#promoraA0601"  # 使用提供的密码
    args.email_address = "feng@promora.ai"  # 用于接收验证码的邮箱
    args.email_password = "sv#promoraA0601"  # 邮箱密码
    args.show_browser = False  # 使用无头模式，避免XServer问题
    args.slow_mo = 200  # 增加操作延迟，便于观察
    
    debug_dir = Path("/tmp/promora_x_registration_test")
    debug_dir.mkdir(exist_ok=True)
    
    print(f"开始测试X账户注册流程，用户名: {args.username}")
    print(f"使用邮箱: {args.email}")
    print(f"调试信息将保存到: {debug_dir}")
    
    account = await test_interactive_x_registration(args)
    
    if account:
        print(f"✅ 测试成功! X账户 {account.username} 注册完成")
        return 0
    else:
        print("❌ 测试失败! 未能完成X账户注册")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
