"""
注册路由模块

此模块提供了处理账户注册请求的API路由。
"""

import logging
import os
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Body, Query
from pydantic import BaseModel, Field

from ..platform_publisher.human_registration import HumanRegistration
from ..platform_publisher.models import PlatformAccount, PlatformType
from ..platform_publisher.verification_dialog import VerificationDialog
from .router import get_platform_publisher

logger = logging.getLogger("agentpress")

router = APIRouter(
    prefix="/platform/human_register",
    tags=["platform"],
    responses={404: {"description": "Not found"}},
)

class RegistrationRequest(BaseModel):
    """注册请求模型"""
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")
    display_name: Optional[str] = Field(None, description="显示名称")
    custom_email_credentials: Optional[Dict[str, Any]] = Field(None, description="自定义邮箱凭据")

class RegistrationResponse(BaseModel):
    """注册响应模型"""
    status: str = Field(..., description="注册状态")
    message: str = Field(..., description="注册消息")
    account: Optional[Dict[str, Any]] = Field(None, description="账户信息")
    verification_id: Optional[str] = Field(None, description="验证ID")
    screenshots: Optional[List[str]] = Field(None, description="截图路径列表")

@router.post("/x", response_model=RegistrationResponse)
async def human_register_x_account(
    request: RegistrationRequest = Body(...),
    platform_publisher = Depends(get_platform_publisher)
):
    """使用人类行为模拟注册X账户
    
    Args:
        request: 注册请求
        platform_publisher: 平台发布器
        
    Returns:
        注册响应
    """
    try:
        email_address = None
        email_password = None
        email_provider = "gmail"
        
        if request.custom_email_credentials:
            email_address = request.custom_email_credentials.get("email")
            email_password = request.custom_email_credentials.get("password")
            email_provider = request.custom_email_credentials.get("provider", "gmail")
        else:
            email_address = os.environ.get("EMAIL_ADDRESS")
            email_password = os.environ.get("EMAIL_PASSWORD")
            email_provider = os.environ.get("EMAIL_PROVIDER", "gmail")
        
        human_registration = HumanRegistration(
            browser_tool=platform_publisher.browser_tool,
            email_address=email_address,
            email_password=email_password,
            email_provider=email_provider
        )
        
        account = await human_registration.register_x_account(
            username=request.username,
            email=request.email,
            password=request.password,
            display_name=request.display_name
        )
        
        if account:
            platform_publisher.account_manager.add_account(account)
            
            return RegistrationResponse(
                status="success",
                message=f"成功注册X账户: {account.username}",
                account=account.dict(),
                screenshots=[]  # 可以添加截图路径
            )
        else:
            return RegistrationResponse(
                status="failed",
                message="X账户注册失败，请检查日志获取详细信息",
                screenshots=[]  # 可以添加截图路径
            )
    except Exception as e:
        logger.error(f"注册X账户时出错: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"注册X账户时出错: {str(e)}"
        )

@router.post("/zhihu", response_model=RegistrationResponse)
async def human_register_zhihu_account(
    request: RegistrationRequest = Body(...),
    platform_publisher = Depends(get_platform_publisher)
):
    """使用人类行为模拟注册知乎账户
    
    Args:
        request: 注册请求
        platform_publisher: 平台发布器
        
    Returns:
        注册响应
    """
    try:
        email_address = None
        email_password = None
        email_provider = "gmail"
        
        if request.custom_email_credentials:
            email_address = request.custom_email_credentials.get("email")
            email_password = request.custom_email_credentials.get("password")
            email_provider = request.custom_email_credentials.get("provider", "gmail")
        else:
            email_address = os.environ.get("EMAIL_ADDRESS")
            email_password = os.environ.get("EMAIL_PASSWORD")
            email_provider = os.environ.get("EMAIL_PROVIDER", "gmail")
        
        human_registration = HumanRegistration(
            browser_tool=platform_publisher.browser_tool,
            email_address=email_address,
            email_password=email_password,
            email_provider=email_provider
        )
        
        account = await human_registration.register_zhihu_account(
            username=request.username,
            email=request.email,
            password=request.password,
            display_name=request.display_name
        )
        
        if account:
            platform_publisher.account_manager.add_account(account)
            
            return RegistrationResponse(
                status="success",
                message=f"成功注册知乎账户: {account.username}",
                account=account.dict(),
                screenshots=[]  # 可以添加截图路径
            )
        else:
            return RegistrationResponse(
                status="failed",
                message="知乎账户注册失败，请检查日志获取详细信息",
                screenshots=[]  # 可以添加截图路径
            )
    except Exception as e:
        logger.error(f"注册知乎账户时出错: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"注册知乎账户时出错: {str(e)}"
        )
