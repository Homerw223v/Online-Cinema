import asyncio
from getpass import getpass

from db.postgres import async_session
from models.access import ExtendedRole
from models.users import ExtendedUser
from services.repository import RolesService, UsersAdminService


async def create_superuser(username, email, password, first_name, last_name):
    async with async_session() as session:
        role_service = RolesService(session)
        role = ExtendedRole(name="admin", users=[], permissions=[])
        roles_list = await role_service.get_list(filters={"name": "admin"}, paginated_params=None)
        if roles_list:
            admin_role = roles_list[0]
        else:
            admin_role = await role_service.create(role)
        superuser = ExtendedUser(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            roles=[admin_role.id],
            permissions=[],
        )
        user_service = UsersAdminService(session)
        await user_service.create(superuser)


if __name__ == "__main__":
    username = input("Input username: ")
    email = input("Input email: ")
    password = getpass("Password: ")
    first_name = input("First name: ")
    last_name = input("Last name: ")
    asyncio.run(create_superuser(username, email, password, first_name, last_name))
