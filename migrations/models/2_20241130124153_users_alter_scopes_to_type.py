from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" ADD "type" VARCHAR(7) NOT NULL  DEFAULT 'default';
        ALTER TABLE "users" DROP COLUMN "scopes";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" ADD "scopes" TEXT NOT NULL;
        ALTER TABLE "users" DROP COLUMN "type";"""
