"""
验证路由模块

此模块提供了处理验证请求的API路由。
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Body, Query, Path
from pydantic import BaseModel

from ..platform_publisher.verification_dialog import VerificationDialog

logger = logging.getLogger("agentpress")

router = APIRouter(
    prefix="/verification",
    tags=["verification"],
    responses={404: {"description": "Not found"}},
)

class VerificationResult(BaseModel):
    """验证结果模型"""
    code: Optional[str] = None
    text: Optional[str] = None
    action: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

@router.post("/{verification_id}/submit")
async def submit_verification(
    verification_id: str = Path(..., description="验证ID"),
    result: VerificationResult = Body(..., description="验证结果")
):
    """提交验证结果
    
    Args:
        verification_id: 验证ID
        result: 验证结果
        
    Returns:
        操作结果
    """
    try:
        result_dict = result.dict(exclude_none=True)
        success = await VerificationDialog.submit_verification_result(
            verification_id=verification_id,
            result=result_dict
        )
        
        if success:
            return {
                "status": "success",
                "message": "验证结果已提交",
                "verification_id": verification_id
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"提交验证结果失败: {verification_id}"
            )
    except Exception as e:
        logger.error(f"提交验证结果时出错: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"提交验证结果时出错: {str(e)}"
        )

@router.post("/{verification_id}/cancel")
async def cancel_verification(
    verification_id: str = Path(..., description="验证ID"),
    reason: str = Query("user_cancelled", description="取消原因")
):
    """取消验证
    
    Args:
        verification_id: 验证ID
        reason: 取消原因
        
    Returns:
        操作结果
    """
    try:
        success = await VerificationDialog.cancel_verification(
            verification_id=verification_id,
            reason=reason
        )
        
        if success:
            return {
                "status": "success",
                "message": "验证已取消",
                "verification_id": verification_id
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"取消验证失败: {verification_id}"
            )
    except Exception as e:
        logger.error(f"取消验证时出错: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"取消验证时出错: {str(e)}"
        )

@router.get("/{verification_id}/status")
async def get_verification_status(
    verification_id: str = Path(..., description="验证ID")
):
    """获取验证状态
    
    Args:
        verification_id: 验证ID
        
    Returns:
        验证状态
    """
    try:
        import json
        from pathlib import Path
        
        verification_dir = Path("/tmp/promora_verification")
        verification_file = verification_dir / f"verification_{verification_id}.json"
        
        if not verification_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"验证不存在: {verification_id}"
            )
        
        with open(verification_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return {
            "status": "success",
            "verification_id": verification_id,
            "verification_status": data.get("status", "unknown"),
            "verification_type": data.get("type", "unknown"),
            "platform": data.get("platform", "unknown"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取验证状态时出错: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取验证状态时出错: {str(e)}"
        )
