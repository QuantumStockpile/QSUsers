from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" ADD "role_id" INT NOT NULL;
        ALTER TABLE "users" ADD CONSTRAINT "fk_users_roles_2657b48c" FOREIGN KEY ("role_id") REFERENCES "roles" ("id") ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" DROP CONSTRAINT "fk_users_roles_2657b48c";
        ALTER TABLE "users" DROP COLUMN "role_id";"""
