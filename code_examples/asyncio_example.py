import asyncio
import random
from master_logger.master_logger import Logger
# This examples showcases two coroutines which set permissions to admin users and another one to normal users
# The function that sets the permission only required the user_id and permission, but not the account_id
# The Logger showcases how we can set a 'global' variable associated to the execution of the coroutines
# where we can set the account_id without passing the parameter unnecessarily just to log it
# The account id set to the logger context globally to the coroutine but
# do not overlap and there is no race condition between coroutines as it uses contextvars

# Example result, may vary from randomness from asyncio.sleep(random_wait_time).
#
# [2025-04-08 15:34:44][DEBUG][coroutine_admins:37][ADMIN:account 1] Beginning admin set permissions
# [2025-04-08 15:34:44][DEBUG][coroutine_admins:37][ADMIN:account 2] Beginning admin set permissions
# [2025-04-08 15:34:44][DEBUG][coroutine_admins:37][ADMIN:account 3] Beginning admin set permissions
# [2025-04-08 15:34:44][DEBUG][coroutine_users:43][USER:account 107] Beginning user set permissions
# [2025-04-08 15:34:44][DEBUG][coroutine_users:43][USER:account 201] Beginning user set permissions
# [2025-04-08 15:34:44][DEBUG][coroutine_users:43][USER:account 303] Beginning user set permissions
# [2025-04-08 15:34:44][DEBUG][set_permissions:53][USER:account 201] Set permission user_permission to user 35
# [2025-04-08 15:34:44][DEBUG][coroutine_users:45][USER:account 201] Ending user set permissions
# [2025-04-08 15:34:44][DEBUG][set_permissions:53][ADMIN:account 2] Set permission admin_permission to user 3
# [2025-04-08 15:34:44][DEBUG][coroutine_admins:39][ADMIN:account 2] Ending admins set permissions
# [2025-04-08 15:34:45][DEBUG][set_permissions:53][USER:account 303] Set permission user_permission to user 57
# [2025-04-08 15:34:45][DEBUG][coroutine_users:45][USER:account 303] Ending user set permissions
# [2025-04-08 15:34:45][DEBUG][set_permissions:53][USER:account 107] Set permission user_permission to user 77
# [2025-04-08 15:34:45][DEBUG][coroutine_users:45][USER:account 107] Ending user set permissions
# [2025-04-08 15:34:46][DEBUG][set_permissions:53][ADMIN:account 3] Set permission admin_permission to user 5
# [2025-04-08 15:34:46][DEBUG][coroutine_admins:39][ADMIN:account 3] Ending admins set permissions
# [2025-04-08 15:34:46][DEBUG][set_permissions:53][ADMIN:account 1] Set permission admin_permission to user 7
# [2025-04-08 15:34:46][DEBUG][coroutine_admins:39][ADMIN:account 1] Ending admins set permissions



logger = Logger(log_line_number=False)


async def coroutine_admins(account_id: int, user_id: int, permission: str):
    logger.set_context_key(f"ADMIN:account {account_id}")
    logger.debug(f"Beginning admin set permissions")
    await set_permissions(user_id, permission)
    logger.debug(f"Ending admins set permissions")

async def coroutine_users(account_id: int, user_id: int, permission: str):
    logger.set_context_key(f"USER:account {account_id}")
    logger.debug(f"Beginning user set permissions")
    await set_permissions(user_id, permission)
    logger.debug(f"Ending user set permissions")

async def set_permissions(user_id: int, permission_name: str):
    random_wait_time = random.uniform(0, 3)
    await asyncio.sleep(random_wait_time)

    # We don't have explicitly passed the user's account id byt it would be useful to know in the logs
    # from which account the user is associated
    logger.debug(f"Set permission {permission_name} to user {user_id}")

async def main():
    tasks = []

    for admin_account_id, admin_user_id in [(1, 7), (2, 3), (3, 5)]:
        tasks.append(coroutine_admins(account_id=admin_account_id, user_id=admin_user_id, permission="admin_permission"))
    for user_account_id, user_id in [(107, 77), (201, 35), (303, 57)]:
        tasks.append(coroutine_users(account_id=user_account_id, user_id=user_id, permission="user_permission"))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())