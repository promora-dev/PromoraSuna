"""
Account manager for platform publishing in Promora.

This module provides functionality for managing platform accounts.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logger import logger
from .models import PlatformAccount, PlatformType


class AccountManager:
    """Manager for platform accounts."""
    
    def __init__(self, accounts_file: Optional[str] = None):
        """Initialize the account manager.
        
        Args:
            accounts_file: Path to the accounts file
        """
        self.accounts_file = accounts_file or os.path.join(os.path.dirname(__file__), "accounts.json")
        self.accounts: Dict[PlatformType, Dict[str, PlatformAccount]] = {
            PlatformType.X: {},
            PlatformType.LINKEDIN: {},
            PlatformType.MEDIUM: {},
            PlatformType.ZHIHU: {}
        }
        self._load_accounts()
    
    def _load_accounts(self) -> None:
        """Load accounts from the accounts file."""
        if not os.path.exists(self.accounts_file):
            logger.warning(f"Accounts file not found: {self.accounts_file}")
            return
        
        try:
            with open(self.accounts_file, "r") as f:
                accounts_data = json.load(f)
            
            for platform_str, accounts in accounts_data.items():
                try:
                    platform = PlatformType(platform_str)
                    for account_id, account_data in accounts.items():
                        account = PlatformAccount(
                            account_id=account_id,
                            platform=platform,
                            username=account_data["username"],
                            display_name=account_data.get("display_name"),
                            auth_type=account_data["auth_type"],
                            auth_data=account_data["auth_data"],
                            last_used=datetime.fromisoformat(account_data["last_used"]) if account_data.get("last_used") else None,
                            usage_count=account_data.get("usage_count", 0),
                            status=account_data.get("status", "active")
                        )
                        self.accounts[platform][account_id] = account
                except ValueError:
                    logger.warning(f"Invalid platform: {platform_str}")
        except Exception as e:
            logger.error(f"Error loading accounts: {e}")
    
    def _save_accounts(self) -> None:
        """Save accounts to the accounts file."""
        accounts_data = {}
        
        for platform, platform_accounts in self.accounts.items():
            accounts_data[platform.value] = {}
            for account_id, account in platform_accounts.items():
                accounts_data[platform.value][account_id] = {
                    "username": account.username,
                    "display_name": account.display_name,
                    "auth_type": account.auth_type,
                    "auth_data": account.auth_data,
                    "last_used": account.last_used.isoformat() if account.last_used else None,
                    "usage_count": account.usage_count,
                    "status": account.status
                }
        
        try:
            with open(self.accounts_file, "w") as f:
                json.dump(accounts_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving accounts: {e}")
    
    def add_account(self, account: PlatformAccount) -> None:
        """Add a platform account.
        
        Args:
            account: Platform account to add
        """
        self.accounts[account.platform][account.account_id] = account
        self._save_accounts()
    
    def get_account(self, platform: PlatformType, account_id: str) -> Optional[PlatformAccount]:
        """Get a platform account.
        
        Args:
            platform: Platform to get the account for
            account_id: ID of the account to get
            
        Returns:
            Platform account, or None if not found
        """
        return self.accounts.get(platform, {}).get(account_id)
    
    def get_accounts(self, platform: Optional[PlatformType] = None) -> List[PlatformAccount]:
        """Get all platform accounts.
        
        Args:
            platform: Platform to get accounts for, or None for all platforms
            
        Returns:
            List of platform accounts
        """
        if platform:
            return list(self.accounts.get(platform, {}).values())
        
        all_accounts = []
        for platform_accounts in self.accounts.values():
            all_accounts.extend(platform_accounts.values())
        
        return all_accounts
    
    def update_account(self, account: PlatformAccount) -> None:
        """Update a platform account.
        
        Args:
            account: Platform account to update
        """
        if account.platform not in self.accounts or account.account_id not in self.accounts[account.platform]:
            logger.warning(f"Account not found: {account.platform}/{account.account_id}")
            return
        
        self.accounts[account.platform][account.account_id] = account
        self._save_accounts()
    
    def remove_account(self, platform: PlatformType, account_id: str) -> None:
        """Remove a platform account.
        
        Args:
            platform: Platform to remove the account from
            account_id: ID of the account to remove
        """
        if platform not in self.accounts or account_id not in self.accounts[platform]:
            logger.warning(f"Account not found: {platform}/{account_id}")
            return
        
        del self.accounts[platform][account_id]
        self._save_accounts()
    
    def update_account_usage(self, platform: PlatformType, account_id: str) -> None:
        """Update the usage statistics for an account.
        
        Args:
            platform: Platform of the account
            account_id: ID of the account
        """
        if platform not in self.accounts or account_id not in self.accounts[platform]:
            logger.warning(f"Account not found: {platform}/{account_id}")
            return
        
        account = self.accounts[platform][account_id]
        account.last_used = datetime.now()
        account.usage_count += 1
        
        self._save_accounts()
    
    def get_least_used_account(self, platform: PlatformType) -> Optional[PlatformAccount]:
        """Get the least used account for a platform.
        
        Args:
            platform: Platform to get the account for
            
        Returns:
            Least used platform account, or None if no accounts are available
        """
        if platform not in self.accounts or not self.accounts[platform]:
            return None
        
        active_accounts = [account for account in self.accounts[platform].values() if account.status == "active"]
        
        if not active_accounts:
            return None
        
        return min(active_accounts, key=lambda account: (account.usage_count, account.last_used or datetime.min))
    
    def add_zhihu_account(self, username: str, password: str, account_id: Optional[str] = None) -> PlatformAccount:
        """Add a Zhihu account.
        
        Args:
            username: Zhihu username
            password: Zhihu password
            account_id: Optional account ID, defaults to username
            
        Returns:
            Created platform account
        """
        account_id = account_id or username
        
        account = PlatformAccount(
            account_id=account_id,
            platform=PlatformType.ZHIHU,
            username=username,
            display_name=None,
            auth_type="credentials",
            auth_data={
                "username": username,
                "password": password
            },
            last_used=None,
            usage_count=0,
            status="active"
        )
        
        self.add_account(account)
        return account
    
    def add_x_account(self, username: str, password: str, account_id: Optional[str] = None) -> PlatformAccount:
        """Add an X (Twitter) account.
        
        Args:
            username: X username
            password: X password
            account_id: Optional account ID, defaults to username
            
        Returns:
            Created platform account
        """
        account_id = account_id or username
        
        account = PlatformAccount(
            account_id=account_id,
            platform=PlatformType.X,
            username=username,
            display_name=None,
            auth_type="credentials",
            auth_data={
                "username": username,
                "password": password
            },
            last_used=None,
            usage_count=0,
            status="active"
        )
        
        self.add_account(account)
        return account
